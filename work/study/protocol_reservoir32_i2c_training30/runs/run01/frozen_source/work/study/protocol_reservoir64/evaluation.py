"""Untouched final cases, independent output checks, controls and retained traces."""
import csv
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import (StreamReceiver, load_weights, NAMES, INVALID,
                                        FALL, BIT0, ARCHITECTURE_HASH)
from .data import PROFILES, RESERVED
from .training import SEEDS
from .uart_emitter import generate as uart_generate
from .simulation import run_uart, run_i2c
from .checkers import uart_decode, i2c_decode, bus_events
from .scoring import score_events, byte_errors, distribution
from .usb_emitter import training_gate
from .profiles import load_config


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def final_cases():
    rng = np.random.default_rng(90000)
    return [dict(name='phrase', payload=RESERVED, valid=True),
            dict(name='every_byte', payload=bytes(range(256)), valid=True),
            dict(name='random_binary', payload=rng.integers(0, 256, 2048, dtype=np.uint8).tobytes(), valid=True),
            dict(name='long_message', payload=rng.integers(0, 256, 1024, dtype=np.uint8).tobytes(), valid=True),
            dict(name='repeated_patterns', payload=b'\x00' * 128 + b'\xff' * 128 + b'\x55\xaa' * 128, valid=True),
            dict(name='fast_clock', payload=rng.integers(0, 256, 128, dtype=np.uint8).tobytes(), ratio=.97, low=8, high=8, valid=True),
            dict(name='slow_clock', payload=rng.integers(0, 256, 128, dtype=np.uint8).tobytes(), ratio=1.03, low=12, high=12, valid=True),
            dict(name='jitter', payload=rng.integers(0, 256, 128, dtype=np.uint8).tobytes(), jitter=1, low=10, high=10, valid=True),
            dict(name='fast_with_jitter', payload=rng.integers(0, 256, 128, dtype=np.uint8).tobytes(), ratio=.97, jitter=1, low=8, high=12, valid=True),
            dict(name='slow_with_jitter', payload=rng.integers(0, 256, 128, dtype=np.uint8).tobytes(), ratio=1.03, jitter=1, low=12, high=8, valid=True),
            dict(name='malformed_recovery', payload=rng.integers(0, 256, 64, dtype=np.uint8).tobytes(), malformed=True, valid=False),
            dict(name='stop_then_read', payload=rng.integers(0, 256, 64, dtype=np.uint8).tobytes(), repeated=False, valid=True),
            dict(name='unrelated_address', payload=b'\x10\x00\xff\x40', address=0x35, valid=True),
            dict(name='idle_and_disturbance', payload=bytes(range(32)), disturbance=True, valid=False)]


def applicable(profile, case):
    return not (profile.startswith('uart') and case['name'] in ('stop_then_read', 'unrelated_address'))


def uart_case(case, index, parity):
    bad = (2, 4) if case.get('malformed') else ()
    data = uart_generate(case['payload'], 90001 + index, parity=parity,
                         ratio=case.get('ratio', 1.), jitter=case.get('jitter', 0), bad_at=bad)
    if case.get('malformed') and parity:
        # Flip the complete parity cell of one other frame; labels identify the
        # observed bit, while the controller alone must discover wrong parity.
        frame = data['frames'][6]
        start = frame['start'] + 9 * 16
        data['lines'][start:start + 16, 0] ^= 1
        center = start + 8
        data['labels'][center] = BIT0 + int(data['lines'][center, 0])
        frame['valid'] = False
    expected = [frame['value'] for frame in data['frames'] if frame['valid']]
    if case.get('disturbance'):
        # Observable break and rapid transitions, immediately followed by data.
        levels = np.array([1] * 256 + [0] * 192 + [1, 0] * 64 + [1] * 16, dtype=np.uint8)
        prefix = np.column_stack((levels, np.ones(len(levels), dtype=np.uint8)))
        labels = np.zeros(len(prefix), dtype=np.int64)
        labels[400] = INVALID
        data['lines'] = np.concatenate((prefix, data['lines']))
        data['labels'] = np.concatenate((labels, data['labels']))
        for frame in data['frames']:
            frame['start'] += len(prefix)
            frame['end'] += len(prefix)
    data['expected'] = expected
    return data


