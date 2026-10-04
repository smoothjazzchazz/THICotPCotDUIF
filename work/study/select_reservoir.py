"""Choose one shared reservoir using training diagnostics and validation events.

This module accepts no test data. Its numerical screening limits are experiment
settings, not hardware specifications or a proof of the echo-state property.
"""

from copy import deepcopy
import numpy as np

from work.model.reservoir_model import FeatureExtractor, IntegerReservoir, make_reservoir_config
from work.study.comparison import collect_states, select_reference, train_and_select
from work.study.signals import WARMUP_TICKS


PRIMARY_READOUTS = ("hamming", "linear_full")
MAX_SATURATED_FRACTION = 0.5
MAX_INITIAL_STATE_GAP = 1
PROBE_TICKS = 128
PROBE_TAIL_TICKS = 16


def candidate_configs(first_seed=23, seed_count=3):
    """Keep the node count, arithmetic and tap indices fixed within each seed."""
    if first_seed < 0 or seed_count < 1:
        raise ValueError("Use a nonnegative first seed and a positive seed count")
    for seed in range(first_seed, first_seed + seed_count):
        original = make_reservoir_config(seed)
        yield f"seed{seed}/original", original

        # Copy nested tap lists so changing a candidate cannot change another one.
        independent = deepcopy(original)
        independent.leak_shifts = [min(shift, 1) for shift in original.leak_shifts]
        independent.recurrent_taps = [[[source, 0] for source, _ in row]
                                      for row in original.recurrent_taps]
        # Nodes can still retain their own state where the leak shift is nonzero.
        yield f"seed{seed}/no_recurrence", independent

        for leak in (0, 1, 2):
            forward = deepcopy(original)
            forward.leak_shifts = [leak] * len(original.leak_shifts)
            for node, row in enumerate(forward.recurrent_taps):
                kept_connection = False
                for tap in row:
                    source, weight = tap
                    # Delayed links from lower-index nodes cannot form a loop.
                    if weight and source < node and not kept_connection:
                        kept_connection = True
                    else:
                        tap[1] = 0
            forward.feature_taps = [[[source, 1 if weight > 0 else -1] for source, weight in row]
                                    for row in original.feature_taps]
            yield f"seed{seed}/forward_leak{leak}", forward


def state_diagnostics(states, config):
    samples = np.concatenate([row[WARMUP_TICKS:] for row in states])
    if not len(samples):
        raise ValueError("Training streams need samples after the startup interval")
    bits = (samples >= 0).astype(int)
    low = -(1 << (config.state_bits - 1))
    high = -low - 1
    # Count both individual bits that change and complete patterns the readout sees.
    return {
        "varying_sign_bits": int(np.count_nonzero(np.ptp(bits, axis=0))),
        "distinct_binary_fingerprints": len(np.unique(bits, axis=0)),
        "saturated_state_fraction": float(np.mean((samples == low) | (samples == high))),
    }


def initial_state_diagnostics(config, training_levels):
    """Compare opposite initial states under identical subsequent inputs.

The final 16 ticks must differ by no more than one integer count per node.
Rounding can leave that residual. This does not imply equal quantized bits or
convergence on every input, and does not measure task-specific memory capacity.
"""
    probes = {"idle_low": [0] * PROBE_TICKS, "idle_high": [1] * PROBE_TICKS,
              "training_prefix": training_levels[:PROBE_TICKS]}
    low = -(1 << (config.state_bits - 1))
    high = -low - 1
    gaps = {}
    for name, levels in probes.items():
        if len(levels) < PROBE_TAIL_TICKS:
            raise ValueError("Initial-state probe needs at least 16 input samples")
        left, right = IntegerReservoir(config), IntegerReservoir(config)
        left.state = (low,) * len(config.leak_shifts)
        right.state = (high,) * len(config.leak_shifts)
        features = FeatureExtractor()
        distances = []
        for level in levels:
            # Identical features isolate the effect of the two starting states.
            values = features.step(level)
            a, b = left.step(values), right.step(values)
            distances.append(max(abs(x - y) for x, y in zip(a, b, strict=True)))
        # Check the whole tail, so a brief agreement cannot hide a later divergence.
        gaps[name] = max(distances[-PROBE_TAIL_TICKS:])
    return {"maximum_tail_gap": max(gaps.values()), "probe_tail_gaps": gaps}


