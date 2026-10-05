"""Deterministic timing diagnostics, separate from fitting and held-out evidence."""

from itertools import product

import numpy as np

from work.model.reservoir_model import FeatureExtractor, IntegerReservoir
from work.study.comparison import collect_states
from work.study.delay_chains import EXPERIMENT
from work.study.signals import RECOGNITION_TICKS, SignalStream, WARMUP_TICKS


def pulse_probe(first, second, gap, class_id):
    levels = [0] * WARMUP_TICKS + [1] * first + [0] * gap + [1] * second
    onset = len(levels)
    levels += [0] * RECOGNITION_TICKS
    targets = [2] * onset + [class_id] * RECOGNITION_TICKS
    return SignalStream(-1, levels, targets,
                        [{"class_id": class_id, "start": onset, "end": len(levels)}], 0, 0)


def first_pulse_delay(gap, second_width, offset):
    # Last first-pulse high is at WARMUP + first - 1; final falling edge is
    # WARMUP + first + gap + second. Subtract and include the decision offset.
    return gap + second_width + 1 + offset


def verify_chain(config, age_weight):
    """Check every snapshot and flush, using identical features for both starts.

The induction is independent of input: node 0 overwrites its old value; each
successor copies one old predecessor. Thus update 16 overwrites every initial
node. This concerns reservoir state only, not arbitrary FeatureExtractor state.
"""
    extractor = FeatureExtractor()
    left, right = IntegerReservoir(config), IntegerReservoir(config)
    left.state, right.state = (-32,) * 16, (31,) * 16
    initial = left.state
    inputs, gaps, snapshots = [], [], []
    levels = [0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0] * 2
    for tick, level in enumerate(levels):
        features = extractor.step(level)
        q = features[0] + age_weight * features[2]
        inputs.append(q)
        a, b = left.step(features), right.step(features)
        expected = tuple(inputs[tick - node] if node <= tick else initial[node - tick - 1]
                         for node in range(16))
        if a != expected:
            raise AssertionError(f"Chain propagation differs at tick {tick}")
        gaps.append(max(abs(x - y) for x, y in zip(a, b, strict=True)))
        snapshots.append(list(a))
    if any(gaps[15:]):
        raise AssertionError("Initial reservoir values survive update 16")
    return {"levels": levels, "root_inputs": inputs, "states": snapshots,
            "maximum_initial_gap_by_update": gaps, "first_equal_update": gaps.index(0) + 1,
            "scope": "Identical feature sequences; FeatureExtractor state is not flushed by this claim"}


def boundary_diagnostics(configs):
    """Vary durations on a fixed, small grid; no random test streams are used.

For each required comparison, gap and second width cover the entire +/-1 and
+/-2 grids. First widths receive the same -range, 0, or +range change on both
sides. This isolates timing loss; it is not an exhaustive perturbation study.
Snapshots are (four decision offsets, 16 nodes), after each sample update.
"""
    records = []
    for radius in EXPERIMENT["boundary_duration_ranges"]:
        for known, unknown, class_id in (((3, 8), (8, 8), 0), ((8, 3), (3, 3), 1)):
            for first_delta, gap_delta, second_delta in product(
                    (-radius, 0, radius), range(-radius, radius + 1), range(-radius, radius + 1)):
                gap, second = 3 + gap_delta, known[1] + second_delta
                first_a, first_b = known[0] + first_delta, unknown[0] + first_delta
                streams = [pulse_probe(first_a, second, gap, class_id),
                           pulse_probe(first_b, second, gap, 7)]
                delays = [first_pulse_delay(gap, second, offset) for offset in range(4)]
                entry = {"range": radius, "nominal_known": list(known),
                         "nominal_unknown": list(unknown), "first_delta": first_delta,
                         "first_widths": [first_a, first_b], "gap": gap, "second": second,
                         "last_first_high_delay": delays,
                         "last_first_high_inside": [delay <= 15 for delay in delays], "candidates": {}}
                for name, config in configs.items():
                    windows = []
                    for stream in streams:
                        onset = stream.windows[0]["start"]
                        windows.append(collect_states(stream, config)[onset:onset + 4])
                    a, b = windows
                    entry["candidates"][name] = {
                        "full_distance": np.abs(a - b).sum(axis=1).tolist(),
                        "bit_distance": np.count_nonzero((a >= 0) != (b >= 0), axis=1).tolist(),
                        "decision_states": [a.tolist(), b.tolist()],
                    }
                records.append(entry)
    return {"scope": "Development timing grid, never used for fitting or held-out scores",
            "records": records}
