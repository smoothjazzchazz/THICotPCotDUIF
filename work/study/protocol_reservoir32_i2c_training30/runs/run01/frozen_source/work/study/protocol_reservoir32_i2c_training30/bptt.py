"""Original BPTT equations with the experiment-local state dimension."""
import numpy as np
from .receiver import MASK, LEAKS, NODES

def loss_gradient(w, x, y, valid, h0, weights, backward=True):
    length, size = y.shape
    states = np.empty((length + 1, size, NODES))
    proposals = np.empty((length, size, NODES))
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
    grad['wo'] = dlogit.reshape(-1, 8).T @ states[1:].reshape(-1, NODES)
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

