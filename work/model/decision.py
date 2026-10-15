"""Reject weak/ambiguous scores, stabilize candidates, and emit explicit events."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Classification:
    class_id: int | None  # None here means evaluated and unknown, not idle.
    score: float | None
    margin: float | None
    reason: str


@dataclass(frozen=True)
class SymbolEvent:
    class_id: int | None
    start_tick: int
    decision_tick: int


@dataclass(frozen=True)
class DecisionOutput:
    candidate: Classification | None
    stable_ticks: int
    event: SymbolEvent | None


class DecisionStage:
    """Emit once per uninterrupted candidate run, including unknown runs.

    Missing scores break the run; they are not repeated evidence. Use hold_ticks=1
    for a one-tick completion trigger, or a continuous readout for longer holds.
    """

    def __init__(self, minimum_score=0.0, minimum_margin=0.0, hold_ticks=1):
        if not isinstance(hold_ticks, int) or hold_ticks < 1:
            raise ValueError("hold_ticks must be a positive integer")
        if not isfinite(minimum_score) or not isfinite(minimum_margin) or minimum_margin < 0:
            raise ValueError("thresholds must be finite and margin nonnegative")
        self.minimum_score = minimum_score
        self.minimum_margin = minimum_margin
        self.hold_ticks = hold_ticks
        self.reset()

    def reset(self):
        self.pending = None
        self.start_tick = None
        self.stable_ticks = 0
        self.emitted = False

    def classify(self, scores):
        if not scores or any(not isfinite(score) for _, score in scores):
            return Classification(None, None, None, "no usable scores")
        ranked = sorted(scores, key=lambda item: item[1], reverse=True)
        class_id, score = ranked[0]
        margin = score - ranked[1][1] if len(ranked) > 1 else None
        if score < self.minimum_score:
            return Classification(None, score, margin, "below score threshold")
        if margin is not None and (margin == 0 or margin < self.minimum_margin):
            return Classification(None, score, margin, "ambiguous")
        return Classification(class_id, score, margin, "accepted")

    def step(self, readout, tick):
        if readout is None:
            self.reset()
            return DecisionOutput(None, 0, None)
        candidate = self.classify(readout.scores)
        if self.pending is None or candidate.class_id != self.pending.class_id:
            self.start_tick = readout.start_tick
            self.stable_ticks = 0
            self.emitted = False
        self.pending = candidate
        self.stable_ticks += 1
        event = None
        if self.stable_ticks >= self.hold_ticks and not self.emitted:
            event = SymbolEvent(candidate.class_id, self.start_tick, tick)
            self.emitted = True
        return DecisionOutput(candidate, self.stable_ticks, event)
