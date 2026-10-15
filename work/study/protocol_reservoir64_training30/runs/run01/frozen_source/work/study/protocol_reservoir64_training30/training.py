"""Original NumPy BPTT/Adam with longer credit assignment and complete checkpoints."""
import json
import time
import traceback
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import (MASK, LEAKS, NAMES, StreamReceiver, StreamEvent,
    initial_weights, save_weights, load_weights)
from work.study.protocol_reservoir64.training import batch, class_weights, loss_gradient
from work.study.protocol_reservoir64.scoring import score_events
from work.study.protocol_reservoir64.profiles import load_config
from .data import load_split, cases
from .metrics import add_precision, score_case, aggregate, selection_key

EPOCHS, CHUNK, LR = 30, 512, .003
SEEDS = (11, 29, 47)
CHECKPOINTS = (1, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30)
MULTIPLIERS = np.array([1., 2., 2., 4., 4., 1., 4., 1.])


def write_json(path, obj):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def adam_step(w, grad, m, v, step):
    norm = np.sqrt(sum(float((g * g).sum()) for g in grad.values()))
    if not np.isfinite(norm):
        raise FloatingPointError('nonfinite gradient')
    for key in w:
        g = grad[key] / max(norm, 1)
        m[key] = .9 * m[key] + .1 * g
        v[key] = .999 * v[key] + .001 * g * g
        w[key] -= LR * (m[key] / (1 - .9 ** step)) / (np.sqrt(v[key] / (1 - .999 ** step)) + 1e-8)
        np.clip(w[key], -7.99, 7.99, out=w[key])
    w['wh'] *= MASK
    if any(not np.all(np.isfinite(a)) for a in w.values()):
        raise FloatingPointError('nonfinite coefficient')
    return float(norm)


def dev_predictions(w, data, weights):
    x, y, valid = data
    state = np.zeros((x.shape[1], 64))
    kinds = np.zeros(y.shape, dtype=np.int64)
    total, count = 0., float(valid.sum())
    for start in range(0, len(x), CHUNK):
        stop = min(start + CHUNK, len(x))
        logits = []
        for t in range(start, stop):
            state = state * (1 - LEAKS) + LEAKS * np.tanh(x[t] @ w['wx'].T + state @ w['wh'].T + w['b'])
            logits.append(state @ w['wo'].T + w['bo'])
        raw = np.asarray(logits)
        order = np.argsort(raw, axis=-1)
        ranked = np.take_along_axis(raw, order, axis=-1)
        k = order[..., -1].copy()
        k[ranked[..., -1] - ranked[..., -2] < .15] = 6
        kinds[start:stop] = k
        raw -= raw.max(axis=-1, keepdims=True)
        prob = np.exp(raw); prob /= prob.sum(axis=-1, keepdims=True)
        target = y[start:stop]
        picked = np.take_along_axis(prob, target[..., None], axis=-1)[..., 0]
        total -= float((np.log(np.maximum(picked, 1e-30)) * weights[target] * valid[start:stop]).sum())
    return total / count, kinds


def dev_event_scores(w, streams, data, weights, profile):
    loss, kinds = dev_predictions(w, data, weights)
    rows = []
    for i, stream in enumerate(streams):
        k = kinds[:len(stream['labels']), i]
        changed = np.flatnonzero((k != 0) & (k != np.r_[0, k[:-1]]))
        events = [StreamEvent(int(k[t]), int(t), int(t)) for t in changed]
        expected = [(int(t), int(stream['labels'][t])) for t in np.flatnonzero(stream['labels'])]
        score, _ = score_events(expected, events, allow_early=profile.startswith('uart'))
        rows.append(dict(stream=i, symbols=add_precision(score, events), ticks=len(k)))
    return loss, rows


def live_dev(w, profile, config):
    rows = []
    for case in cases(profile, 'dev'):
        metrics, _ = score_case(profile, case, StreamReceiver(w), config)
        rows.append(dict(condition=case['name'], valid=case['valid'], **metrics))
    return rows


def save_optimizer(path, w, m, v, state, epoch, step):
    arrays = {**{'w_' + k:a for k,a in w.items()}, **{'m_' + k:a for k,a in m.items()},
              **{'v_' + k:a for k,a in v.items()}, 'ending_state':state}
    np.savez_compressed(path, **arrays, metadata=json.dumps(dict(epoch=epoch, step=step,
        next_epoch=epoch + 1, next_chunk=0, state_at_next_epoch='zeros, same independent stream starts as original',
        chunk=CHUNK, lr=LR, rng='none in training; fixed stream order; deterministic Adam')))


def restore_optimizer(path):
    with np.load(path, allow_pickle=False) as f:
        d = [{k:f[p + k].copy() for k in initial_weights(0)} for p in ('w_', 'm_', 'v_')]
        meta = json.loads(str(f['metadata']))
    return *d, meta


