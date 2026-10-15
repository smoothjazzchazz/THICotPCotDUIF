"""Supervision, exposure and long-window gradient audits before any main fit."""
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import MASK, LEAKS, NAMES, features, initial_weights
from work.study.protocol_reservoir64.training import batch, class_weights, loss_gradient
from work.study.protocol_reservoir64.checkers import bus_events
from .data import PROFILES, RESERVED, load_split
from .training import CHUNK, MULTIPLIERS, write_json


def gradient_check():
    rng = np.random.default_rng(778)
    x, y = rng.normal(0, .4, (512, 2, 6)), rng.integers(0, 8, (512, 2))
    valid, h = np.ones((512, 2)), rng.normal(0, .1, (2, 64))
    w, weights = initial_weights(11), np.array([1., 12., 12., 48., 48., 5., 48., 12.])
    loss, state, grads = loss_gradient(w, x, y, valid, h, weights)
    taps = [tuple(map(int,p)) for p in np.argwhere(MASK)[[1, 100, 250]]]
    entries = [('wx', (3, 1)), ('wh', taps[0]), ('wh', taps[1]), ('wh', taps[2]),
               ('wo', (4, 7)), ('b', (7,)), ('bo', (3,))]
    rows = []
    for key, index in entries:
        before, eps = w[key][index], 1e-5
        w[key][index] = before + eps
        plus = loss_gradient(w, x, y, valid, h, weights, False)[0]
        w[key][index] = before - eps
        minus = loss_gradient(w, x, y, valid, h, weights, False)[0]
        w[key][index] = before
        numerical = (plus - minus) / (2 * eps)
        error = abs(numerical - grads[key][index])
        assert error < 1e-7
        rows.append(dict(parameter=key, index=index, analytic=float(grads[key][index]),
                         finite_difference=numerical, absolute_error=float(error)))
    assert np.count_nonzero(grads['wh'] * (1 - MASK)) == 0
    # Forward continuity must be independent of where gradients are cut.
    state1 = h.copy()
    for a in range(0, 512, 128):
        _, state1, _ = loss_gradient(w, x[a:a+128], y[a:a+128], valid[a:a+128], state1, weights, False)
    np.testing.assert_allclose(state1, state, rtol=0, atol=1e-14)
    return dict(finite_difference=rows, chunked_state_max_error=float(abs(state1-state).max()),
                group_gradient_norms={k:float(np.linalg.norm(v)) for k,v in grads.items()})


def credit_trace(w, lines):
    x = features(lines[:512])
    state, proposals = [np.zeros(64)], []
    for sample in x:
        z = np.tanh(w['wx'] @ sample + w['wh'] @ state[-1] + w['b'])
        proposals.append(z)
        state.append((1-LEAKS)*state[-1] + LEAKS*z)
    # Sensitivity of the final STOP logit to earlier state, no loss-weight mixing.
    dh = w['wo'][4].copy()
    rows = []
    for t in range(len(x)-1, -1, -1):
        lag = len(x)-1-t
        if lag in (0, 16, 64, 128, 160, 176, 256, 511):
            rows.append(dict(lag=lag, norm=float(np.linalg.norm(dh))))
        dh = dh*(1-LEAKS) + (dh*LEAKS*(1-proposals[t]**2)) @ w['wh']
    return rows


