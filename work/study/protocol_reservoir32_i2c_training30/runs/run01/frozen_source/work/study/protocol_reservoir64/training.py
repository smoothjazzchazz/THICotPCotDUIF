"""Off-chip NumPy BPTT/Adam, including gradients of input and recurrent weights."""
import json
import time
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import MASK, LEAKS, initial_weights, features, save_weights

SEEDS = (11, 29, 47)
EPOCHS, CHUNK, LR = 12, 128, .003


def batch(streams):
    maximum = max(len(s['labels']) for s in streams)
    x = np.zeros((maximum, len(streams), 6))
    y = np.zeros((maximum, len(streams)), dtype=np.int64)
    valid = np.zeros(y.shape)
    for i, stream in enumerate(streams):
        n = len(stream['labels'])
        x[:n, i] = features(stream['lines'])
        y[:n, i] = stream['labels']
        valid[:n, i] = 1
    return x, y, valid


def class_weights(y, valid):
    counts = np.bincount(y[valid > 0], minlength=8)
    return np.minimum(12, np.sqrt(max(counts) / np.maximum(counts, 1)))


def loss_gradient(w, x, y, valid, h0, weights, backward=True):
    length, size = y.shape
    states = np.empty((length + 1, size, 64))
    proposals = np.empty((length, size, 64))
    states[0] = h0
    for t in range(length):
        proposals[t] = np.tanh(x[t] @ w['wx'].T + states[t] @ w['wh'].T + w['b'])
        states[t + 1] = states[t] * (1 - LEAKS) + proposals[t] * LEAKS
    logits = states[1:] @ w['wo'].T + w['bo']
    logits -= logits.max(axis=2, keepdims=True)
    prob = np.exp(logits)
    prob /= prob.sum(axis=2, keepdims=True)
    rows, columns = np.indices(y.shape)
    scale = valid * weights[y]
    norm = max(float(valid.sum()), 1.)
    loss = -float((np.log(np.maximum(prob[rows, columns, y], 1e-30)) * scale).sum()) / norm
    if not backward:
        return loss, states[-1].copy(), None
    prob[rows, columns, y] -= 1
    dlogit = prob * (scale / norm)[..., None]
    grad = {k: np.zeros_like(value) for k, value in w.items()}
    grad['wo'] = dlogit.reshape(-1, 8).T @ states[1:].reshape(-1, 64)
    grad['bo'] = dlogit.sum(axis=(0, 1))
    dh = np.zeros_like(h0)
    projected = dlogit @ w['wo']
    for t in range(length - 1, -1, -1):
        dh += projected[t]
        dz = dh * LEAKS * (1 - proposals[t] ** 2)
        grad['wx'] += dz.T @ x[t]
        grad['wh'] += dz.T @ states[t]
        grad['b'] += dz.sum(axis=0)
        dh = dh * (1 - LEAKS) + dz @ w['wh']
    grad['wh'] *= MASK
    return loss, states[-1].copy(), grad


def evaluate_loss(w, data, weights):
    x, y, valid = data
    state, total, count = np.zeros((x.shape[1], 64)), 0., 0
    for start in range(0, len(x), CHUNK):
        stop = start + CHUNK
        loss, state, _ = loss_gradient(w, x[start:stop], y[start:stop], valid[start:stop],
                                       state, weights, backward=False)
        n = valid[start:stop].sum()
        total, count = total + loss * n, count + n
    return total / count


def fit(train, dev, directory, seed, readout_only=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    train, dev = batch(train), batch(dev)
    x, y, valid = train
    weights = class_weights(y, valid)
    w = initial_weights(seed)
    initial = {k: v.copy() for k, v in w.items()}
    save_weights(directory / 'initial.npz', initial, seed=seed, readout_only=readout_only)
    m, v = ({k: np.zeros_like(a) for k, a in w.items()} for _ in range(2))
    step, history, best_loss, best_epoch = 0, [], float('inf'), None
    started = time.monotonic()
    for epoch in range(EPOCHS):
        state = np.zeros((x.shape[1], 64))
        losses = []
        for start in range(0, len(x), CHUNK):
            stop = start + CHUNK
            loss, state, grad = loss_gradient(w, x[start:stop], y[start:stop], valid[start:stop], state, weights)
            if readout_only:
                for key in ('wx', 'wh', 'b'):
                    grad[key][:] = 0
            norm = np.sqrt(sum(float((g * g).sum()) for g in grad.values()))
            step += 1
            for key in w:
                g = grad[key] / max(norm, 1)
                m[key] = .9 * m[key] + .1 * g
                v[key] = .999 * v[key] + .001 * g * g
                w[key] -= LR * (m[key] / (1 - .9 ** step)) / (np.sqrt(v[key] / (1 - .999 ** step)) + 1e-8)
                np.clip(w[key], -7.99, 7.99, out=w[key])
            w['wh'] *= MASK
            losses.append(loss)
        dev_loss = evaluate_loss(w, dev, weights)
        checkpoint = f'epoch_{epoch + 1:02d}.npz'
        save_weights(directory / checkpoint, w, seed=seed, epoch=epoch + 1, readout_only=readout_only)
        if dev_loss < best_loss:
            best_loss, best_epoch = dev_loss, epoch + 1
            save_weights(directory / 'selected.npz', w, seed=seed, epoch=epoch + 1, readout_only=readout_only)
        row = dict(epoch=epoch + 1, steps=step, train_loss=float(np.mean(losses)), dev_loss=dev_loss,
                   elapsed_seconds=time.monotonic() - started)
        history.append(row)
        print(json.dumps(dict(model=str(directory), **row)), flush=True)
    selected = dict(np.load(directory / 'selected.npz', allow_pickle=False))
    changes = {k: float(np.linalg.norm(selected[k] - initial[k])) for k in initial}
    result = dict(seed=seed, readout_only=readout_only, epochs=EPOCHS, steps=step,
                  best_epoch=best_epoch, class_weights=weights.tolist(), history=history,
                  parameter_l2_changes=changes, stream_count=x.shape[1],
                  truncated_bptt=CHUNK, training_ticks=int(valid.sum()))
    (directory / 'fit.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
