"""Run the same pipeline with history, recurrence, or the original pulse baseline."""

import argparse
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
import hashlib
import io
import json
from pathlib import Path
import sys

from work.model.conditioning import InputConditioner
from work.model.controller import MappingController
from work.model.decision import DecisionStage
from work.model.memory import ExplicitHistory, RecurrentReservoir
from work.model.readout import PrototypeReadout, PulseLengthReadout
from work.model.system_simple_model import StagedReceiver, print_trace, run_simulation
from work.model.temporal import TemporalEncoder
from work.model.transmit_simple_model import Transmitter
from work.study.stage_demo.fitting import fit_prototypes
from work.study.stage_demo.scoring import score_trace
from work.study.stage_demo.stimuli import demonstration, training_examples


@dataclass(frozen=True)
class DemoConfig:
    memory: str = "history"
    stable_ticks: int = 1
    delay_ticks: int = 0


def make_receiver(config, prototypes=None, minimum_score=0.0, minimum_margin=0.0):
    if config.memory in ("history", "pulse"):
        memory = ExplicitHistory(depth=4)
    elif config.memory == "reservoir":
        memory = RecurrentReservoir()
    else:
        raise ValueError("memory must be history, reservoir, or pulse")
    readout = (PulseLengthReadout({2: 0, 4: 1}) if config.memory == "pulse" else
               PrototypeReadout({} if prototypes is None else prototypes))
    return StagedReceiver(
        InputConditioner(stable_ticks=config.stable_ticks, delay_ticks=config.delay_ticks),
        TemporalEncoder(), memory, readout,
        DecisionStage(minimum_score, minimum_margin, hold_ticks=1))


def build_receiver(config):
    if config.memory == "pulse":
        return make_receiver(config)
    # Training is complete before the demonstration samples are constructed.
    prototypes, score, margin = fit_prototypes(
        training_examples(), lambda: make_receiver(config))
    return make_receiver(config, prototypes, score, margin)


def run_demo(config):
    receiver = build_receiver(config)
    levels, expected = demonstration()
    trace = run_simulation(iter(levels), receiver=receiver,
                           controller=MappingController({0: 2, 1: 1}),
                           transmitter=Transmitter(patterns={2: (1, 0), 1: (0, 1)}))
    results = score_trace(trace, expected, config.stable_ticks, config.delay_ticks)
    return receiver, levels, trace, results


def save_results(directory, config, receiver, levels, trace, results, rendered_trace):
    repo = Path(__file__).resolve().parents[3]
    directory = directory.resolve()
    study_root = repo / "work/study"
    if not directory.is_relative_to(study_root):
        raise ValueError("example results must stay under work/study")
    directory.mkdir(parents=True, exist_ok=False)
    sources = sorted((repo / "work/model").glob("*.py")) + sorted(Path(__file__).parent.glob("*.py"))
    hashes = {str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sources}
    memory_config = (asdict(receiver.memory.config) if isinstance(receiver.memory, RecurrentReservoir)
                     else {"depth": receiver.memory.depth})
    manifest = {
        "command": "python3 -B -m work.study.stage_demo.run_demo " + " ".join(sys.argv[1:]),
        "config": asdict(config), "seed": None, "deterministic": True,
        "memory_parameters": memory_config,
        "prototypes": getattr(receiver.readout, "prototypes", None),
        "pulse_mapping": getattr(receiver.readout, "pulse_length_to_class", None),
        "decision": {"minimum_score": receiver.decision.minimum_score,
                     "minimum_margin": receiver.decision.minimum_margin, "hold_ticks": 1},
        "controller_mapping": {0: 2, 1: 1}, "tx_patterns": {2: [1, 0], 1: [0, 1]},
        "training_examples": training_examples(), "input_levels": levels,
        "source_sha256": hashes, "results": results,
        "scope": "Deterministic demonstration; not held-out performance or hardware evidence.",
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (directory / "trace.txt").write_text(rendered_trace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", choices=("history", "reservoir", "pulse"), default="history")
    parser.add_argument("--stable-ticks", type=int, choices=(1, 2), default=1,
                        help="1: pass through; 2: suppress isolated glitches")
    parser.add_argument("--delay-ticks", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--output", type=Path, help="new result directory under work/study")
    args = parser.parse_args()
    config = DemoConfig(args.memory, args.stable_ticks, args.delay_ticks)
    receiver, levels, trace, results = run_demo(config)
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_trace(f"Stage demo: {asdict(config)}", trace)
        print("\nPer-condition diagnostic (no held-out accuracy claim):")
        for condition in results["conditions"]:
            print(f"  {condition['condition']}: {condition['observed']}; "
                  f"correct={condition['correct']}, "
                  f"raw-start latency={condition['raw_start_to_decision']}")
        print("False known events on unfamiliar/background:",
              results["false_known_events_on_unfamiliar_or_background"])
        print("All expected:", results["all_expected"])
    rendered_trace = buffer.getvalue()
    print(rendered_trace, end="")
    if args.output is not None:
        save_results(args.output, config, receiver, levels, trace, results, rendered_trace)


if __name__ == "__main__":
    main()
