"""Two interchangeable memories: step(TemporalSample) -> immutable value tuple."""

from dataclasses import dataclass
from math import isfinite, tanh


class ExplicitHistory:
    """Oldest-to-newest feature frames, zero padded after reset."""

    def __init__(self, depth=4):
        if not isinstance(depth, int) or depth < 1:
            raise ValueError("depth must be a positive integer")
        self.depth = depth
        self.reset()

    def reset(self):
        self.frames = [(0.0, 0.0, 0.0)] * self.depth

    def step(self, sample):
        self.frames = self.frames[1:] + [sample.features]
        return self.state

    @property
    def state(self):
        return tuple(value for frame in self.frames for value in frame)


@dataclass(frozen=True)
class ReservoirConfig:
    # Hand-written, deterministic starting point; no topology search is implied.
    input_weights: tuple = ((0.8, 0.2, 0.1), (0.3, -0.4, 0.2), (-0.2, 0.5, 0.4))
    recurrent_weights: tuple = ((0.5, 0.2, 0.0), (0.0, 0.7, 0.1), (0.1, 0.0, 0.3))
    leak: float = 0.75


class RecurrentReservoir:
    """Small floating-point comparison, not the reference integer arithmetic."""

    def __init__(self, config=None):
        config = ReservoirConfig() if config is None else config
        # Copy rows so separately constructed stages never share mutable weights.
        self.config = ReservoirConfig(
            tuple(tuple(row) for row in config.input_weights),
            tuple(tuple(row) for row in config.recurrent_weights), config.leak)
        size = len(self.config.input_weights)
        if size == 0 or len(self.config.recurrent_weights) != size:
            raise ValueError("reservoir matrices must have the same nonzero row count")
        if any(len(row) != 3 for row in self.config.input_weights):
            raise ValueError("each input row needs three temporal features")
        if any(len(row) != size for row in self.config.recurrent_weights):
            raise ValueError("recurrent matrix must be square")
        if not 0 < self.config.leak <= 1:
            raise ValueError("leak must be in (0, 1]")
        for row in self.config.input_weights + self.config.recurrent_weights:
            if not all(isfinite(value) for value in row):
                raise ValueError("reservoir weights must be finite")
        self.reset()

    def reset(self):
        self.state = (0.0,) * len(self.config.input_weights)

    def step(self, sample):
        old_state = self.state
        new_state = []
        for node, input_row in enumerate(self.config.input_weights):
            drive = 0.0
            for weight, value in zip(input_row, sample.features):
                drive += weight * value
            for weight, value in zip(self.config.recurrent_weights[node], old_state):
                drive += weight * value
            new_state.append((1 - self.config.leak) * old_state[node]
                             + self.config.leak * tanh(drive))
        # Commit together: node order must not affect this tick's recurrence.
        self.state = tuple(new_state)
        return self.state


class RunHistory:
    """Duration slots updated on observed edges, cleared at observed frame start.

    The chronological slots encode alternating high/low runs. Overflow is marked
    by the framer/count gate, never hidden by shifting off a malformed prefix.
    Relative normalization is performed only on a completed frame, so each
    feature sees the same causally available total duration.
    """

    def __init__(self, depth=15, relative=False, duration_scale=16.0):
        if not isinstance(depth, int) or depth < 1:
            raise ValueError("depth must be positive")
        if not isfinite(duration_scale) or duration_scale <= 0:
            raise ValueError("duration_scale must be finite and positive")
        self.depth = depth
        self.relative = relative
        self.duration_scale = duration_scale
        self.reset()

    def reset(self):
        self.durations = [0.0] * self.depth
        self.count = 0

    @property
    def state(self):
        divisor = sum(self.durations) if self.relative else self.duration_scale
        divisor = max(divisor, 1.0)
        return tuple(value / divisor for value in self.durations)

    def step(self, sample):
        if sample.frame_started:
            self.reset()
        elif sample.frame_active and sample.completed_run is not None:
            if self.count < self.depth:
                self.durations[self.count] = sample.completed_run.duration
            self.count = min(self.count + 1, self.depth + 1)
        return self.state


class LastFallingLatch:
    """Run a memory continuously and retain its last falling-edge snapshot.

    Delimiter waiting does not overwrite the decision snapshot. The underlying
    memory is NOT reset on frame boundaries; prefix contamination stays visible.
    Extra storage is one full state vector plus a returned immutable snapshot.
    """

    def __init__(self, memory):
        self.memory = memory
        self.reset()

    def reset(self):
        self.memory.reset()
        self.latched = tuple(self.memory.state)
        self.state = self.latched

    def step(self, sample):
        live = self.memory.step(sample)
        if sample.transition == -1:
            self.latched = tuple(live)
        self.state = self.latched if sample.frame_complete else live
        return self.state
