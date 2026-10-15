"""Offline UART-assumption traffic; this module is never imported by TX."""
import numpy as np
from work.model.stream_reservoir import NONE, BIT0, BIT1, START, STOP, INVALID


def generate(payload, seed, parity=False, ratio=1., jitter=0, gaps=False, bad_at=(), prefix=12):
    rng = np.random.default_rng(seed)
    samples, labels, frames = [1] * prefix, [NONE] * prefix, []
    elapsed = float(prefix) + float(rng.random())
    for index, value in enumerate(payload):
        bits = [(value >> bit) & 1 for bit in range(8)]
        if parity:
            bits += [sum(bits) % 2]
        stop = 0 if index in bad_at else 1
        cells = [0] + bits + [stop]
        kinds = [START] + [BIT0 + b for b in bits] + [STOP if stop else INVALID]
        start = len(samples)
        for bit, kind in zip(cells, kinds):
            elapsed += 16 * ratio + (int(rng.integers(-jitter, jitter + 1)) if jitter else 0)
            length = max(3, round(elapsed) - len(samples))
            center = len(samples) + length // 2
            samples.extend([bit] * length)
            labels.extend([NONE] * length)
            labels[center] = kind
        frames.append(dict(start=start, end=len(samples) - 1, value=int(value), valid=bool(stop)))
        if gaps:
            length = int(rng.integers(0, 3)) * 16
            samples.extend([1] * length)
            labels.extend([NONE] * length)
            elapsed += length
    samples.extend([1] * 64)
    labels.extend([NONE] * 64)
    return dict(lines=np.column_stack((samples, np.ones(len(samples), dtype=np.uint8))).astype(np.uint8),
                labels=np.array(labels, dtype=np.int64), frames=frames,
                metadata=dict(seed=seed, parity=parity, ratio=ratio, jitter=jitter,
                              expected=list(payload), source_status='assumed profile, unverified'))
