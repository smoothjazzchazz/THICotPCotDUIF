"""Synthetic pulse-order task. These waveforms are not a protocol standard."""

from dataclasses import dataclass
import random


CLASS_IDS = (0, 1, 2, 7)
CLASS_NAMES = ("short-long", "long-short", "background", "unknown")
RECOGNITION_TICKS = 4
WARMUP_TICKS = 20


@dataclass
class SignalStream:
    seed: int
    levels: list
    targets: list
    windows: list
    jitter: int
    flip_probability: float


def make_stream(seed, patterns=24, jitter=1, flip_probability=0.0):
    """Label four ticks after the final falling edge, never the shared prefix.

Noise changes the samples, not the intended labels. The receiver never receives
the labels or the pattern boundaries. State continues across patterns.
"""
    rng = random.Random(seed)
    order = [(0, 1, 7)[i % 3] for i in range(patterns)]
    rng.shuffle(order)
    levels = [0] * WARMUP_TICKS
    targets = [2] * WARMUP_TICKS
    windows = []
    for class_id in order:
        if class_id == 0:
            widths = (3, 8)
        elif class_id == 1:
            widths = (8, 3)
        else:
            widths = rng.choice([(3, 3), (5, 5), (8, 8)])
        first, second = [max(1, width + rng.randint(-jitter, jitter))
                         for width in widths]
        gap = max(1, 3 + rng.randint(-jitter, jitter))
        pulse = [1] * first + [0] * gap + [1] * second
        levels.extend(pulse)
        targets.extend([2] * len(pulse))
        # The next sample is the falling edge: only now is the whole pair available.
        onset = len(levels)
        rest = rng.randint(12, 20)
        levels.extend([0] * rest)
        targets.extend([class_id] * RECOGNITION_TICKS
                       + [2] * (rest - RECOGNITION_TICKS))
        windows.append({"class_id": class_id, "start": onset,
                        "end": onset + RECOGNITION_TICKS})
    for tick in range(WARMUP_TICKS, len(levels)):
        if rng.random() < flip_probability:
            levels[tick] = 1 - levels[tick]
    return SignalStream(seed, levels, targets, windows, jitter, flip_probability)


def run_length_predictions(levels, tolerance):
    """Causal two-pulse template listener with the same four-tick label window.

It sees samples only. A low run of eight ticks separates pairs; the distance is
the absolute width/gap error summed across the three runs.
"""
    templates = ((3, 3, 8), (8, 3, 3))
    first = None
    high = low = gap = 0
    held_class = 2
    hold_until = 0
    result = []
    for tick, level in enumerate(levels):
        if level:
            if high == 0:
                gap = low
            high += 1
            low = 0
        else:
            low += 1
            if high:
                # A falling edge completes a pulse; classify only after the second.
                if first is None:
                    first = high
                else:
                    measured = (first, gap, high)
                    distances = [sum(abs(a - b) for a, b in zip(measured, row))
                                 for row in templates]
                    best = min(range(2), key=lambda i: distances[i])
                    held_class = (best if distances[best] <= tolerance
                                  and distances[0] != distances[1] else 7)
                    hold_until = tick + RECOGNITION_TICKS
                    first = None
                high = 0
            if low >= 8:
                # A long idle gap discards any unfinished pair, including glitch fragments.
                first = None
        result.append(held_class if tick < hold_until else 2)
    return result
