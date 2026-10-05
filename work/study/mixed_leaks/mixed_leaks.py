"""Opt-in leak experiment: fixed taps, task memory, and stricter eligibility.

The original selector and model are reused without changing their policies.
Probe states have shape (context, decision tick, node); tick zero includes the
state update caused by the final falling-edge sample.
"""

from copy import deepcopy
from itertools import product

import numpy as np

from work.study.shared.comparison import collect_states, evaluate, train_and_select
from work.study.readout_comparison.select_reservoir import (
    candidate_configs, initial_state_diagnostics, joint_validation_key,
    rejection_reasons, state_diagnostics,
)
from work.study.shared.signals import RECOGNITION_TICKS, SignalStream, WARMUP_TICKS


# Fixed before held-out evaluation. These are study choices, not chip requirements.
EXPERIMENT = {
    "topology_seed": 24, "base_candidate": "seed24/forward_leak0",
    "data_seed": 23, "test_seed": 104,
    "train_streams": 12, "validation_streams": 6, "test_streams": 6, "patterns": 24,
    "train_noise": [1, .005], "validation_noise": [1, .01],
    "test_conditions": {"clean": [0, 0], "jitter": [2, 0],
                        "glitches": [0, .02], "mixed": [2, .02]},
    "leak_patterns": {
        "uniform0": [0] * 16, "uniform1": [1] * 16,
        "uniform2": [2] * 16, "uniform3": [3] * 16,
        "alternating02": [0, 2] * 8, "alternating20": [2, 0] * 8,
        "cycle0123": [0, 1, 2, 3] * 4, "cycle3210": [3, 2, 1, 0] * 4,
    },
    "pulse_pairs": [[3, 8], [8, 3], [3, 3], [5, 5], [8, 8]],
    "pair_classes": [0, 1, 7, 7, 7], "gap_ticks": 3,
    "preceding_patterns": 2, "context_rest_ticks": [12, 20],
    "minimum_probe_recall": .9,
    "minimum_validation_precision": .8, "minimum_validation_recall": .8,
    "minimum_validation_unknown_recall": .8,
}


def mixed_candidates():
    """Copy the documented selected topology; only the 16 leaks may vary."""
    base = dict(candidate_configs(EXPERIMENT["topology_seed"], 1))[EXPERIMENT["base_candidate"]]
    for name, leaks in EXPERIMENT["leak_patterns"].items():
        config = deepcopy(base)
        config.leak_shifts = list(leaks)
        yield name, config


def memory_probe_streams():
    """Reset/20-low probe plus all two-pair prefixes at both normal rest limits.

Each stream resets once. Prefixes are shared across target alternatives, never
reset at target onset, and receive labels only for diagnostic scoring afterward.
All five nominal pairs appear as prefixes and targets, including unknown (5,5).
"""
    pairs = [tuple(pair) for pair in EXPERIMENT["pulse_pairs"]]
    classes = dict(zip(pairs, EXPERIMENT["pair_classes"], strict=True))
    contexts = [("reset", (), 0)]
    for rest in EXPERIMENT["context_rest_ticks"]:
        for prefix in product(pairs, repeat=EXPERIMENT["preceding_patterns"]):
            label = f"{prefix[0]} then {prefix[1]}; rest={rest}"
            contexts.append((label, prefix, rest))
    records = []
    for context, prefix, rest in contexts:
        for pair in pairs:
            levels = [0] * WARMUP_TICKS
            targets = [2] * WARMUP_TICKS
            windows = []
            for index, (first, second) in enumerate((*prefix, pair)):
                pulse = [1] * first + [0] * EXPERIMENT["gap_ticks"] + [1] * second
                levels.extend(pulse)
                targets.extend([2] * len(pulse))
                start = len(levels)
                trailing = rest if index < len(prefix) else RECOGNITION_TICKS
                levels.extend([0] * trailing)
                class_id = classes[first, second]
                targets.extend([class_id] * RECOGNITION_TICKS + [2] * (trailing - RECOGNITION_TICKS))
                windows.append({"class_id": class_id, "start": start,
                                "end": start + RECOGNITION_TICKS})
            records.append({"context": context, "pair": list(pair),
                            "stream": SignalStream(-1, levels, targets, windows, 0, 0)})
    return records


def memory_diagnostics(probes, states):
    """Separate pulse information from sign quantization and prefix interference.

Matched-context distance changes only the first pulse. Cross-context distance
allows unrelated prefixes to differ too. Within-target diameter measures the
largest prefix effect for the same target. Distances are raw integer L1 counts
or Hamming bit counts; neither is a recognition score.
"""
    by_pair = {}
    for record, state in zip(probes, states, strict=True):
        start = record["stream"].windows[-1]["start"]
        by_pair.setdefault(tuple(record["pair"]), []).append(state[start:start + RECOGNITION_TICKS])
    comparisons = []
    for known, unknown in (((3, 8), (8, 8)), ((8, 3), (3, 3))):
        left, right = np.asarray(by_pair[known]), np.asarray(by_pair[unknown])
        entry = {"known": list(known), "unknown": list(unknown)}
        for name, a, b in (("full", left, right), ("bits", left >= 0, right >= 0)):
            a, b = a.astype(int), b.astype(int)
            distances = np.abs(a - b).sum(axis=-1)
            # Exclude the reset-only case when measuring continuous-prefix effects.
            ac, bc = a[1:], b[1:]
            cross = np.abs(ac[:, None] - bc[None, :]).sum(axis=-1)
            within_a = np.abs(ac[:, None] - ac[None, :]).sum(axis=-1)
            within_b = np.abs(bc[:, None] - bc[None, :]).sum(axis=-1)
            entry[name] = {
                "reset_distance": distances[0].tolist(),
                "continuous_min_distance": distances[1:].min(axis=0).tolist(),
                "continuous_max_distance": distances[1:].max(axis=0).tolist(),
                "cross_context_min_distance": cross.min(axis=(0, 1)).tolist(),
                "within_target_max_distance": np.maximum(
                    within_a.max(axis=(0, 1)), within_b.max(axis=(0, 1))).tolist(),
                "matched_context_distances": distances.tolist(),
            }
        comparisons.append(entry)
    return {"decision_offsets": list(range(RECOGNITION_TICKS)),
            "contexts": list(dict.fromkeys(record["context"] for record in probes)),
            "comparisons": comparisons}


