"""Small interaction checks for the shared scaffold, not protocol validation."""

import unittest
from math import tanh

from work.model.conditioning import InputConditioner
from work.model.controller import MappingController
from work.model.decision import DecisionStage, SymbolEvent
from work.model.memory import ExplicitHistory, RecurrentReservoir, ReservoirConfig
from work.model.readout import ClassScores, PrototypeReadout, PulseLengthReadout
from work.model.system_simple_model import StagedReceiver, run_simulation
from work.model.temporal import CompletedRun, TemporalEncoder
from work.model.transmit_simple_model import Transmitter


def make_receiver(memory=None, conditioner=None):
    return StagedReceiver(
        InputConditioner() if conditioner is None else conditioner,
        TemporalEncoder(), ExplicitHistory(2) if memory is None else memory,
        PulseLengthReadout({2: 0, 4: 1}), DecisionStage())


class StageTests(unittest.TestCase):
    def test_filter_delay_and_reset(self):
        conditioner = InputConditioner(stable_ticks=2, delay_ticks=2)
        samples = [1, 0, 1, 1, 0, 0, 0, 0]
        first = [conditioner.step(level) for level in samples]
        self.assertEqual([sample.level for sample in first], [0, 0, 0, 0, 0, 1, 1, 0])
        self.assertEqual([sample.delayed_level for sample in first], [0, 0, 1, 0, 1, 1, 0, 0])
        conditioner.reset()
        self.assertEqual(first, [conditioner.step(level) for level in samples])
        passthrough = InputConditioner()
        self.assertEqual([passthrough.step(level).level for level in samples], samples)
        with self.assertRaises(ValueError):
            conditioner.step(2)

    def test_temporal_measurement_and_initial_high(self):
        encoder = TemporalEncoder()
        samples = [encoder.step(level, tick) for tick, level in enumerate([1, 1, 0, 0, 1])]
        self.assertEqual([sample.transition for sample in samples], [0, 0, -1, 0, 1])
        self.assertEqual([sample.elapsed_ticks for sample in samples], [0, 1, 0, 1, 0])
        self.assertEqual(samples[2].completed_run, CompletedRun(1, 0, 2))
        self.assertEqual(samples[4].completed_run, CompletedRun(0, 2, 2))
        with self.assertRaises(ValueError):
            encoder.step(0, 6)
        encoder.reset()
        self.assertEqual(encoder.step(1, 0), samples[0])

    def test_memory_order_and_parallel_recurrence(self):
        encoder = TemporalEncoder()
        history = ExplicitHistory(2)
        first = encoder.step(1, 0)
        second = encoder.step(0, 1)
        self.assertEqual(history.step(first), (0.0, 0.0, 0.0) + first.features)
        snapshot = history.step(second)
        self.assertEqual(snapshot, first.features + second.features)
        history.reset()
        self.assertEqual(snapshot, first.features + second.features)
        self.assertEqual(history.state, (0.0,) * 6)

        reservoir = RecurrentReservoir(ReservoirConfig(
            ((1, 0, 0), (0, 0, 0)), ((0, 0), (1, 0)), 1.0))
        self.assertEqual(reservoir.step(first), (tanh(1), 0.0))
        self.assertEqual(reservoir.step(first), (tanh(1), tanh(tanh(1))))
        reservoir.reset()
        self.assertEqual(reservoir.state, (0.0, 0.0))

    def test_readout_scores_and_dimension_mismatch(self):
        prototypes = {0: [0.0, 1.0], 1: [1.0, 0.0]}
        readout = PrototypeReadout(prototypes, trigger="every_tick")
        prototypes[0][0] = 99
        sample = TemporalEncoder().step(0, 0)
        scores = readout.step((0, 1), sample)
        self.assertEqual(scores.scores, ((0, 0.0), (1, -1.0)))
        with self.assertRaises(ValueError):
            readout.step((0,), sample)
        decision = DecisionStage(minimum_score=-0.2, minimum_margin=0.1)
        self.assertEqual(decision.classify(scores.scores).class_id, 0)
        self.assertIsNone(decision.classify(((0, -0.3), (1, -1))).class_id)
        self.assertEqual(decision.classify(((0, 0), (1, 0))).reason, "ambiguous")
        self.assertEqual(decision.classify(((0, 0), (1, -0.05))).reason, "ambiguous")

    def test_stabilization_unknown_and_absence(self):
        decision = DecisionStage(hold_ticks=2)
        first = decision.step(ClassScores(((0, 0.0),), 3), 3)
        self.assertEqual(first.candidate.class_id, 0)
        self.assertIsNone(first.event)
        self.assertEqual(decision.step(ClassScores(((0, 0.0),), 4), 4).event,
                         SymbolEvent(0, 3, 4))
        self.assertIsNone(decision.step(ClassScores(((0, 0.0),), 5), 5).event)
        self.assertIsNone(decision.step(ClassScores((), 6), 6).event)
        unknown = decision.step(ClassScores((), 7), 7)
        self.assertEqual(unknown.event, SymbolEvent(None, 6, 7))
        absent = decision.step(None, 8)
        self.assertIsNone(absent.candidate)
        self.assertIsNone(absent.event)
        self.assertIsNone(decision.step(ClassScores((), 9), 9).event)
        decision.reset()
        self.assertIsNone(decision.pending)

    def test_zero_request_timing_backlog_and_transmitter_reset(self):
        patterns = {0: [0, 1, 0, 1, 0]}
        transmitter = Transmitter(patterns=patterns)
        patterns[0][0] = 1
        controller = MappingController({0: 0, None: 0})
        levels = [1, 1, 0, 1, 1, 0] + [0] * 8
        trace = run_simulation(levels, make_receiver(), controller, transmitter)
        self.assertEqual(trace[2]["request"].symbol_id, 0)
        self.assertIsNone(trace[2]["output_level"])
        self.assertEqual([row["output_level"] for row in trace[3:13]], [0, 1, 0, 1, 0] * 2)
        # A request at tick 5 waits for the first five-sample response to finish.
        self.assertEqual(trace[5]["request"].requested_tick, 5)
        self.assertIsNone(controller.step(SymbolEvent(None, 0, 1), 1))
        transmitter.reset()
        self.assertEqual(transmitter.symbols, [])
        self.assertIsNone(transmitter.step())
        preloaded = Transmitter([0], patterns={0: [0]})
        self.assertEqual(preloaded.step(), 0)
        preloaded.reset()
        self.assertEqual(preloaded.step(), 0)

    def test_conditioning_latency_is_in_event_timestamps(self):
        receiver = make_receiver(conditioner=InputConditioner(stable_ticks=2, delay_ticks=2))
        trace = run_simulation([0, 1, 1, 0] + [0] * 7, receiver)
        self.assertEqual(trace[6]["event"], SymbolEvent(0, 4, 6))
        self.assertEqual([row["output_level"] for row in trace[7:9]], [1, 0])
        self.assertTrue(all(row["event"] is None for row in trace[:6]))

    def test_reset_replay_independence_and_causal_prefix(self):
        prefix = [0, 1, 1, 0, 1, 1, 1]
        for memory_type in (ExplicitHistory, RecurrentReservoir):
            with self.subTest(memory=memory_type.__name__):
                receiver = make_receiver(memory_type())
                untouched = make_receiver(memory_type())
                initial_state = untouched.memory.state
                first = run_simulation(iter(prefix), receiver)
                self.assertEqual(untouched.memory.state, initial_state)
                self.assertIsNone(untouched.observation)
                self.assertEqual(first, run_simulation(iter(prefix), receiver))
                # Two incompatible futures cannot change any earlier trace entry.
                for suffix in ([0] * 8, [1] * 8):
                    longer = run_simulation(iter(prefix + suffix), receiver)
                    self.assertEqual(first, longer[:len(prefix)])
                # The unfinished final high run is not completed by end-of-input.
                self.assertIsNone(first[-1]["event"])

    def test_continuous_readout_through_runner(self):
        receiver = StagedReceiver(InputConditioner(), TemporalEncoder(), ExplicitHistory(1),
                                  PrototypeReadout({0: (1, 0, 0)}, trigger="every_tick"),
                                  DecisionStage(minimum_score=-0.02, hold_ticks=2))
        trace = run_simulation([1, 1, 1], receiver, MappingController({0: 0}),
                               Transmitter(patterns={0: [0]}))
        self.assertEqual(trace[1]["event"], SymbolEvent(0, 0, 1))
        self.assertEqual(trace[2]["output_level"], 0)
        self.assertIsNone(trace[2]["event"])


if __name__ == "__main__":
    unittest.main()
