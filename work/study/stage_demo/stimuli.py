"""Synthetic pulse examples and scoring annotations; never imported by inference."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedPulse:
    name: str
    start_tick: int
    width: int
    class_id: int | None


def training_examples():
    # These labels belong only to offline fitting. No online stage sees them.
    examples = []
    for width, class_id in ((2, 0), (4, 1)):
        for prefix in (8, 12):
            examples.append((class_id, [0] * prefix + [1] * width + [0] * 8))
    return examples


def demonstration():
    levels = [0] * 8
    expected = []
    for name, width, class_id in (
        ("known short", 2, 0), ("unfamiliar width", 3, None),
        ("known long", 4, 1), ("one-tick glitch", 1, None),
        ("known short after junk", 2, 0),
    ):
        expected.append(ExpectedPulse(name, len(levels), width, class_id))
        levels.extend([1] * width + [0] * 8)
    return levels, expected
