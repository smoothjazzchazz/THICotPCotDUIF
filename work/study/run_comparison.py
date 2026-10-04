"""Run with: python -m work.study.run_comparison --output work/study/results/latest"""

import argparse
from dataclasses import asdict
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

from work.model.reservoir_model import make_reservoir_config
from work.study.comparison import (
    METHODS, collect_states, evaluate, measure, train_and_select, verify_reload,
)
from work.study.select_reservoir import candidate_configs, select_reservoir, state_diagnostics
from work.study.signals import make_stream


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def run(args):
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Separate seed ranges keep training and validation from reusing a waveform seed.
    seed_base = args.data_seed * 100000
    train = [make_stream(seed_base + i, args.patterns, 1, .005)
             for i in range(args.train_streams)]
    validation = [make_stream(seed_base + 10000 + i, args.patterns, 1, .01)
                  for i in range(args.validation_streams)]
    selection_report = None
    if args.select_reservoir:
        config, selected, selection_report = select_reservoir(
            train, validation, candidate_configs(args.seed, args.candidate_count),
            progress=lambda message: print(message, flush=True))
        write_json(output / "selection.json", selection_report)
        if config is None:
            raise ValueError(f"No reservoir passed screening; see {output / 'selection.json'}")
        print(f"Selected reservoir: {selection_report['selected_candidate']}", flush=True)
    else:
        config = make_reservoir_config(args.seed)
        print("Collecting integer states; fitting and selecting readouts on train/validation...", flush=True)
        selected = train_and_select(train, [collect_states(s, config) for s in train],
                                    validation, [collect_states(s, config) for s in validation], config)
    training_diagnostics = state_diagnostics([collect_states(s, config) for s in train], config)
    frozen = {"schema_version": 1, "methods": selected}
    # Save the chosen settings before creating test data; nothing below tunes them.
    write_json(output / "config.json", frozen)
    frozen_hash = hashlib.sha256((output / "config.json").read_bytes()).hexdigest()
    print("Settings frozen. Evaluating held-out streams...", flush=True)
    test_seed = args.data_seed if args.test_seed is None else args.test_seed
    test_seed_base = test_seed * 100000
    conditions = {"clean": (0, 0), "jitter": (2, 0), "glitches": (0, .02), "mixed": (2, .02)}
    condition_metrics = {}
    all_streams = []
    combined_predictions = {name: [] for name in METHODS}
    saved_traces = {}
    for index, (name, (jitter, flips)) in enumerate(conditions.items()):
        streams = [make_stream(test_seed_base + 20000 + index * 10000 + i,
                               args.patterns, jitter, flips) for i in range(args.test_streams)]
        states = [collect_states(stream, config) for stream in streams]
        metrics, traces = evaluate(streams, states, selected)
        for stream, state in zip(streams, states, strict=True):
            verify_reload(stream, state, selected)
        condition_metrics[name] = metrics
        saved_traces[name] = {"streams": [asdict(stream) for stream in streams],
                              "states": [state.tolist() for state in states], "methods": traces}
        all_streams.extend(streams)
        for method in METHODS:
            combined_predictions[method].extend(traces[method]["predictions"])
        if name == "mixed":
            trace_example = (streams, states, traces)
    aggregate = {}
    for method, predictions in combined_predictions.items():
        settings = selected[method]
        hold = settings.get("receiver", settings)["hold_ticks"]
        # Pool detections across conditions rather than averaging their F1 scores.
        aggregate[method], _ = measure(all_streams, predictions, hold)
    source_root = Path(__file__).resolve().parents[2]
    sources = sorted((source_root / "work/model").glob("*.py"))
    sources += sorted((source_root / "work/study").glob("*.py"))
    result = {
        "scope": "Synthetic pulse-order study; shared integer reservoir, interchangeable readouts",
        "reservoir_seed": config.seed, "arguments": {**vars(args), "output": str(output)},
        "test_seed": test_seed, "reservoir_selection": selection_report,
        "test_streams": len(all_streams), "test_patterns": len(all_streams) * args.patterns,
        "split_seeds": {"train": [s.seed for s in train], "validation": [s.seed for s in validation],
                        "test": [s.seed for s in all_streams]},
        "selection_objective": "Validation event F1, then balanced tick accuracy, then fewer false events",
        "config_sha256": frozen_hash, "reload_verified": True,
        "training_state_diagnostics": training_diagnostics,
        # Record the exact source bytes used for this run, including its comments.
        "source_sha256": {str(path.relative_to(source_root)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sources},
        "versions": {"python": platform.python_version(),
                     **{name: importlib.metadata.version(name) for name in ("numpy", "matplotlib")}},
        "selected": selected, "conditions": condition_metrics, "aggregate": aggregate,
    }
    write_json(output / "metrics.json", result)
    with gzip.open(output / "traces.json.gz", "wt") as handle:
        json.dump(saved_traces, handle, allow_nan=False)
    from work.study.report import write_report
    write_report(output, result, *trace_example)
    for name, title in METHODS.items():
        row = aggregate[name]
        print(f"{title:23} event F1 {row['event_f1']:6.1%} | "
              f"balanced accuracy {row['balanced_accuracy']:6.1%} | "
              f"unknown recall {row['unknown_recall']:6.1%}")
    print(f"Report: {output / 'report.html'}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("work/study/results/latest"))
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--data-seed", type=int, default=23, help="independent seed for waveform splits")
    parser.add_argument("--test-seed", type=int, help="fresh test waveform seed; defaults to --data-seed")
    parser.add_argument("--select-reservoir", action="store_true", help="search reservoir settings on train/validation")
    parser.add_argument("--candidate-count", type=int, default=3,
                        help="number of consecutive topology seeds starting at --seed; five settings per seed")
    parser.add_argument("--train-streams", type=int, default=12)
    parser.add_argument("--validation-streams", type=int, default=6)
    parser.add_argument("--test-streams", type=int, default=6, help="streams per test condition")
    parser.add_argument("--patterns", type=int, default=24, help="patterns in each continuous stream")
    args = parser.parse_args()
    if args.candidate_count < 1 or (args.test_seed is not None and args.test_seed < 0):
        parser.error("Use a positive candidate count and a nonnegative test seed")
    if args.seed < 0 or args.data_seed < 0 or args.patterns < 3 or any(not 1 <= count < 10000 for count in
                                               (args.train_streams, args.validation_streams,
                                                args.test_streams)):
        parser.error("Use a nonnegative seed, at least 3 patterns and 1–9999 streams per split")
    run(args)


if __name__ == "__main__":
    main()
