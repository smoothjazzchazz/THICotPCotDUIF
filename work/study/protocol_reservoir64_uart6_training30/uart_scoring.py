"""Untouched final cases, independent output checks, controls and retained traces."""
import csv
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import (StreamReceiver, load_weights, NAMES, INVALID,
                                        FALL, BIT0, ARCHITECTURE_HASH)
from .data import PROFILES, RESERVED
from work.study.protocol_reservoir64.uart_emitter import generate as uart_generate
from work.study.protocol_reservoir64.simulation import run_uart, run_i2c
from work.study.protocol_reservoir64.checkers import uart_decode, i2c_decode, bus_events
from work.study.protocol_reservoir64.scoring import score_events, byte_errors, distribution
from work.study.protocol_reservoir64.usb_emitter import training_gate
from work.study.protocol_reservoir64.profiles import load_config


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def uart_case(case, index, parity):
    bad = (2, 4) if case.get('malformed') else ()
    data = uart_generate(case['payload'], 90001 + index, parity=parity,
                         ratio=case.get('ratio', 1.), jitter=case.get('jitter', 0), bad_at=bad, gaps=case.get('gaps', False))
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
    metrics['boundary_timing'] = {NAMES[k]: distribution([e.decision_tick-matched[e.decision_tick] for e in result['events'] if e.kind==k and e.decision_tick in matched]) for k in (3,4)}
    metrics['cold_start_events'] = [dict(kind=e.kind,tick=e.decision_tick) for e in result['events'] if e.decision_tick < data['frames'][0]['start']]
    metrics['timing_requested'] = dict(ratio=case.get('ratio',1.), jitter=case.get('jitter',0), gaps=case.get('gaps',False))
    metrics['frame_lengths'] = sorted(set(f['end']-f['start']+1 for f in data['frames']))
    metrics['passes'] = (exact and not symbols['totals']['errors'] and not checked['errors']
                         and not metrics['deadline_misses'] and not metrics['buffer_overflows'])
    return metrics, result


