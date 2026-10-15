"""Post-freeze arithmetic and replay audit; never tunes or alters a model."""
import hashlib
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import StreamReceiver, load_weights, MASK, initial_weights
from work.model.transmit_simple_model import ScheduledLineTransmitter
from work.study.protocol_reservoir64.controllers import UARTController, I2CController

ROOT = Path(__file__).resolve().parents[1]


def integer_scalar_check():
    rx = StreamReceiver(initial_weights(71), 'quantized')
    q = {k: v.tolist() for k, v in rx.q.items()}
    leaks, lookup = rx.leaks.tolist(), rx.lut.tolist()
    state, previous, ages = [0] * 64, None, [0, 0]
    rng = np.random.default_rng(60009)
    for tick, pair in enumerate(rng.integers(0, 2, (384, 2))):
        line = list(map(int, pair))
        x = []
        for lane in range(2):
            edge = 0 if previous is None else line[lane] - previous[lane]
            ages[lane] = 0 if previous is None or edge else min(127, ages[lane] + 1)
            x.extend(((line[lane] * 2 - 1) * 16384, edge * 16384,
                      (ages[lane] * 16384 + 63) // 127))
        new = []
        for node in range(64):
            total = sum(q['wx'][node][j] * x[j] for j in range(6))
            total += sum(q['wh'][node][j] * state[j] for j in range(64))
            total += q['b'][node] * 16384
            index = max(-2048, min(2048, (total + 131072) // 262144)) + 2048
            raw = (32768 - leaks[node]) * state[node] + leaks[node] * lookup[index]
            new.append(max(-16384, min(16384, (raw + 16384) // 32768)))
        state, previous = new, line
        expected_logits = [sum(q['wo'][c][j] * state[j] for j in range(64)) + q['bo'][c] * 16384 for c in range(8)]
        rx.step(pair, tick)
        assert rx.state.tolist() == state
        assert rx.logits.tolist() == expected_logits
    return dict(ticks=384, exact_state_and_logits=True, reference='scalar Python integer arithmetic')


def replay_path(path):
    profile, mode, seed, _ = path.name.rsplit('_', 3) if path.name.startswith('uart') else path.name.split('_')
    # uart_n / uart_e include one extra underscore; rsplit preserves that prefix.
    weights, _ = load_weights(ROOT / 'models' / profile / f'seed_{seed}' / 'selected.npz')
    with np.load(path / 'waveform.npz', allow_pickle=False) as saved:
        saved = {k: saved[k] for k in saved.files}
    receiver, transmitter = StreamReceiver(weights, mode), ScheduledLineTransmitter()
    controller = I2CController(transmitter) if profile == 'i2c' else UARTController(transmitter, parity=profile == 'uart_e')
    actual_events = []
    for tick, recorded_lines in enumerate(saved['lines']):
        levels, enables = transmitter.step(tick)
        assert list(enables) == saved['enables'][tick].tolist()
        if profile == 'i2c':
            # Replay the external master's drives; recompute target drive and
            # resolved lines, rather than feeding stored labels or bytes.
            lines = tuple(int(not (saved['peer_drives'][tick, i] or enables[i])) for i in range(2))
            assert list(lines) == recorded_lines.tolist()
        else:
            lines = recorded_lines
            assert (levels[0] if enables[0] else 1) == saved['output'][tick]
        event = receiver.step(lines, tick)
        controller.step(event, tick)
        if event:
            actual_events.append((event.kind, event.observation_tick, event.decision_tick))
    assert np.array_equal(np.array(actual_events, dtype=np.int64).reshape(-1, 3), saved['events'])
    expected_path = json.loads((path / 'path.json').read_text())
    assert controller.received == expected_path['recovered_by_controller']
    return dict(trace=path.name, ticks=len(saved['lines']), exact_entire_path=True)


def weight_audit():
    result = []
    for fit_path in sorted((ROOT / 'models').rglob('fit.json')):
        fit = json.loads(fit_path.read_text())
        weights, _ = load_weights(fit_path.parent / 'selected.npz')
        assert np.all(weights['wh'] * (1 - MASK) == 0)
        changes = fit['parameter_l2_changes']
        if fit['readout_only']:
            assert all(changes[k] == 0 for k in ('wx', 'wh', 'b'))
        else:
            assert all(changes[k] > 0 for k in ('wx', 'wh', 'wo'))
        result.append(dict(model=str(fit_path.parent.relative_to(ROOT)), steps=fit['steps'],
                           changes=changes, fixed_topology=True))
    return result


if __name__ == '__main__':
    result = dict(arithmetic=integer_scalar_check(), weights=weight_audit(),
        replay=[replay_path(path) for path in sorted((ROOT / 'final' / 'traces').glob('*'))],
        audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (ROOT / 'audit' / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(arithmetic=result['arithmetic'], models=len(result['weights']),
                         replayed_traces=len(result['replay']))))
