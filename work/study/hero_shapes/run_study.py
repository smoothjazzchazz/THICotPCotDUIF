"""Fit/develop, freeze, then confirm through the existing shared runner."""

import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from work.model.system_simple_model import print_trace

from .fitting import fit, calibrate
from .models import candidate_configs, cost, simulate
from .scoring import observations, passes, score_trace
from .stimuli import FAMILIES, build_stream, build_startup_streams


ROOT = Path(__file__).resolve().parents[3]
SEEDS = {"train": 17301, "dev": 29303, "heldout": 94709, "startup": 85703}
REPEATS = {"train": 8, "dev": 5, "heldout": 8}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def source_hashes():
    files = sorted((ROOT / "work/model").glob("*.py"))
    files += sorted((ROOT / "work/study/hero_shapes").glob("*.py"))
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in files}


def make_stream(family, split):
    return build_stream(family, split, SEEDS[split], repeats=REPEATS[split])


def save_trace(path, title, trace, case):
    lo = max(0, case["start_tick"] - 5)
    hi = min(len(trace), case["end_tick"] + 32)
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print("OFFLINE ANNOTATION (never supplied to inference):")
        print(json.dumps(case, sort_keys=True))
        print_trace(title, trace[lo:hi])
        print("Frame completion: " + str([
            {"tick": r["tick"], "valid": r["receiver_state"].temporal.frame_valid,
             "run_count": r["receiver_state"].temporal.frame_run_count}
            for r in trace[lo:hi] if r["receiver_state"].temporal.frame_complete]))
    path.write_text(buffer.getvalue())


def screen(output):
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for family in FAMILIES:
        training = make_stream(family, "train")
        development = make_stream(family, "dev")
        write_json(output / "inputs" / f"{family}-train.json", training)
        write_json(output / "inputs" / f"{family}-dev.json", development)
        for initial in candidate_configs(family):
            config, provenance = fit(initial, training)
            config, trials, collisions = calibrate(config, development)
            directory = output / family / config["kind"]
            trace = simulate(development["samples"], config)
            result = score_trace(trace, development, config)
            # Verify the offline threshold sweep equals a fully executed receiver.
            selected = [t for t in trials if t["minimum_score"] == config["minimum_score"]
                        and t["minimum_margin"] == config["minimum_margin"]][0]
            if selected["result"]["details"] != result["details"]:
                raise AssertionError("offline threshold screen differs from shared execution")
            write_json(directory / "config.json", config)
            write_json(directory / "fit.json", provenance)
            write_json(directory / "development_trials.json", trials)
            write_json(directory / "development.json", result)
            write_json(directory / "collisions.json", collisions)
            write_json(directory / "cost.json", cost(config))
            for label, predicate in (
                ("known", lambda d: d["expected"] is not None and d["exact"]),
                ("unknown", lambda d: d["expected"] is None and d["exact"]),
                ("failure", lambda d: not d["exact"])):
                detail = next((d for d in result["details"] if predicate(d)), None)
                if detail is not None and (config["kind"] in ("stream_templates", "stream_intervals", "sample12", "run_history")):
                    case = next(c for c in development["cases"] if c["id"] == detail["case_id"])
                    save_trace(directory / f"development_{label}_trace.txt", config["name"], trace, case)
            rows.append({"name": config["name"], "config": str((directory / "config.json").relative_to(output)),
                         "development_pass": passes(result), "totals": result["totals"]})
            print(config["name"], "development", result["totals"], flush=True)
    write_json(output / "development_summary.json", rows)
    write_json(output / "screen_manifest.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(), "seeds": SEEDS,
        "repeats": REPEATS, "source_hashes": source_hashes(),
        "command": sys.argv, "python": platform.python_version(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "initial_search_budget": "3 families x 8 architectures x <=12 rejection settings",
        "selection": "zero false known first; then worst-condition known recall; all architectures retained"})