def fit_job(job):
    output, profile, seed, recipe = job
    output = Path(output)
    if (output / 'freeze.json').exists():
        raise ValueError('fitting forbidden after freeze')
    variant = f'seed_{seed}' if recipe == 'weighted' else 'original_loss_11'
    directory = output / 'models' / profile / variant
    if (directory / 'fit.json').exists():
        return str(directory)
    directory.mkdir(parents=True, exist_ok=True)
    streams, devstreams = load_split(output, profile, 'train'), load_split(output, profile, 'dev')
    x, y, valid = batch(streams)
    dev = batch(devstreams)
    weights = class_weights(y, valid) * (MULTIPLIERS if recipe == 'weighted' else 1)
    w = initial_weights(seed)
    initial = {k:v.copy() for k,v in w.items()}
    if not (directory / 'initial.npz').exists():
        save_weights(directory / 'initial.npz', w, seed=seed, recipe=recipe)
    m, v = ({k:np.zeros_like(a) for k,a in w.items()} for _ in range(2))
    history, step, first = [], 0, 1
    if (directory / 'history.json').exists():
        history = json.loads((directory / 'history.json').read_text())
        w, m, v, resume = restore_optimizer(directory / f"optimizer_{history[-1]['epoch']:02d}.npz")
        step, first = resume['step'], resume['next_epoch']
    config = load_config(output, profile)
    started = time.monotonic()
    previous_elapsed = history[-1]['elapsed_seconds'] if history else 0
    try:
        for epoch in range(first, EPOCHS + 1):
            state = np.zeros((12, 64))
            summed, count, norms, group_norms = 0., 0., [], {k:[] for k in w}
            for start in range(0, len(x), CHUNK):
                stop = start + CHUNK
                incoming = state.copy()
                loss, state, grad = loss_gradient(w, x[start:stop], y[start:stop], valid[start:stop], state, weights)
                if not np.isfinite(loss) or not np.all(np.isfinite(state)):
                    raise FloatingPointError('nonfinite loss/state')
                for k,g in grad.items():
                    group_norms[k].append(float(np.linalg.norm(g)))
                step += 1
                norms.append(adam_step(w, grad, m, v, step))
                n = float(valid[start:stop].sum())
                summed += loss * n; count += n
            dev_loss, event_rows = dev_event_scores(w, devstreams, dev, weights, profile)
            write_json(directory / f'dev_events_{epoch:02d}.json', event_rows)
            row = dict(epoch=epoch, steps=step, train_loss=summed / count, dev_loss=dev_loss,
                train_loss_note='valid-tick weighted online loss before each optimizer update',
                elapsed_seconds=previous_elapsed + time.monotonic() - started,
                gradient_norm_mean=float(np.mean(norms)), gradient_norm_max=max(norms),
                clipped_updates=sum(n > 1 for n in norms),
                gradient_group_norm_mean={k:float(np.mean(vv)) for k,vv in group_norms.items()})
            if epoch in CHECKPOINTS:
                rows = live_dev(w, profile, config)
                write_json(directory / f'dev_live_{epoch:02d}.json', rows)
                row['live'] = aggregate(rows)
                row['selection_key'] = list(selection_key(row['live'], dev_loss))
            save_weights(directory / f'epoch_{epoch:02d}.npz', w, seed=seed, epoch=epoch, recipe=recipe)
            save_optimizer(directory / f'optimizer_{epoch:02d}.npz', w, m, v, state, epoch, step)
            history.append(row)
            write_json(directory / 'history.json', history)
            print(json.dumps(dict(profile=profile, variant=variant, epoch=epoch, steps=step,
                                  train_loss=row['train_loss'], dev_loss=dev_loss,
                                  live=row.get('live', {}).get('byte_exact_exchanges'))), flush=True)
        eligible = [r for r in history if 'selection_key' in r]
        best = max(eligible, key=lambda r:tuple(r['selection_key']))
        selected, _ = load_weights(directory / f"epoch_{best['epoch']:02d}.npz")
        save_weights(directory / 'selected.npz', selected, seed=seed, epoch=best['epoch'], recipe=recipe)
        result = dict(seed=seed, recipe=recipe, epochs=EPOCHS, steps=step, best_epoch=best['epoch'],
            class_weights=weights.tolist(), history=history, batch_size=12, truncated_bptt=CHUNK,
            unique_nonpadding_ticks=int(valid.sum()), unique_transaction_ticks=sum(s['metadata']['transaction_ticks'] for s in streams),
            repeated_nonpadding_presentations=int(valid.sum()) * EPOCHS,
            repeated_transaction_presentations=sum(s['metadata']['transaction_ticks'] for s in streams) * EPOCHS,
            padding_presentations=int(valid.size - valid.sum()) * EPOCHS,
            parameter_l2_changes={k:float(np.linalg.norm(selected[k] - initial[k])) for k in initial})
        write_json(directory / 'fit.json', result)
    except Exception:
        save_optimizer(directory / 'failure_state.npz', w, m, v, incoming if 'incoming' in locals() else np.zeros((12,64)),
                       epoch if 'epoch' in locals() else 0, step)
        write_json(directory / 'failure.json', dict(traceback=traceback.format_exc(),
            epoch=epoch if 'epoch' in locals() else None, chunk=start if 'start' in locals() else None))
        raise
    return str(directory)