def save_trace(directory, profile, mode, seed, case, result, metrics):
    destination = directory / f'{profile}_{mode}_{seed}_{case["name"]}'
    destination.mkdir(parents=True)
    events = np.array([(e.kind, e.observation_tick, e.decision_tick) for e in result['events']], dtype=np.int64).reshape(-1, 3)
    arrays = dict(lines=result['lines'], events=events, enables=result['enables'])
    if 'output' in result:
        arrays['output'] = result['output']
    if 'peer_drives' in result:
        arrays['peer_drives'] = result['peer_drives']
    np.savez_compressed(destination / 'waveform.npz', **arrays)
    write_json(destination / 'path.json', dict(expected_ascii=case['payload'].decode('ascii', 'backslashreplace'),
        expected_hex=case['payload'].hex(), recovered_by_controller=result['controller'].received,
        independently_decoded_output=metrics['output_bytes'], result=metrics,
        command_log=result['tx'].applied, controller_errors=result['controller'].errors))
    event_map = {e.decision_tick: NAMES[e.kind] for e in result['events']}
    recovered_map = dict(zip(result['controller'].received_ticks, result['controller'].received))
    with (destination / 'waveform.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['tick', 'observed_0', 'observed_1', 'target_oe0', 'target_oe1',
                         'uart_out', 'receiver_event', 'recovered_byte'])
        for t, pair in enumerate(result['lines']):
            writer.writerow([t, *map(int, pair), *map(int, result['enables'][t]),
                             int(result['output'][t]) if 'output' in result else '',
                             event_map.get(t, ''), recovered_map.get(t, '')])


def score_uart(case, index, receiver, parity, config=None):
    data = uart_case(case, index, parity)
    result = run_uart(data['lines'], receiver, parity, config=config)
    checked = uart_decode(result['output'], parity)
    expected_events = [(t, int(k)) for t, k in enumerate(data['labels']) if k]
    symbols, matched = score_events(expected_events, result['events'], allow_early=True)
    expected, output = data['expected'], checked['bytes']
    good_frames = [f for f in data['frames'] if f['valid']]
    # End-of-stop completion, not first output edge, is the deadline endpoint.
    latencies = [out + 8 - frame['end'] for out, frame in zip(checked['completion_ticks'], good_frames)]
    exact = output == expected
    deadline_misses = sum(t > 1024 or t < 0 for t in latencies) + max(0, len(expected) - len(output))
    metrics = dict(bytes=byte_errors(expected, output), output_bytes=output,
        controller_bytes=byte_errors(expected, result['controller'].received),
        symbols=symbols, output_errors=checked['errors'],
        response_latency=distribution(latencies if exact else []),
        latency_note='paired by byte index only when the entire output sequence is exact',
        deadline_misses=deadline_misses if exact else len(expected),
        controller_errors=len(result['controller'].errors), buffer_overflows=result['controller'].overflow + result['tx'].overflow,
        recovery_success=(output[-16:] == list(case['payload'][-16:])) if not case['valid'] else None,
        malformed_false_bytes=sum(any(f['start'] <= t <= f['end'] + 2 and not f['valid']
                                     for f in data['frames']) for t in result['controller'].received_ticks)
            if case.get('malformed') else None,
        ticks=len(result['lines']), input_presented_bytes=len(case['payload']))
    metrics['passes'] = (exact and not symbols['totals']['errors'] and not checked['errors']
                         and not metrics['deadline_misses'] and not metrics['buffer_overflows'])
    return metrics, result


