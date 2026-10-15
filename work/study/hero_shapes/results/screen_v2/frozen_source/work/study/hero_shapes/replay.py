"""Load a saved recognition/response configuration and replay a saved stream."""

import argparse
import json
from pathlib import Path

from work.model.system_simple_model import print_trace

from .models import simulate
from .scoring import score_trace


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--case", help="optional annotated case ID to limit displayed ticks")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    stream = json.loads(args.input.read_text())
    trace = simulate(stream["samples"], config)
    print(json.dumps(score_trace(trace, stream, config)["totals"], indent=2))
    shown = trace
    if args.case:
        case = next(case for case in stream["cases"] if case["id"] == args.case)
        shown = trace[max(0, case["start_tick"] - 5):case["end_tick"] + 32]
    print_trace(config["name"], shown)


if __name__ == "__main__":
    main()
