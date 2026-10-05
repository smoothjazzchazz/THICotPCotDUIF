"""Opt-in finite delay-chain study: python -m work.study.delay_chains.run_delay_chains."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

from work.model.reservoir_model import ReservoirConfig
from work.study.shared.comparison import collect_states, evaluate, measure, select_reference, verify_reload
from work.study.delay_chains.delay_chains import EXPERIMENT, decision_counts, delay_candidates, fit_candidates
from work.study.delay_chains.delay_chain_probes import boundary_diagnostics, verify_chain
from work.study.mixed_leaks.mixed_leaks import memory_probe_streams, probe_readout_diagnostics
from work.study.readout_comparison.run_comparison import write_json
from work.study.shared.signals import make_stream


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reserve_output(output):
    """Require a new path outside every existing saved-results directory."""
    output = output.resolve()
    results = Path(__file__).resolve().parents[1] / "results"
    for path in results.iterdir() if results.exists() else []:
        protected = path.resolve()
        if path.is_dir() and (output == protected or protected in output.parents
                              or output in protected.parents):
            raise ValueError(f"Protected existing results: {protected}")
    if output.exists():
        raise ValueError(f"Output must be new: {output}")
    output.mkdir(parents=True)
    return output


def seed_inventory(results):
    """Check local recorded plans and datasets before reserving the fresh seed."""
    used_paths, scanned = [], []
    test_seed = EXPERIMENT["test_seed"]
    reserved = {test_seed * 100000 + 20000 + condition * 10000 + index
                for condition in range(4) for index in range(EXPERIMENT["test_streams"])}

    def contains_seed(value):
        if isinstance(value, dict):
            if value.get("test_seed") == test_seed or value.get("seed") in reserved:
                return True
            return any(contains_seed(item) for item in value.values())
        if isinstance(value, list):
            return any(contains_seed(item) for item in value)
        return isinstance(value, int) and value in reserved

    for path in sorted(results.rglob("*.json")):
        data = json.loads(path.read_text())
        scanned.append({"path": str(path), "sha256": digest(path)})
        if contains_seed(data):
            used_paths.append(str(path))
    if test_seed in EXPERIMENT["development_test_seeds"] or used_paths:
        raise ValueError(f"Test seed {test_seed} already used: {used_paths}")
    return {"test_seed": test_seed, "prior_use_found": False, "scanned_json": scanned,
            "scope": "Local saved plans, metrics and stream datasets; prior test seeds 23/24/104 are development"}


def development_streams():
    base = EXPERIMENT["data_seed"] * 100000
    train = [make_stream(base + i, EXPERIMENT["patterns"], *EXPERIMENT["train_noise"])
             for i in range(EXPERIMENT["train_streams"])]
    validation = [make_stream(base + 10000 + i, EXPERIMENT["patterns"], *EXPERIMENT["validation_noise"])
                  for i in range(EXPERIMENT["validation_streams"])]
    return train, validation


def held_out_streams(development_seeds):
    # The caller must freeze and reload settings before entering this function.
    conditions = {}
    base = EXPERIMENT["test_seed"] * 100000
    for index, (name, noise) in enumerate(EXPERIMENT["test_conditions"].items()):
        seeds = [base + 20000 + index * 10000 + i for i in range(EXPERIMENT["test_streams"])]
        if set(seeds) & set(development_seeds):
            raise ValueError("Test seeds overlap development seeds")
        conditions[name] = [make_stream(seed, EXPERIMENT["patterns"], *noise) for seed in seeds]
    return conditions


def add_event_counts(metrics):
    for row in metrics.values():
        row["missed_events"] = row["expected_events"] - row["matched_events"]
        row["false_events"] = row["predicted_events"] - row["matched_events"]


def evaluate_candidate(output, record, candidate, reference, conditions, provenance):
    """Reuse event matching, metrics, replay and the original per-receiver plots."""
    from work.study.shared.report import write_report

    name = record["name"]
    directory = output / name
    directory.mkdir()
    config = ReservoirConfig(**candidate["reservoir"])
    methods = {**candidate["methods"], "run_length": reference}
    write_json(directory / "config.json", {"schema_version": 1, "methods": methods})
    condition_metrics, saved = {}, {}
    all_streams = []
    predictions = {method: [] for method in methods}
    for condition, streams in conditions.items():
        states = [collect_states(stream, config) for stream in streams]
        metrics, traces = evaluate(streams, states, methods)
        add_event_counts(metrics)
        for stream, state in zip(streams, states, strict=True):
            verify_reload(stream, state, methods)
        condition_metrics[condition] = metrics
        saved[condition] = {"streams": [asdict(s) for s in streams],
                            "states": [s.tolist() for s in states], "methods": traces}
        all_streams.extend(streams)
        for method in methods:
            predictions[method].extend(traces[method]["predictions"])
        if condition == "mixed":
            trace_example = streams, states, traces
    aggregate = {}
    for method, guesses in predictions.items():
        hold = methods[method].get("receiver", methods[method])["hold_ticks"]
        aggregate[method], _ = measure(all_streams, guesses, hold)
    add_event_counts(aggregate)
    result = {**provenance, "candidate": name, "reservoir_seed": config.seed,
              "test_streams": len(all_streams), "test_patterns": sum(len(s.windows) for s in all_streams),
              "selected": methods, "training_state_diagnostics": record["training"],
              "conditions": condition_metrics, "aggregate": aggregate, "reload_verified": True,
              "role": record["role"], "eligible": record["eligible"],
              "rejection_reasons": record["rejection_reasons"]}
    write_json(directory / "metrics.json", result)
    with gzip.open(directory / "traces.json.gz", "wt") as handle:
        json.dump(saved, handle, allow_nan=False)
    write_report(directory, result, *trace_example)
    path = directory / "report.html"
    status = "Eligible chain" if record["eligible"] else "Diagnostic evaluation; not an eligible chain"
    notice = (f"<p class='note'><strong>Delay-chain experiment: {name}. {status}.</strong> "
              "See the <a href='../report.html'>selection and timing audit</a>.</p>")
    path.write_text(path.read_text().replace("<h1>", notice + "<h1>", 1))
    return {"conditions": condition_metrics, "aggregate": aggregate, "reload_verified": True}


def save_probe_replay(output, probes, frozen, audit):
    saved = {"records": [{**p, "stream": asdict(p["stream"])} for p in probes], "candidates": {}}
    streams = [p["stream"] for p in probes]
    for record in audit["candidates"]:
        name = record["name"]
        candidate = frozen["candidates"][name]
        states = [collect_states(s, ReservoirConfig(**candidate["reservoir"])) for s in streams]
        methods = {**candidate["methods"], "run_length": frozen["reference"]}
        _, traces = evaluate(streams, states, methods)
        for stream, state in zip(streams, states, strict=True):
            verify_reload(stream, state, methods)
        # Recompute pre-test eligibility evidence from the frozen receivers.
        decisions = decision_counts(probes, traces)
        correctness = probe_readout_diagnostics(probes, traces)
        for method in candidate["methods"]:
            if decisions[method] != record["decision_counts"][method] or correctness[method] != record["probe_readouts"][method]:
                raise AssertionError("Frozen probe decisions differ from selection audit")
        saved["candidates"][name] = {"states": [s.tolist() for s in states], "methods": traces,
                                      "decision_counts": decisions}
    with gzip.open(output / "memory_traces.json.gz", "wt") as handle:
        json.dump(saved, handle, allow_nan=False)


def run(output):
    output = reserve_output(output)
    source_root = Path(__file__).resolve().parents[3]
    inventory = seed_inventory(source_root / "work/study/results")
    sources = sorted((source_root / "work/model").glob("*.py"))
    sources += sorted((source_root / "work/study").glob("[!._]*/*.py"))
    provenance = {
        "scope": "Two predetermined zero-leak delay chains; two legacy controls; one reservoir at a time",
        "experiment": EXPERIMENT, "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": {str(p.relative_to(source_root)): digest(p) for p in sources},
        "versions": {"python": platform.python_version(),
                     **{name: importlib.metadata.version(name) for name in ("numpy", "matplotlib")}},
        "seed_inventory": inventory,
        "selection_policy": (
            "Unchanged readout fitting grids and event-F1 objective. Original binary-diversity, "
            "saturation and initialization screens, plus unchanged mixed-leak collision, probe "
            "decision and >=80% validation precision/known recall/unknown recall requirements. "
            "Rank eligible chains only with the original joint Hamming/full-state key. Controls "
            "are never fallback winners. Failed configurations remain diagnostic; no retuning."),
        "predetermined_configurations": {name: config.to_dict() for name, config in delay_candidates()},
    }
    write_json(output / "plan.json", provenance)
    train, validation = development_streams()
    write_json(output / "development_streams.json",
               {"train": [asdict(s) for s in train], "validation": [asdict(s) for s in validation]})
    provenance["development_dataset_sha256"] = digest(output / "development_streams.json")
    probes = memory_probe_streams()
    chains = {name: config for name, config in delay_candidates() if name in EXPERIMENT["root_age_weights"]}
    timing = boundary_diagnostics(chains)
    timing["propagation_and_flush"] = {
        name: verify_chain(config, EXPERIMENT["root_age_weights"][name]) for name, config in chains.items()}
    write_json(output / "timing.json", timing)
    audit, candidates = fit_candidates(train, validation, probes,
                                       progress=lambda message: print(message, flush=True))
    reference = select_reference(validation)
    write_json(output / "selection.json", audit)
    write_json(output / "config.json", {"schema_version": 1, "selected_candidate": audit["selected_candidate"],
                                        "candidates": candidates, "reference": reference})
    freeze = {"frozen_utc": datetime.now(timezone.utc).isoformat(),
              "sha256": {name: digest(output / name) for name in
                         ("plan.json", "development_streams.json", "timing.json", "selection.json", "config.json")}}
    write_json(output / "freeze.json", freeze)
    # Read disk artifacts back before creating even one held-out waveform.
    frozen = json.loads((output / "config.json").read_text())
    audit = json.loads((output / "selection.json").read_text())
    provenance["config_sha256"] = freeze["sha256"]["config.json"]
    print(f"Frozen selection: {audit['selected_candidate']}. Generating shared seed105 tests.", flush=True)
    conditions = held_out_streams([s.seed for s in train + validation])
    write_json(output / "test_streams.json", {name: [asdict(s) for s in streams]
                                             for name, streams in conditions.items()})
    provenance["test_generated_utc"] = datetime.now(timezone.utc).isoformat()
    provenance["test_dataset_sha256"] = digest(output / "test_streams.json")
    provenance["split_seeds"] = {"train": [s.seed for s in train], "validation": [s.seed for s in validation],
                                 "test": {name: [s.seed for s in streams] for name, streams in conditions.items()}}
    results = {}
    for record in audit["candidates"]:
        name = record["name"]
        print(f"{name}: held-out evaluation and reload checks", flush=True)
        results[name] = evaluate_candidate(output, record, frozen["candidates"][name],
                                          frozen["reference"], conditions, provenance)
    save_probe_replay(output, probes, frozen, audit)
    for name, expected in freeze["sha256"].items():
        if digest(output / name) != expected:
            raise AssertionError(f"Frozen artifact changed: {name}")
    result = {**provenance, "selected_candidate": audit["selected_candidate"], "candidates": results,
              "reload_verified": True, "frozen_artifacts_unchanged": True, "freeze": freeze}
    write_json(output / "metrics.json", result)
    from work.study.delay_chains.delay_chain_report import write_delay_report
    write_delay_report(output, audit, result, timing)
    print(f"Report: {output / 'report.html'}", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("work/study/results/delay-chains-test105"))
    run(parser.parse_args().output)


if __name__ == "__main__":
    main()
