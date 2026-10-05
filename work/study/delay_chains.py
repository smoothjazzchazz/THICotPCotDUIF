"""Two fixed finite-memory candidates and two legacy diagnostic controls.

Each evaluation uses one existing 16-node, six-bit IntegerReservoir. No model
arithmetic or readout policy changes here. Only the two chains can be selected.
"""

from copy import deepcopy

from work.model.reservoir_model import ReservoirConfig
from work.study.comparison import collect_states, evaluate, train_and_select
from work.study.mixed_leaks import (
    EXPERIMENT as MIXED_EXPERIMENT, eligibility_reasons, memory_diagnostics,
    mixed_candidates, probe_readout_diagnostics,
)
from work.study.select_reservoir import (
    candidate_configs, initial_state_diagnostics, joint_validation_key, state_diagnostics,
)


# Fixed before fitting. The inherited requirements are the unchanged mixed-leak
# policy; that experiment's dictionaries and candidate settings are never mutated.
EXPERIMENT = {
    "nodes": 16, "state_bits": 6, "history_ticks": 15,
    "root_age_weights": {"age_chain": -1, "level_chain": 0},
    "controls": ["seed24_forward_leak0", "cycle3210"],
    "data_seed": 23, "test_seed": 105, "development_test_seeds": [23, 24, 104],
    "train_streams": 12, "validation_streams": 6, "test_streams": 6, "patterns": 24,
    "train_noise": [1, .005], "validation_noise": [1, .01],
    "test_conditions": {"clean": [0, 0], "jitter": [2, 0],
                        "glitches": [0, .02], "mixed": [2, .02]},
    "boundary_duration_ranges": [1, 2],
    "requirements": {
        "minimum_binary_fingerprints": 2, "maximum_saturated_fraction": .5,
        "maximum_initial_state_gap": 1, "full_state_collisions_allowed": 0,
        "all_reset_decisions_correct": True,
        **{key: deepcopy(MIXED_EXPERIMENT[key]) for key in (
            "minimum_probe_recall", "minimum_validation_precision",
            "minimum_validation_recall", "minimum_validation_unknown_recall")},
    },
}


def delay_candidates():
    """Keep all tap slots, using valid indices even where weights are zero."""
    nodes = EXPERIMENT["nodes"]
    for name, age_weight in EXPERIMENT["root_age_weights"].items():
        recurrent = []
        inputs = []
        for node in range(nodes):
            recurrent.append([[max(0, node - 1), int(node > 0)], [0, 0], [1, 0]])
            inputs.append([[0, int(node == 0)], [2, age_weight if node == 0 else 0]])
        yield name, ReservoirConfig(EXPERIMENT["state_bits"], [0] * nodes,
                                    recurrent, inputs)
    yield "seed24_forward_leak0", dict(candidate_configs(24, 1))["seed24/forward_leak0"]
    yield "cycle3210", dict(mixed_candidates())["cycle3210"]


def choose_chain(records):
    """Use the original joint key; a legacy control can never be a fallback."""
    selected = None
    best_key = None
    for record in records:
        if record["name"] not in EXPERIMENT["root_age_weights"] or record["rejection_reasons"]:
            continue
        key = tuple(record["selection_key"])
        if best_key is None or key > best_key:
            selected, best_key = record["name"], key
    return selected


def decision_counts(probes, traces):
    """Save actual class counts, not just correctness, for every target/offset."""
    result = {}
    for method, trace in traces.items():
        groups = {}
        for probe, predictions in zip(probes, trace["predictions"], strict=True):
            key = str(tuple(probe["pair"]))
            window = probe["stream"].windows[-1]
            group = groups.setdefault(key, {"target": window["class_id"],
                                            "reset": None,
                                            "continuous": [{} for _ in range(4)]})
            choices = predictions[window["start"]:window["end"]]
            if probe["context"] == "reset":
                group["reset"] = choices
            else:
                for offset, choice in enumerate(choices):
                    counts = group["continuous"][offset]
                    label = str(choice)
                    counts[label] = counts.get(label, 0) + 1
        result[method] = groups
    return result


def fit_candidates(train, validation, probes, progress=print):
    """Reuse identical state snapshots and fitting budgets for all three readouts.

Only training fits coefficients. Validation chooses the original ridge/decision/M
grid. Clean probes screen these choices; they do not fit or retune them.
"""
    if not train or not validation or {s.seed for s in train} & {s.seed for s in validation}:
        raise ValueError("Nonempty, disjoint training and validation streams required")
    records, frozen = [], {}
    streams = [probe["stream"] for probe in probes]
    for name, config in delay_candidates():
        progress(f"{name}: fitting three readouts on shared states")
        train_states = [collect_states(s, config) for s in train]
        validation_states = [collect_states(s, config) for s in validation]
        probe_states = [collect_states(s, config) for s in streams]
        methods = train_and_select(train, train_states, validation, validation_states,
                                   config, include_reference=False)
        _, traces = evaluate(streams, probe_states, methods)
        record = {
            "name": name, "role": "candidate" if name in EXPERIMENT["root_age_weights"] else "control",
            "config": config.to_dict(), "training": state_diagnostics(train_states, config),
            "initial_state": initial_state_diagnostics(config, train[0].levels),
            "memory": memory_diagnostics(probes, probe_states),
            "probe_readouts": probe_readout_diagnostics(probes, traces),
            "decision_counts": decision_counts(probes, traces),
            "validation": {method: row["validation"] for method, row in methods.items()},
            "selection_key": list(joint_validation_key(methods)),
        }
        record["rejection_reasons"] = eligibility_reasons(record)
        record["eligible"] = record["role"] == "candidate" and not record["rejection_reasons"]
        records.append(record)
        frozen[name] = {"reservoir": config.to_dict(), "methods": methods}
        progress(f"{name}: {len(record['rejection_reasons'])} rejection reasons; "
                 f"validation full-state F1={record['validation']['linear_full']['event_f1']:.1%}")
    return {"selected_candidate": choose_chain(records), "candidates": records}, frozen