def preflight(output):
    from .run import ROOT, ORIGINAL, source_paths, sha, check_preservation
    output = Path(output)
    directory = output / 'audit'; directory.mkdir(exist_ok=True)
    check_preservation(output)
    profiles, ids = {}, set()
    for profile in PROFILES:
        splits = {}
        for split in ('train','dev'):
            streams = load_split(output, profile, split)
            counts = np.zeros(8, dtype=np.int64)
            clean_failures, transactions, complete128, complete512, frames = [], 0, 0, 0, 0
            for stream_index, stream in enumerate(streams):
                labels = stream['labels']; counts += np.bincount(labels, minlength=8)
                payloads = b''
                if profile == 'i2c':
                    expected = [(int(t), int(labels[t])) for t in np.flatnonzero(labels)]
                    assert bus_events(stream['lines']) == expected
                for tx in stream['metadata']['transactions']:
                    assert tx['seed'] not in ids
                    ids.add(tx['seed']); transactions += 1
                    payloads += bytes(tx['expected'])
                    if tx['independent_check']['clean'] and not tx['independent_check']['exact']:
                        clean_failures.append(tx['seed'])
                    if profile.startswith('uart'):
                        clock_rng = np.random.default_rng(tx['seed'])
                        elapsed = 12. + float(clock_rng.random())
                        cursor = 12
                        sample_index = tx['seed'] - stream['metadata']['seed'] + stream_index
                        parity = profile == 'uart_e'
                        for frame_index, frame in enumerate(tx['frames']):
                            assert cursor == frame['start']
                            reconstructed = []
                            for cell in range(11 if profile == 'uart_e' else 10):
                                elapsed += 16 * tx['ratio'] + (int(clock_rng.integers(-1,2)) if tx['jitter'] else 0)
                                end = round(elapsed)
                                reconstructed.append(cursor + (end-cursor)//2 + tx['offset'])
                                cursor = end
                            assert cursor-1 == frame['end']
                            if sample_index % 3 == 1:
                                gap = int(clock_rng.integers(0,3))*16
                                cursor += gap; elapsed += gap

                            a, b = frame['start']+tx['offset'], frame['end']+tx['offset']
                            positions = np.flatnonzero(labels[a:b+1]) + a
                            assert positions.tolist() == reconstructed
                            assert len(positions) == (11 if profile == 'uart_e' else 10)
                            assert labels[positions[0]] == 3
                            bits = [(frame['value'] >> k) & 1 for k in range(8)]
                            assert [int(labels[t]-1) for t in positions[1:9]] == bits
                            if profile == 'uart_e':
                                parity = sum(bits) % 2
                                if tx['parity_bad'] and frame_index == 0: parity ^= 1
                                assert labels[positions[9]] - 1 == parity
                            complete128 += a//128 == b//128
                            complete512 += a//512 == b//512
                            frames += 1
                assert RESERVED not in payloads
            # Independent decoder can be imperfect on jitter; retain all such
            # evidence, and require the exact emitter-cell label audit above.
            splits[split] = dict(class_counts=dict(zip(NAMES, map(int,counts))),
                transactions=transactions, independent_clean_decoder_failures=clean_failures,
                frames=frames, complete_frames_inside_128=complete128,
                complete_frames_inside_512=complete512,
                i2c_boundary_labels_exact=profile == 'i2c',
                uart_cell_centers_independently_reconstructed=profile.startswith('uart'))
        train = load_split(output, profile, 'train')
        x,y,valid = batch(train)
        base = class_weights(y,valid)
        counts = np.bincount(y[valid>0], minlength=8)
        original_data = load_split(ORIGINAL,profile,'train')
        old_counts = np.bincount(np.concatenate([s['labels'] for s in original_data]), minlength=8)
        profiles[profile] = dict(splits=splits, original_class_counts=dict(zip(NAMES,map(int,old_counts))),
            original_loss_weights=base.tolist(), main_loss_weights=(base*MULTIPLIERS).tolist(),
            original_loss_class_mass=(base*counts/(base*counts).sum()).tolist(),
            main_loss_class_mass=(base*MULTIPLIERS*counts/(base*MULTIPLIERS*counts).sum()).tolist(),
            initial_stop_credit_trace=credit_trace(initial_weights(11),train[0]['lines']),
            unsupported_label_classes=[NAMES[k] for k,n in enumerate(counts) if n==0])
        assert counts[3]>0 and counts[4]>0
    result = dict(passed=True, profiles=profiles, gradient_audit=gradient_check(),
        distinct_transaction_seeds=len(ids), split_seed_overlap=0,
        sources={str(p.relative_to(ROOT)):sha(p) for p in source_paths()},
        supervision_notes=[
            'UART pulses checked against frame payload, parity and actual line level; low stop cells label INVALID.',
            'I2C labels match independent observed edge contract, including all repeated START/STOP and malformed edges.',
            'I2C malformed packets contain valid physical edges; no synthetic INVALID event is invented for them.',
            'BOUNDARY is unused by both declared profiles; I2C INVALID arises from uncertain decisions, not a teacher boundary class.',
            'A 512-tick window removes the 128-tick hard cutoff for most whole UART frames; it does not guarantee nonvanishing gradients.',
            'Full live development scoring, including startup and tails, is separate from teacher-forced waveform loss.'])
    write_json(directory / 'preflight.json',result)
    print(json.dumps(dict(preflight_passed=True, transaction_seeds=len(ids),
                         profiles={k:v['splits']['train']['class_counts'] for k,v in profiles.items()})),flush=True)