def probe_readout_diagnostics(probes, traces):
    """Measure fitted decisions at each target tick, grouped by exact pulse pair.

Readouts are fitted on ordinary training streams, never these clean probes.
Minimum recall across pairs and offsets catches dependence on irrelevant history
that a pooled known-event F1 or a state-distance plot can hide.
"""
    result = {}
    for method, trace in traces.items():
        by_pair = {}
        for record, predictions in zip(probes, trace["predictions"], strict=True):
            window = record["stream"].windows[-1]
            actual = np.asarray(predictions[window["start"]:window["end"]])
            by_pair.setdefault(str(tuple(record["pair"])), []).append(actual == window["class_id"])
        pairs = {}
        for pair, correct in by_pair.items():
            correct = np.asarray(correct)
            pairs[pair] = {"reset_correct": correct[0].tolist(),
                           "continuous_recall_by_tick": correct[1:].mean(axis=0).tolist()}
        result[method] = {
            "pairs": pairs,
            "minimum_continuous_recall": min(min(row["continuous_recall_by_tick"]) for row in pairs.values()),
            "all_reset_ticks_correct": all(all(row["reset_correct"]) for row in pairs.values()),
        }
    return result


def eligibility_reasons(record):
    """Keep old screens and require usable full-state memory and rejection."""
    reasons = rejection_reasons(record["training"], record["initial_state"])
    for pair in record["memory"]["comparisons"]:
        label = f"{pair['known']} versus {pair['unknown']}"
        for key in ("reset_distance", "continuous_min_distance", "cross_context_min_distance"):
            if min(pair["full"][key]) == 0:
                reasons.append(f"full-state collision: {label}, {key}")
    learned = record["probe_readouts"]["linear_full"]
    if not learned["all_reset_ticks_correct"]:
        reasons.append("full-state readout misses a clean reset-probe decision tick")
    if learned["minimum_continuous_recall"] < EXPERIMENT["minimum_probe_recall"]:
        reasons.append("full-state readout below 90% on a continuous probe pair/offset")
    metrics = record["validation"]["linear_full"]
    for metric, limit in (("event_precision", "minimum_validation_precision"),
                          ("event_recall", "minimum_validation_recall"),
                          ("unknown_recall", "minimum_validation_unknown_recall")):
        if metrics[metric] < EXPERIMENT[limit]:
            reasons.append(f"full-state validation {metric} below {EXPERIMENT[limit]:.0%}")
    return reasons


def fit_candidates(train, validation, probes, progress=print):
    """Fit every candidate for diagnosis, but select only fully eligible ones.

No test streams enter here. Existing readout grids and ranking are unchanged;
the original mean Hamming/full-state key ranks only the experiment's survivors.
"""
    if not train or not validation or {s.seed for s in train} & {s.seed for s in validation}:
        raise ValueError("Nonempty, disjoint training and validation streams required")
    audit = {"selected_candidate": None, "candidates": []}
    frozen = {}
    best_key = None
    for name, config in mixed_candidates():
        progress(f"{name}: fitting three readouts on shared states")
        training_states = [collect_states(stream, config) for stream in train]
        validation_states = [collect_states(stream, config) for stream in validation]
        probe_states = [collect_states(record["stream"], config) for record in probes]
        methods = train_and_select(train, training_states, validation, validation_states,
                                   config, include_reference=False)
        _, traces = evaluate([record["stream"] for record in probes], probe_states, methods)
        record = {"name": name, "config": config.to_dict(),
                  "training": state_diagnostics(training_states, config),
                  "initial_state": initial_state_diagnostics(config, train[0].levels),
                  "memory": memory_diagnostics(probes, probe_states),
                  "probe_readouts": probe_readout_diagnostics(probes, traces),
                  "validation": {method: row["validation"] for method, row in methods.items()},
                  "selection_key": list(joint_validation_key(methods))}
        record["rejection_reasons"] = eligibility_reasons(record)
        key = tuple(record["selection_key"])
        if not record["rejection_reasons"] and (best_key is None or key > best_key):
            best_key = key
            audit["selected_candidate"] = name
        audit["candidates"].append(record)
        frozen[name] = {"reservoir": config.to_dict(), "methods": methods}
        progress(f"{name}: {len(record['rejection_reasons'])} rejection reasons; "
                 f"validation full-state F1={record['validation']['linear_full']['event_f1']:.1%}")
    return audit, frozen
