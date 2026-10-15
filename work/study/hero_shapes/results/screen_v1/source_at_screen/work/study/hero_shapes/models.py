"""Loaded experiment settings; execution remains in the common model runner."""

from dataclasses import asdict
from random import Random

from work.model.conditioning import InputConditioner
from work.model.controller import MappingController
from work.model.decision import DecisionStage
from work.model.memory import (ExplicitHistory, LastFallingLatch, RecurrentReservoir,
                               ReservoirConfig, RunHistory)
from work.model.readout import FramePrototypeReadout, StreamingTemplateReadout
from work.model.system_simple_model import StagedReceiver, run_simulation
from work.model.temporal import FramedTemporalEncoder
from work.model.transmit_simple_model import Transmitter

from .stimuli import FAMILIES, IDLE_TICKS


RESPONSES = {0: [1, 1, 0, 1, 0], 1: [1, 0, 0, 1, 1, 0]}
MAPPING = {0: 0, 1: 1}


def reservoir_settings(kind, seed=733):
    if kind == "reservoir3":
        return asdict(ReservoirConfig())
    rng = Random(seed)
    size = 16
    inputs = [[rng.uniform(-0.7, 0.7) for _ in range(3)] for _ in range(size)]
    recurrent = [[0.0] * size for _ in range(size)]
    for i in range(size):
        if kind == "ring16":
            recurrent[i][(i - 1) % size] = 0.92
        else:
            for j in rng.sample(range(size), 3):
                recurrent[i][j] = rng.choice((-0.28, 0.28))
            recurrent[i][i] += 0.35
    return {"input_weights": inputs, "recurrent_weights": recurrent,
            "leak": 0.45 if kind == "ring16" else 0.25}


def candidate_configs(family):
    definition = FAMILIES[family]
    runs = len(definition["templates"][0])
    common = {"family": family, "stable_ticks": 2, "delay_ticks": 1,
              "idle_ticks": IDLE_TICKS, "max_runs": 31, "max_frame_ticks": 512,
              "expected_runs": runs, "minimum_score": 0.0, "minimum_margin": 0.0,
              "prototypes": {}, "mapping": MAPPING, "responses": RESPONSES}
    result = []
    for kind in ("stream_templates", "run_history", "sample12", "sample64",
                 "reservoir3", "ring16", "sparse16"):
        config = dict(common, kind=kind, name=f"{family}/{kind}")
        if kind == "stream_templates":
            config.update(templates=definition["templates"], scales=definition["scales"])
        elif kind == "run_history":
            config.update(depth=runs, relative=(family == "relative_order"),
                          duration_scale=16.0)
        elif kind.startswith("sample"):
            config["depth"] = int(kind.removeprefix("sample"))
        else:
            config["reservoir"] = reservoir_settings(kind)
        result.append(config)
    return result


def build_receiver(config):
    kind = config["kind"]
    if kind == "stream_templates":
        # A one-frame history exposes the live features for traces; it contributes
        # nothing to template recognition and can be omitted in an implementation.
        memory = ExplicitHistory(1)
        readout = StreamingTemplateReadout(
            {int(k): v for k, v in config["templates"].items()}, config["scales"])
    else:
        if kind == "run_history":
            memory = RunHistory(config["depth"], config["relative"], config["duration_scale"])
        elif kind.startswith("sample"):
            memory = LastFallingLatch(ExplicitHistory(config["depth"]))
        else:
            memory = LastFallingLatch(RecurrentReservoir(ReservoirConfig(**config["reservoir"])))
        readout = FramePrototypeReadout(
            {int(k): vectors for k, vectors in config["prototypes"].items()},
            expected_runs=config["expected_runs"])
    return StagedReceiver(
        InputConditioner(config["stable_ticks"], config["delay_ticks"]),
        FramedTemporalEncoder(config["idle_ticks"], config["max_runs"],
                              config["max_frame_ticks"],
                              config["delay_ticks"] + config["stable_ticks"] - 1),
        memory, readout,
        DecisionStage(config["minimum_score"], config["minimum_margin"]))


def simulate(samples, config):
    return run_simulation(iter(samples), build_receiver(config),
                          MappingController({int(k): v for k, v in config["mapping"].items()}),
                          Transmitter(patterns={int(k): v for k, v in config["responses"].items()}))


def cost(config):
    """Algorithmic numeric slots/operations, never bits, gates or physical rates."""
    kind = config["kind"]
    params = sum(len(v) for rows in config["prototypes"].values() for v in rows)
    common = {"conditioning_delay_samples": config["delay_ticks"],
              "shared_control": "conditioner levels/count; encoder run/tick; framer flags/count/start; decision/controller records",
              "schedule": "RX stages execute within one modeled tick; TX first; unbounded software TX queue",
              "score_parameter_values": params,
              "prototype_vectors": sum(len(rows) for rows in config["prototypes"].values())}
    if kind == "stream_templates":
        hypotheses = len(config["templates"]) * len(config["scales"])
        common.update(memory_values=3, latch_values=0, numeric_state_values=hypotheses,
                      loaded_values=sum(map(len, config["templates"].values())) + len(config["scales"]),
                      arithmetic=f"per completed run: {hypotheses} relative errors/max updates; no temporal matrix products",
                      note="three feature values are trace-only; run index and hypothesis errors carry recognition")
    elif kind == "run_history":
        common.update(memory_values=config["depth"], latch_values=0,
                      arithmetic=f"one stored duration per edge; {config['depth']} normalization divisions each sample in this readable implementation",
                      note="loaded run-count gate plus duration slots; normalization could be deferred to decision but is not timed here")
    elif kind.startswith("sample"):
        n = 3 * config["depth"]
        common.update(memory_values=n, latch_values=n,
                      arithmetic=f"shift {config['depth']} frames/sample; {params} squared differences per decision")
    else:
        n = len(config["reservoir"]["input_weights"])
        nonzero = sum(w != 0 for row in config["reservoir"]["recurrent_weights"] for w in row)
        common.update(memory_values=n, latch_values=n, loaded_values=n * (n + 3) + 1,
                      recurrent_nonzero=nonzero,
                      arithmetic=f"actual dense loops: {n*(n+3)} drive products + {2*n} blend products + {n} tanh/sample; {params} squared differences/decision",
                      note="sparse conceptual connectivity still uses dense Python arithmetic; floating-point sensitivity is unquantized")
    return common
