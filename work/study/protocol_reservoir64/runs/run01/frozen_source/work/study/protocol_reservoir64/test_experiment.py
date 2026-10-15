import unittest
from collections import deque
import numpy as np
from work.model.stream_reservoir import (ARCHITECTURE_HASH, MASK, LEAKS, LineFeatures,
    StreamReceiver, StreamEvent, initial_weights, save_weights, load_weights,
    NONE, BIT0, START, STOP, FALL)
from work.model.transmit_simple_model import ScheduledLineTransmitter
from .checkers import uart_decode, i2c_decode, bus_events, usb_unstuff_nrzi
from .uart_emitter import generate as uart_generate
from .i2c_emitter import generate as i2c_generate
from .usb_emitter import nrzi_diagnostic, generate_packet, MissingUSBSource, training_gate
from .simulation import run_uart, run_i2c
from .training import loss_gradient
from .data import generate_split


class OracleEvents:
    """Test-only ground-truth injection checks controller wiring, never a model score."""
    def __init__(self, labels):
        self.labels = labels
    def step(self, lines, tick):
        kind = self.labels[tick] if tick < len(self.labels) else NONE
        return StreamEvent(int(kind), tick, tick) if kind else None


class EdgeReference:
    """Test-only conventional bus observer; independent of emitter/controller."""
    def __init__(self, delay=0):
        self.previous, self.pending, self.delay = (1, 1), deque(), delay
    def step(self, lines, tick):
        before = self.previous
        self.previous = lines
        kind = None
        if before[0] == lines[0] == 1 and before[1] != lines[1]:
            kind = START if lines[1] == 0 else STOP
        elif before[0] != lines[0]:
            kind = BIT0 + lines[1] if lines[0] else FALL
        if kind is not None:
            self.pending.append(StreamEvent(kind, tick, tick + self.delay))
        return self.pending.popleft() if self.pending and self.pending[0].decision_tick <= tick else None