def freeze(output):
    manifest = json.loads((output / "screen_manifest.json").read_text())
    current = source_hashes()
    if current != manifest["source_hashes"]:
        raise ValueError("source changed since screen; rerun development in a new directory")
    rows = json.loads((output / "development_summary.json").read_text())
    configs = {row["config"]: sha256((output / row["config"]).read_bytes()).hexdigest() for row in rows}
    frozen = output / "frozen_source"
    frozen.mkdir(exist_ok=False)
    for rel in current:
        target = frozen / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)
    write_json(output / "freeze.json", {
        "frozen_utc": datetime.now(timezone.utc).isoformat(), "source_hashes": current,
        "config_hashes": configs, "seeds": SEEDS, "repeats": REPEATS,
        "scoring": "per-condition counts; exact single events; end through end+22; response samples checked separately",
        "confirmation": "all 24 configurations; no revision or threshold selection from heldout",
        "promising_before_confirmation": [r["name"] for r in rows if r["development_pass"]]})
    print("Frozen definitions, implementations, fitted parameters, thresholds and scoring.", flush=True)


def verify_freeze(output):
    frozen = json.loads((output / "freeze.json").read_text())
    if source_hashes() != frozen["source_hashes"]:
        raise ValueError("frozen source hash mismatch")
    for rel, expected in frozen["config_hashes"].items():
        if sha256((output / rel).read_bytes()).hexdigest() != expected:
            raise ValueError(f"frozen configuration changed: {rel}")
    return frozen


def confirm(output):
    frozen = verify_freeze(output)
    if (output / "confirmation_summary.json").exists():
        raise FileExistsError("confirmation already exists; never overwrite evidence")
    # Generate heldout stimuli only after the frozen artifact has been verified.
    streams = {family: make_stream(family, "heldout") for family in FAMILIES}
    startup = {family: build_startup_streams(family, SEEDS["startup"]) for family in FAMILIES}
    for family, stream in streams.items():
        write_json(output / "inputs" / f"{family}-heldout.json", stream)
        write_json(output / "inputs" / f"{family}-startup.json", startup[family])
    summary = []
    for rel in frozen["config_hashes"]:
        config = json.loads((output / rel).read_text())
        directory = (output / rel).parent
        stream = streams[config["family"]]
        trace = simulate(stream["samples"], config)
        result = score_trace(trace, stream, config)
        cold = []
        for cold_stream in startup[config["family"]]:
            cold_trace = simulate(cold_stream["samples"], config)
            cold.append({"name": cold_stream.get("name", "startup"),
                         "result": score_trace(cold_trace, cold_stream, config)})
        write_json(directory / "heldout.json", result)
        write_json(directory / "startup.json", cold)
        write_json(directory / "heldout_observations.json", observations(trace, stream))
        failures = [d for d in result["details"] if not d["exact"]]
        if failures and config["kind"] in ("stream_templates", "stream_intervals", "run_history", "sample12"):
            case = next(c for c in stream["cases"] if c["id"] == failures[0]["case_id"])
            save_trace(directory / "heldout_failure_trace.txt", config["name"], trace, case)
        summary.append({"name": config["name"], "passes": passes(result),
                        "startup_passes": all(passes(c["result"]) for c in cold),
                        "totals": result["totals"], "latency": result["latency"],
                        "response_latency": result["responses"]["decision_to_response"],
                        "cost": cost(config)})
        print(config["name"], "heldout", result["totals"], flush=True)
    write_json(output / "confirmation_summary.json", summary)
    verify_freeze(output)
    print("Confirmation retained, with no model revisions.", flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("phase", choices=("screen", "freeze", "confirm", "verify"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    study = ROOT / "work/study"
    if not output.is_relative_to(study):
        parser.error("results must be within work/study")
    {"screen": screen, "freeze": freeze, "confirm": confirm,
     "verify": verify_freeze}[args.phase](output)


if __name__ == "__main__":
    main()