def score_i2c(case, receiver, config=None):
    result = run_i2c(case['payload'], receiver, low=case.get('low', 10), high=case.get('high', 10),
        address=case.get('address', 0x32), repeated=case.get('repeated', True),
        malformed=case.get('malformed', False), disturbance=case.get('disturbance', False),
        jitter=case['name'] == 'jitter', config=config)
    decoded = i2c_decode(result['lines'])
    read_transactions = [d for d in decoded if d['bytes'] and d['bytes'][0] == ((case.get('address', 0x32) << 1) | 1)]
    output = [b for d in read_transactions for b in d['bytes'][1:]]
    expected = [] if case.get('address', 0x32) != 0x32 else list(case['payload'])
    symbols, matched = score_events(bus_events(result['lines']), result['events'])
    fall_ticks = {e.decision_tick for e in result['events'] if e.kind == FALL}
    latencies = [due - matched[t] for t, due in result['controller'].response_requests if t in fall_ticks and t in matched]
    deadlines = sum(latency > 6 for latency in latencies)
    if expected:
        deadlines += sum(not ack for ack in result['peer'].acks)
        deadlines += max(0, len(expected) + 2 - len(result['peer'].acks))
    foreign_ack = bool(any(result['peer'].acks)) if not expected else False
    metrics = dict(bytes=byte_errors(expected, output), output_bytes=output,
        controller_bytes=byte_errors(expected, result['controller'].received), symbols=symbols,
        response_latency=distribution(latencies), deadline_misses=deadlines,
        controller_errors=len(result['controller'].errors), buffer_overflows=result['controller'].overflow + result['tx'].overflow,
        peer_read=result['peer'].read, independent_peer_agree=output == result['peer'].read,
        peer_acks=result['peer'].acks, peer_timeout=result['peer'].timeout or not result['peer'].done,
        foreign_address_ack=foreign_ack, stretch_waits=distribution(result['peer'].stretches),
        recovery_success=(output == expected) if not case['valid'] else None,
        ticks=len(result['lines']), input_presented_bytes=len(result['controller'].received),
        attempted_payload_bytes=len(case['payload']), independent_bus_transactions=decoded)
    metrics['passes'] = (output == expected and result['controller'].received == expected
        and not symbols['totals']['errors'] and not deadlines and not metrics['buffer_overflows']
        and not metrics['peer_timeout'] and not foreign_ack and metrics['independent_peer_agree']
        and (not expected or bool(result['peer'].stretches)))
    return metrics, result


def resource_cost(output):
    weights, variants = {}, []
    for profile in PROFILES:
        for seed in SEEDS:
            w, _ = load_weights(output / 'models' / profile / f'seed_{seed}' / 'selected.npz')
            effective = np.diag(1 - np.tile([1, .5, .25, .125], 16)) + np.diag(np.tile([1, .5, .25, .125], 16)) @ w['wh']
            variants.append(dict(profile=profile, seed=seed,
                recurrent_spectral_radius=float(max(abs(np.linalg.eigvals(w['wh'])))),
                unsaturated_linearization_radius=float(max(abs(np.linalg.eigvals(effective)))),
                max_abs_weight=max(float(abs(v).max()) for v in w.values())))
    return dict(architecture_hash=ARCHITECTURE_HASH,
        parameters=dict(input_weights=384, recurrent_weights=256, state_bias=64,
                        readout_weights=512, readout_bias=8, total_trained=1224,
                        fixed_leaks=64, recurrent_indices_bits=256 * 6),
        logical_storage_bytes=dict(float64_coefficients=1224 * 8, quantized_int16_coefficients=1224 * 2,
            float64_state_double_buffer=64 * 8 * 2, quantized_state_double_buffer=64 * 2 * 2,
            leak_q15=128, recurrent_indices_packed=192, tanh_lut_q14=4097 * 2,
            preprocessor_previous_levels=2, preprocessor_edge_ages=2,
            event_register_64bit_timestamps_and_class=17, decision_last_class=1, tick_counter=8,
            uart_byte_fifo=32, uart_assembly_bits_and_count=3, uart_queue_deadlines_64bit=32 * 8,
            uart_schedule_counter=8, i2c_byte_storage=4096, i2c_controller_fields_upper_bound=64,
            tx_pending_commands_512x25bytes=512 * 25, tx_output_latches=4),
        arithmetic_per_tick=dict(sparse_MAC=384 + 256 + 512, dense_numpy_MAC=384 + 4096 + 512,
            leak_blend_products=128, tanh_or_LUT=64, bias_additions=72,
            quant_accumulator_bits=64, worst_case_drive_abs_bound=88,
            worst_case_readout_abs_bound=520, top_two_readout_comparisons_upper_bound=16),
        implementation_notes=[
            'Float reference uses float64; quantized steps use int64 NumPy arrays for overflow-safe arithmetic.',
            'Logical int16 parameter/state storage and sparse MAC counts are a packing proposal, not the Python process footprint.',
            'Current NumPy execution stores dense 64x64 recurrence even though only 256 entries can be nonzero.',
            'Tanh ROM generated once off-line; LUT and fixed-point rounding are used in online quantized steps.',
            'Python logs, full traces, emitted-event lists and recovered-byte lists are diagnostic sinks, not runtime decision inputs.',
            'Master/stimulus, training BPTT buffers and independent checkers are external to emulator; not counted as device storage.',
            'No accelerator schedule, area, achievable frequency, power, electrical or silicon feasibility measured.',
            'Linearization radii do not prove echo-state behavior or long-term stability.'],
        trained_dynamics=variants)