class ExperimentTests(unittest.TestCase):
    def test_fixed_sparse_topology_and_causality(self):
        self.assertEqual(MASK.shape, (64, 64))
        np.testing.assert_array_equal(MASK.sum(1), np.full(64, 4))
        w = initial_weights(11)
        prefix = [(1, 1)] * 8 + [(0, 1)] * 11 + [(1, 0)] * 7
        for mode in ('float', 'quantized'):
            snapshots = []
            for suffix in ([(0, 0)] * 20, [(1, 1)] * 20):
                rx, record = StreamReceiver(w, mode), []
                for tick, pair in enumerate(prefix + suffix):
                    event = rx.step(pair, tick)
                    if tick < len(prefix):
                        record.append((event, rx.state.copy()))
                snapshots.append(record)
            for a, b in zip(*snapshots):
                self.assertEqual(a[0], b[0])
                np.testing.assert_array_equal(a[1], b[1])

    def test_gradient_actual_internal_weights(self):
        rng = np.random.default_rng(21)
        w = initial_weights(4)
        x, y = rng.normal(size=(7, 2, 6)), rng.integers(0, 8, (7, 2))
        valid, h = np.ones((7, 2)), rng.normal(0, .1, (2, 64))
        _, _, grad = loss_gradient(w, x, y, valid, h, np.ones(8))
        recurrent_tap = tuple(np.argwhere(MASK)[13])
        for key, index in [('wx', (3, 1)), ('wh', recurrent_tap), ('wo', (1, 3)), ('b', (7,))]:
            old, epsilon = w[key][index], 1e-5
            w[key][index] = old + epsilon
            plus = loss_gradient(w, x, y, valid, h, np.ones(8), False)[0]
            w[key][index] = old - epsilon
            minus = loss_gradient(w, x, y, valid, h, np.ones(8), False)[0]
            w[key][index] = old
            self.assertAlmostEqual(grad[key][index], (plus - minus) / (2 * epsilon), places=7)

    def test_quantized_determinism_and_bounds(self):
        a, b = (StreamReceiver(initial_weights(29), 'quantized') for _ in range(2))
        rng = np.random.default_rng(17)
        for t, pair in enumerate(rng.integers(0, 2, (400, 2))):
            self.assertEqual(a.step(pair, t), b.step(pair, t))
            self.assertTrue(np.max(np.abs(a.state)) <= 16384)
            self.assertTrue(np.issubdtype(a.logits.dtype, np.integer))
            np.testing.assert_array_equal(a.state, b.state)

    def test_scheduler_causality_and_overflow(self):
        tx = ScheduledLineTransmitter(capacity=1)
        with self.assertRaises(ValueError):
            tx.schedule(0, 0, True, 4, 4)
        self.assertTrue(tx.schedule(0, 0, True, 5, 4))
        self.assertFalse(tx.schedule(1, 0, True, 6, 4))
        self.assertFalse(tx.step(4)[1][0])
        self.assertTrue(tx.step(5)[1][0])
        self.assertEqual(tx.overflow, 1)

    def test_uart_generator_and_full_tx_all_bytes(self):
        for parity in (False, True):
            payload = bytes(range(256)) + bytes([0, 255, 85, 170]) * 8
            generated = uart_generate(payload, 501, parity=parity)
            self.assertEqual(uart_decode(generated['lines'][:, 0], parity)['bytes'], list(payload))
            result = run_uart(generated['lines'], OracleEvents(generated['labels']), parity)
            self.assertEqual(uart_decode(result['output'], parity)['bytes'], list(payload))
            self.assertFalse(result['controller'].errors)
            self.assertFalse(result['tx'].overflow)

    def test_i2c_interactive_store_read_stretch_and_nack(self):
        payload = bytes(range(32)) + bytes([0, 255, 85, 170]) * 3
        for timing in (8, 10, 12):
            result = run_i2c(payload, EdgeReference(delay=2), low=timing, high=timing)
            self.assertEqual(result['controller'].storage, list(payload))
            self.assertEqual(result['peer'].read, list(payload))
            decoded = i2c_decode(result['lines'])
            self.assertEqual(decoded[1]['bytes'], [0x65] + list(payload))
            self.assertFalse(decoded[1]['acks'][-1])
            self.assertTrue(result['peer'].stretches)
            self.assertFalse(result['peer'].timeout)
            self.assertFalse(result['controller'].errors)
        foreign = run_i2c(b'abc', EdgeReference(), address=0x35)
        self.assertFalse(any(foreign['peer'].acks))
        self.assertFalse(foreign['controller'].storage)
        recovery = run_i2c(b'recover', EdgeReference(), malformed=True, repeated=False)
        self.assertEqual(recovery['peer'].read, list(b'recover'))
        self.assertTrue(recovery['controller'].errors)

    def test_independent_i2c_generator(self):
        payload = bytes(range(256))
        stream = i2c_generate(payload, 71)
        decoded = i2c_decode(stream['lines'])
        self.assertEqual(decoded[0]['bytes'], [0x64] + list(payload))
        self.assertEqual(decoded[1]['bytes'], [0x65] + list(payload))
        self.assertEqual(bus_events(stream['lines']), [(t, int(k)) for t, k in enumerate(stream['labels']) if k])

    def test_usb_source_gate_and_line_diagnostic(self):
        bits = [1] * 24 + [0, 1] * 8
        self.assertEqual(usb_unstuff_nrzi(nrzi_diagnostic(bits)), bits)
        with self.assertRaises(MissingUSBSource):
            generate_packet(b'abc')
        self.assertEqual(training_gate(False)['fit_steps'], 0)
        with self.assertRaises(ValueError):
            usb_unstuff_nrzi(['J'] * 7)

    def test_split_nonoverlap_and_no_reserved_phrase(self):
        ids = set()
        for profile in ('uart_n', 'uart_e', 'i2c'):
            for split in ('train', 'dev'):
                streams, _ = generate_split(profile, split)
                for stream in streams:
                    seed = stream['metadata']['seed']
                    self.assertNotIn(seed, ids)
                    ids.add(seed)
                    self.assertGreaterEqual(len(stream['lines']), 4096)
                    self.assertNotIn(b'House Improvement Committee', bytes(stream['metadata']['expected']))


if __name__ == '__main__':
    unittest.main()
