"""Digital conditioning of one already sampled lane; no analog simulation."""

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ConditionedSample:
    raw_level: int
    delayed_level: int
    level: int


class InputConditioner:
    """Delay samples, then accept a level after N consecutive equal samples.

    delay_ticks is a deterministic sample pipeline, not a metastability model.
    With delay_ticks=0 and stable_ticks=1 this is pass-through.
    """

    def __init__(self, stable_ticks=1, delay_ticks=0, initial_level=0):
        if not isinstance(stable_ticks, int) or stable_ticks < 1:
            raise ValueError("stable_ticks must be a positive integer")
        if not isinstance(delay_ticks, int) or delay_ticks < 0:
            raise ValueError("delay_ticks must be a nonnegative integer")
        if initial_level not in (0, 1):
            raise ValueError("initial_level must be 0 or 1")
        self.stable_ticks = stable_ticks
        self.delay_ticks = delay_ticks
        self.initial_level = initial_level
        self.reset()

    def reset(self):
        self.delay_line = deque([self.initial_level] * self.delay_ticks)
        self.level = self.initial_level
        self.pending_level = self.initial_level
        self.pending_count = 0

    def step(self, input_level):
        if input_level not in (0, 1):
            raise ValueError("input samples must be 0 or 1")
        self.delay_line.append(input_level)
        delayed_level = self.delay_line.popleft()
        if delayed_level != self.pending_level:
            self.pending_level = delayed_level
            self.pending_count = 0
        self.pending_count = min(self.pending_count + 1, self.stable_ticks)
        if self.pending_count == self.stable_ticks:
            self.level = self.pending_level
        return ConditionedSample(input_level, delayed_level, self.level)