def evaluate(output):
    output = Path(output)
    final = output / 'final'
    final.mkdir(exist_ok=False)
    cases = final_cases()
    write_json(final / 'cases.json', [{**c, 'payload': list(c['payload'])} for c in cases])
    all_results = []
    for profile in PROFILES:
        config = load_config(output, profile)
        for variant in [*(f'seed_{seed}' for seed in SEEDS), 'readout_only']:
            seed = int(variant.split('_')[-1]) if variant.startswith('seed_') else 11
            weights, metadata = load_weights(output / 'models' / profile / variant / 'selected.npz')
            for mode in ('float', 'quantized'):
                rows = []
                for index, case in enumerate(cases):
                    if not applicable(profile, case):
                        continue
                    receiver = StreamReceiver(weights, mode, margin=config['decision_margin'])
                    metrics, result = (score_i2c(case, receiver, config) if profile == 'i2c'
                                       else score_uart(case, index, receiver, config['parity'], config))
                    rows.append(dict(condition=case['name'], valid=case['valid'], **metrics))
                    if case['name'] == 'phrase' and variant.startswith('seed_'):
                        save_trace(final / 'traces', profile, mode, seed, case, result, metrics)
                    print(json.dumps(dict(profile=profile, variant=variant, mode=mode,
                        case=case['name'], exact=metrics['bytes']['exact'], received=metrics['bytes']['recovered'],
                        expected=metrics['bytes']['expected'], symbol_errors=metrics['symbols']['totals']['errors'])), flush=True)
                record = dict(profile=profile, variant=variant, seed=seed, mode=mode,
                              qualified=all(r['passes'] for r in rows if r['valid']), conditions=rows)
                all_results.append(record)
                write_json(final / f'{profile}_{variant}_{mode}.json', record)
    controls = []
    # Matched phrase, every-byte and long repeated-bit conditions for all controls.
    for profile in PROFILES:
        config = load_config(output, profile)
        weights, _ = load_weights(output / 'models' / profile / 'seed_11' / 'selected.npz')
        for mode in ('float', 'quantized'):
            for control in ('disabled', 'no_recurrence'):
                for index in (0, 1, 4):
                    case = cases[index]
                    receiver = StreamReceiver(weights, mode, margin=config['decision_margin'], control=control)
                    metrics, _ = (score_i2c(case, receiver, config) if profile == 'i2c'
                                  else score_uart(case, index, receiver, config['parity'], config))
                    controls.append(dict(profile=profile, mode=mode, control=control,
                                         condition=case['name'], **metrics))
    write_json(final / 'controls.json', controls)
    qualification = {profile: all(row['qualified'] for row in all_results
        if row['profile'] == profile and row['variant'].startswith('seed_')) for profile in PROFILES}
    usb = training_gate(all(qualification.values()))
    write_json(final / 'usb_status.json', usb)
    write_json(final / 'cost.json', resource_cost(output))
    summary = dict(qualification=qualification, usb=usb, models=[{
        k: row[k] for k in ('profile', 'variant', 'seed', 'mode', 'qualified')} for row in all_results])
    write_json(final / 'summary.json', summary)
    print(json.dumps(summary), flush=True)


def replay(output, profile, mode, seed):
    path = Path(output) / 'final' / 'traces' / f'{profile}_{mode}_{seed}_phrase'
    with np.load(path / 'waveform.npz', allow_pickle=False) as trace:
        lines, expected = trace['lines'], trace['events']
    weights, _ = load_weights(Path(output) / 'models' / profile / f'seed_{seed}' / 'selected.npz')
    receiver, actual = StreamReceiver(weights, mode), []
    for tick, pair in enumerate(lines):
        event = receiver.step(pair, tick)
        if event is not None:
            actual.append((event.kind, event.observation_tick, event.decision_tick))
    actual = np.array(actual, dtype=np.int64).reshape(-1, 3)
    if not np.array_equal(actual, expected):
        raise AssertionError('saved observation replay differs')
    print(json.dumps(dict(profile=profile, mode=mode, seed=seed, ticks=len(lines),
                          replay_events=len(actual), exact_replay=True, waveform=str(path / 'waveform.csv'))))
