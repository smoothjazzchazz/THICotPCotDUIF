"""Separate mixed-leak study; run with python -m work.study.run_mixed_leaks."""

import argparse
from dataclasses import asdict
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

from work.model.reservoir_model import ReservoirConfig
from work.study.comparison import collect_states, evaluate, measure, select_reference, verify_reload
from work.study.mixed_leaks import EXPERIMENT, fit_candidates, memory_probe_streams
from work.study.run_comparison import write_json
from work.study.signals import make_stream


def reserve_output(output):
    """Refuse protected trees and nonempty output, including symlink aliases."""
    output = output.resolve()
    results = Path(__file__).resolve().parent / "results"
    for name in ("latest", "selected"):
        protected = (results / name).resolve()
        if output == protected or protected in output.parents or output in protected.parents:
            raise ValueError(f"Protected original results: {protected}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    return output


def development_streams():
    """Use original training/validation distributions and separate seed ranges."""
    base = EXPERIMENT["data_seed"] * 100000
    train = [make_stream(base + i, EXPERIMENT["patterns"], *EXPERIMENT["train_noise"])
             for i in range(EXPERIMENT["train_streams"])]
    validation = [make_stream(base + 10000 + i, EXPERIMENT["patterns"], *EXPERIMENT["validation_noise"])
                  for i in range(EXPERIMENT["validation_streams"])]
    return train, validation


def held_out_streams(development_seeds):
    """Called only after disk freeze; identical objects are used for every candidate."""
    base = EXPERIMENT["test_seed"] * 100000
    conditions = {}
    for index, (name, noise) in enumerate(EXPERIMENT["test_conditions"].items()):
        seeds = [base + 20000 + index * 10000 + i for i in range(EXPERIMENT["test_streams"])]
        if set(seeds) & set(development_seeds):
            raise ValueError("Test seeds overlap development seeds")
        conditions[name] = [make_stream(seed, EXPERIMENT["patterns"], *noise) for seed in seeds]
    return conditions


def evaluate_candidate(output, name, frozen, reference, conditions, record, provenance):
    """Replay saved receivers; save all held-out traces and reuse the original report."""
    from work.study.report import write_report

    directory = output / name
    directory.mkdir()
    config = ReservoirConfig(**frozen["reservoir"])
    selected = {**frozen["methods"], "run_length": reference}
    write_json(directory / "config.json", {"schema_version": 1, "methods": selected})
    condition_metrics = {}
    saved_traces = {}
    all_streams = []
    predictions = {method: [] for method in selected}
    for condition, streams in conditions.items():
        states = [collect_states(stream, config) for stream in streams]
        metrics, traces = evaluate(streams, states, selected)
        for stream, state in zip(streams, states, strict=True):
            verify_reload(stream, state, selected)
        condition_metrics[condition] = metrics
        saved_traces[condition] = {"streams": [asdict(stream) for stream in streams],
                                   "states": [state.tolist() for state in states], "methods": traces}
        all_streams.extend(streams)
        for method in selected:
            predictions[method].extend(traces[method]["predictions"])
        if condition == "mixed":
            trace_example = streams, states, traces
    aggregate = {}
    for method, guesses in predictions.items():
        hold = selected[method].get("receiver", selected[method])["hold_ticks"]
        aggregate[method], _ = measure(all_streams, guesses, hold)
    result = {**provenance, "candidate": name, "reservoir_seed": config.seed,
              "test_streams": len(all_streams), "test_patterns": len(all_streams) * EXPERIMENT["patterns"],
              "training_state_diagnostics": record["training"], "selected": selected,
              "conditions": condition_metrics, "aggregate": aggregate, "reload_verified": True,
              "eligible": not record["rejection_reasons"], "rejection_reasons": record["rejection_reasons"]}
    write_json(directory / "metrics.json", result)
    with gzip.open(directory / "traces.json.gz", "wt") as handle:
        json.dump(saved_traces, handle, allow_nan=False)
    write_report(directory, result, *trace_example)
    # The shared report describes one configuration. Make its diagnostic status visible.
    report_path = directory / "report.html"
    notice = (f"<p class='note'><strong>Mixed-leak experiment: {name}.</strong> "
              f"{'Eligible' if result['eligible'] else 'Rejected; diagnostic evaluation only'}. "
              "See the <a href='../report.html'>experiment audit and memory probes</a>.</p>")
    report_path.write_text(report_path.read_text().replace("<h1>", notice + "<h1>", 1))
    return {"conditions": condition_metrics, "aggregate": aggregate, "reload_verified": True}


def run(output):
    output = reserve_output(output)
    source_root = Path(__file__).resolve().parents[2]
    sources = sorted((source_root / "work/model").glob("*.py"))
    sources += sorted((source_root / "work/study").glob("*.py"))
    provenance = {
        "scope": "Fixed seed24 taps, per-node leaks only; one 16-node six-bit integer reservoir",
        "experiment": EXPERIMENT,
        "source_sha256": {str(path.relative_to(source_root)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sources},
        "versions": {"python": platform.python_version(),
                     **{name: importlib.metadata.version(name) for name in ("numpy", "matplotlib")}},
        "selection_policy": (
            "Unchanged readout grids and event-F1 setting selection. Original saturation, "
            "binary-diversity and initialization screens; no full-state probe collisions "
            "at any offset, including across prefixes; full-state readout correct on every "
            "reset-probe tick and >=90% for each continuous pair/offset; full-state validation "
            "precision, known recall and unknown recall each >=80%. Rank survivors using "
            "the unchanged mean Hamming/full-state validation key. Rejected candidates are "
            "fitted/evaluated for diagnosis only. No fallback if every candidate fails."),
    }
    # Save the policy before any fitting, and freeze every method before any test data.
    write_json(output / "plan.json", provenance)
    train, validation = development_streams()
    probes = memory_probe_streams()
    audit, candidates = fit_candidates(train, validation, probes,
                                       progress=lambda message: print(message, flush=True))
    reference = select_reference(validation)
    write_json(output / "selection.json", audit)
    write_json(output / "config.json", {"schema_version": 1,
                                        "selected_candidate": audit["selected_candidate"],
                                        "candidates": candidates, "reference": reference})
    frozen_bytes = (output / "config.json").read_bytes()
    provenance["config_sha256"] = hashlib.sha256(frozen_bytes).hexdigest()
    # Evaluate what was serialized, rather than the in-memory objects used in fitting.
    frozen = json.loads(frozen_bytes)
    print(f"Frozen selection: {audit['selected_candidate'] or 'none; all candidates rejected'}. "
          "Generating fresh shared test streams.", flush=True)
    conditions = held_out_streams([s.seed for s in train + validation])
    provenance["split_seeds"] = {"train": [s.seed for s in train],
                                 "validation": [s.seed for s in validation],
                                 "test": {name: [s.seed for s in streams] for name, streams in conditions.items()}}
    dataset = {name: [asdict(stream) for stream in streams] for name, streams in conditions.items()}
    write_json(output / "test_streams.json", dataset)
    provenance["test_dataset_sha256"] = hashlib.sha256((output / "test_streams.json").read_bytes()).hexdigest()
    results = {}
    for record in audit["candidates"]:
        name = record["name"]
        print(f"{name}: held-out evaluation and streaming reload checks", flush=True)
        results[name] = evaluate_candidate(output, name, frozen["candidates"][name],
                                          frozen["reference"], conditions, record, provenance)
    # Store complete probe inputs, states, scores and decisions for independent inspection.
    probe_traces = {"records": [{**record, "stream": asdict(record["stream"])} for record in probes],
                    "candidates": {}}
    for name, candidate in frozen["candidates"].items():
        config = ReservoirConfig(**candidate["reservoir"])
        streams = [record["stream"] for record in probes]
        states = [collect_states(stream, config) for stream in streams]
        methods = {**candidate["methods"], "run_length": frozen["reference"]}
        _, traces = evaluate(streams, states, methods)
        for stream, state in zip(streams, states, strict=True):
            verify_reload(stream, state, methods)
        probe_traces["candidates"][name] = {"states": [s.tolist() for s in states], "methods": traces}
    with gzip.open(output / "memory_traces.json.gz", "wt") as handle:
        json.dump(probe_traces, handle, allow_nan=False)
    if (output / "config.json").read_bytes() != frozen_bytes:
        raise AssertionError("Settings changed after freeze")
    result = {**provenance, "selected_candidate": audit["selected_candidate"], "candidates": results,
              "reload_verified": True, "config_unchanged_after_test": True}
    write_json(output / "metrics.json", result)
    from work.study.mixed_leak_report import write_mixed_report
    write_mixed_report(output, audit, result)
    print(f"Report: {output / 'report.html'}", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("work/study/results/mixed-leaks-seed24-test104"))
    args = parser.parse_args()
    run(args.output)


if __name__ == "__main__":
    main()
