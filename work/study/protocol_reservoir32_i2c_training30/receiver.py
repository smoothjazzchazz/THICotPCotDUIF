"""Two-line trainable sparse memory; protocol rules never enter this receiver.

NumPy is an optional dependency of the opt-in protocol experiment. Inference
accepts exactly one observation at a time, with no frame or payload arguments.
"""

from dataclasses import dataclass
import hashlib
import json

import numpy as np


NONE, BIT0, BIT1, START, STOP, FALL, INVALID, BOUNDARY = range(8)
NAMES = ("NONE", "BIT0", "BIT1", "START", "STOP", "FALL", "INVALID", "BOUNDARY")
NODES, INPUTS, CLASSES, AGE_CAP, TOPOLOGY_SEED = 32, 6, 8, 127, 640031
LEAKS = np.tile(np.array([1., .5, .25, .125]), NODES // 4)


def connection_mask():
    rng = np.random.default_rng(TOPOLOGY_SEED)
    mask = np.zeros((NODES, NODES))
    for row in range(NODES):
        taps = {row, (row - 1) % NODES}
        while len(taps) < 4:
            taps.add(int(rng.integers(NODES)))
        mask[row, list(taps)] = 1
    return mask


MASK = connection_mask()
ARCHITECTURE = dict(nodes=NODES, inputs=INPUTS, classes=list(NAMES),
                    topology_seed=TOPOLOGY_SEED, mask=MASK.astype(int).tolist(),
                    leaks=LEAKS.tolist(), age_cap=AGE_CAP,
                    update="h'=(1-a)*h+a*tanh(Wx*x+Wh*h+b)",
                    quantization="int16 W Q12; state/input Q14; leak Q15; int64 MAC; LUT Q14")
ARCHITECTURE_HASH = hashlib.sha256(json.dumps(ARCHITECTURE, sort_keys=True).encode()).hexdigest()


def initial_weights(seed):
    rng = np.random.default_rng(seed)
    return dict(wx=rng.normal(0, .35, (NODES, INPUTS)),
                wh=rng.normal(0, .35, (NODES, NODES)) * MASK,
                b=np.zeros(NODES), wo=rng.normal(0, .1, (CLASSES, NODES)), bo=np.zeros(8))


class LineFeatures:
    """Only generic edge measurements; six stored small integers outside nodes."""

    def __init__(self):
        self.previous = None
        self.ages = np.zeros(2, dtype=np.int64)

    def step(self, lines, integer=False):
        lines = np.asarray(lines, dtype=np.int64)
        if lines.shape != (2,) or np.any((lines != 0) & (lines != 1)):
            raise ValueError("two binary line levels required")
        delta = np.zeros(2, dtype=np.int64) if self.previous is None else lines - self.previous
        self.ages = np.where(delta != 0, 0, np.minimum(self.ages + 1, AGE_CAP))
        if self.previous is None:
            self.ages[:] = 0
        self.previous = lines.copy()
        if integer:
            return np.column_stack(((2 * lines - 1) * 16384, delta * 16384,
                                    (self.ages * 16384 + 63) // 127)).reshape(6)
        return np.column_stack((2 * lines - 1, delta, self.ages / AGE_CAP)).reshape(6)


def features(lines):
    encoder = LineFeatures()
    return np.array([encoder.step(pair) for pair in lines])


@dataclass(frozen=True)
class StreamEvent:
    kind: int
    observation_tick: int
    decision_tick: int


def rounded_shift(values, bits):
    return (values + (1 << (bits - 1))) >> bits


class StreamReceiver:
    def __init__(self, weights, mode="float", margin=.15, control="trained"):
        if mode not in ("float", "quantized") or control not in ("trained", "disabled", "no_recurrence"):
            raise ValueError("unknown arithmetic or control")
        expected = initial_weights(0)
        self.weights = {key: np.asarray(weights[key], dtype=np.float64).copy() for key in expected}
        if any(self.weights[k].shape != v.shape or not np.all(np.isfinite(self.weights[k]))
               for k, v in expected.items()):
            raise ValueError("weight shapes/values disagree with architecture")
        if np.any(self.weights["wh"] * (1 - MASK)):
            raise ValueError("weight outside fixed recurrent connection pattern")
        self.mode, self.margin, self.control = mode, margin, control
        self.encoder = LineFeatures()
        self.state = np.zeros(NODES, dtype=np.int64 if mode == "quantized" else np.float64)
        self.last_class, self.last_tick = NONE, -1
        self.logits = np.zeros(8)
        if mode == "quantized":
            self.q = {k: np.clip(np.floor(v * 4096 + .5), -32768, 32767).astype(np.int64)
                      for k, v in self.weights.items()}
            self.leaks = (LEAKS * 32768).astype(np.int64)
            # Constructed off-line, equivalent to a loaded ROM; step uses integers only.
            self.lut = np.floor(np.tanh(np.arange(-2048, 2049) / 256) * 16384 + .5).astype(np.int64)
            self.qmargin = int(np.floor(margin * (1 << 26) + .5))

    def step(self, lines, tick):
        if tick != self.last_tick + 1:
            raise ValueError("continuous consecutive ticks required")
        self.last_tick = tick
        x = self.encoder.step(lines, self.mode == "quantized")
        recurrence = self.control != "no_recurrence"
        if self.mode == "float":
            w = self.weights
            drive = w["wx"] @ x + w["b"]
            if recurrence:
                drive += w["wh"] @ self.state
            self.state = (1 - LEAKS) * self.state + LEAKS * np.tanh(drive)
            if self.control == "disabled":
                self.state[:] = 0
            self.logits = w["wo"] @ self.state + w["bo"]
            threshold = self.margin
        else:
            w = self.q
            drive = w["wx"] @ x + (w["b"] << 14)
            if recurrence:
                drive += w["wh"] @ self.state
            index = np.clip(rounded_shift(drive, 18), -2048, 2048) + 2048
            proposal = self.lut[index]
            self.state = np.clip(rounded_shift((32768 - self.leaks) * self.state
                                               + self.leaks * proposal, 15), -16384, 16384)
            if self.control == "disabled":
                self.state[:] = 0
            self.logits = w["wo"] @ self.state + (w["bo"] << 14)
            threshold = self.qmargin
        order = np.argsort(self.logits)
        kind = int(order[-1])
        if self.logits[order[-1]] - self.logits[order[-2]] < threshold:
            kind = INVALID
        event = StreamEvent(kind, tick, tick) if kind != NONE and kind != self.last_class else None
        self.last_class = kind
        return event


def save_weights(path, weights, **metadata):
    np.savez_compressed(path, **weights, metadata=json.dumps(dict(
        architecture_hash=ARCHITECTURE_HASH, **metadata)))


def load_weights(path):
    with np.load(path, allow_pickle=False) as saved:
        metadata = json.loads(str(saved["metadata"]))
        if metadata["architecture_hash"] != ARCHITECTURE_HASH:
            raise ValueError("architecture hash mismatch")
        return {key: saved[key].copy() for key in initial_weights(0)}, metadata