def rejection_reasons(state_stats, initial_state_stats):
    reasons = []
    if state_stats["distinct_binary_fingerprints"] < 2:
        reasons.append("constant binary fingerprint")
    if state_stats["saturated_state_fraction"] > MAX_SATURATED_FRACTION:
        reasons.append("more than half the training node samples are saturated")
    if initial_state_stats["maximum_tail_gap"] > MAX_INITIAL_STATE_GAP:
        reasons.append("initial-state probe retains a gap greater than one count")
    return reasons


def joint_validation_key(readouts):
    metrics = [readouts[name]["validation"] for name in PRIMARY_READOUTS]
    # Compare F1 first, then accuracy on a tie; negation favors fewer false events.
    return (sum(row["event_f1"] for row in metrics) / len(metrics),
            sum(row["balanced_accuracy"] for row in metrics) / len(metrics),
            -sum(row["false_events_per_1000_ticks"] for row in metrics) / len(metrics))


def select_reservoir(train, validation, candidates, progress=None):
    """Return (configuration, fitted readouts, audit report), or two Nones.

All surviving candidates receive the same readout fitting/threshold search.
The primary Hamming and full-state linear readouts have equal selection weight.
The one-bit linear readout remains a diagnostic, and the conventional reference
does not influence reservoir selection. Exact ties keep the earlier candidate.
"""
    if not train or not validation:
        raise ValueError("Reservoir selection needs training and validation streams")
    if {stream.seed for stream in train} & {stream.seed for stream in validation}:
        raise ValueError("Training and validation stream seeds must be disjoint")
    report = {
        "objective": "Mean Hamming/full-state-linear validation event F1; then mean balanced accuracy; then fewer false events",
        "screening": {"maximum_saturated_fraction": MAX_SATURATED_FRACTION,
                      "minimum_binary_fingerprints": 2,
                      "maximum_initial_state_gap": MAX_INITIAL_STATE_GAP,
                      "probe_ticks": PROBE_TICKS, "probe_tail_ticks": PROBE_TAIL_TICKS},
        "selected_candidate": None, "candidates": [],
    }
    best_config = best_readouts = best_key = None
    for name, config in candidates:
        train_states = [collect_states(stream, config) for stream in train]
        state_stats = state_diagnostics(train_states, config)
        initial_state_stats = initial_state_diagnostics(config, train[0].levels)
        reasons = rejection_reasons(state_stats, initial_state_stats)
        record = {"name": name, "config": config.to_dict(), "training": state_stats,
                  "initial_state": initial_state_stats, "rejection_reasons": reasons,
                  "validation": None, "selection_key": None}
        # Failed candidates stay in the audit, but never reach readout fitting.
        if reasons:
            if progress:
                progress(f"{name}: rejected ({'; '.join(reasons)})")
        else:
            if progress:
                progress(f"{name}: fitting readouts...")
            validation_states = [collect_states(stream, config) for stream in validation]
            readouts = train_and_select(train, train_states, validation, validation_states,
                                       config, include_reference=False)
            key = joint_validation_key(readouts)
            record["validation"] = {method: row["validation"] for method, row in readouts.items()}
            record["selection_key"] = list(key)
            if best_key is None or key > best_key:
                best_config, best_readouts, best_key = config, readouts, key
                report["selected_candidate"] = name
            if progress:
                progress(f"{name}: mean validation event F1 {key[0]:.1%}")
        report["candidates"].append(record)
    if best_readouts is not None:
        # This listener does not use reservoir states, so select its settings once.
        best_readouts["run_length"] = select_reference(validation)
    return best_config, best_readouts, report
