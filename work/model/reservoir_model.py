"""Tick-level integer reservoir and interchangeable readouts for the Python study.

Encoding, startup and arithmetic choices here are experimental, not a released
hardware contract. There is no synchronizer, clock divider or pipeline delay.
"""

from dataclasses import asdict, dataclass
import random


UNKNOWN = 7


@dataclass
class ReservoirConfig:
    state_bits: int
    leak_shifts: list
    recurrent_taps: list
    feature_taps: list
    seed: int = 0

    def to_dict(self):
        return asdict(self)


def make_reservoir_config(seed=23, nodes=16, state_bits=6):
    if nodes < 3 or state_bits < 2:
        raise ValueError("Need at least three nodes and two state bits")
    rng = random.Random(seed)
    recurrent = []
    inputs = []
    for _ in range(nodes):
        # Each tap is [source index, weight]; a zero weight leaves that link inactive.
        recurrent.append([[j, rng.choice([-1, 0, 0, 0, 1])]
                          for j in rng.sample(range(nodes), 3)])
        inputs.append([[j, rng.choice([-2, -1, 1, 2])]
                       for j in rng.sample(range(3), 2)])
    return ReservoirConfig(state_bits, [rng.randrange(4) for _ in range(nodes)],
                           recurrent, inputs, seed)


class FeatureExtractor:
    """One already-sampled lane: signed level, signed edge, log2 edge age."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.previous = 0
        self.age = 0

    def step(self, level):
        if level not in (0, 1):
            raise ValueError("Input samples must be 0 or 1")
        edge = level - self.previous
        self.age = 0 if edge else min(127, self.age + 1)
        self.previous = level
        # Age buckets are 0, 1, 2–3, 4–7, ... ticks; an edge starts the count over.
        return (2 * level - 1, edge, self.age.bit_length())


class IntegerReservoir:
    def __init__(self, config):
        self.config = config
        self.reset()

    def reset(self):
        self.state = (0,) * len(self.config.leak_shifts)

    def step(self, features):
        low = -(1 << (self.config.state_bits - 1))
        high = -low - 1
        # All nodes read last tick's values, even if their source was updated earlier.
        previous = self.state
        updated = []
        for node, leak in enumerate(self.config.leak_shifts):
            # Shift 0 clears this carryover term; larger shifts retain more old state.
            # Signed shifts round down, so small integer states may stop decaying.
            value = previous[node] - (previous[node] >> leak)
            value += sum(weight * previous[source]
                         for source, weight in self.config.recurrent_taps[node])
            value += sum(weight * features[source]
                         for source, weight in self.config.feature_taps[node])
            # Python integers keep the complete sum; clip once, after all taps.
            updated.append(max(low, min(high, value)))
        self.state = tuple(updated)
        return self.state


def encode_state(state, encoding, scale=32):
    if encoding == "binary":
        return tuple(int(value >= 0) for value in state)
    if encoding == "signed":
        return tuple(value / scale for value in state)
    raise ValueError(f"Unknown state encoding: {encoding}")


class HammingReadout:
    def __init__(self, class_ids, prototypes):
        self.class_ids = tuple(class_ids)
        self.prototypes = tuple(tuple(row) for row in prototypes)

    def score(self, state):
        bits = encode_state(state, "binary")
        # Negate the mismatch count so a closer prototype gets a higher score.
        return tuple(-sum(a != b for a, b in zip(bits, prototype, strict=True))
                     for prototype in self.prototypes)

    def to_dict(self):
        return {"kind": "hamming", "class_ids": self.class_ids,
                "prototypes": self.prototypes, "encoding": "binary"}


class LinearReadout:
    """Floating-point research readout; coefficients are not hardware weights."""

    def __init__(self, class_ids, weights, bias, encoding="signed", scale=32):
        self.class_ids = tuple(class_ids)
        self.weights = tuple(tuple(row) for row in weights)
        self.bias = tuple(bias)
        self.encoding = encoding
        self.scale = scale

    def score(self, state):
        values = encode_state(state, self.encoding, self.scale)
        return tuple(offset + sum(w * x for w, x in zip(row, values, strict=True))
                     for row, offset in zip(self.weights, self.bias, strict=True))

    def to_dict(self):
        return {"kind": "linear_float", "class_ids": self.class_ids,
                "weights": self.weights, "bias": self.bias,
                "encoding": self.encoding, "scale": self.scale}


def readout_from_dict(data):
    if data["kind"] == "hamming":
        return HammingReadout(data["class_ids"], data["prototypes"])
    if data["kind"] == "linear_float":
        return LinearReadout(data["class_ids"], data["weights"], data["bias"],
                             data["encoding"], data["scale"])
    raise ValueError(f"Unknown readout: {data['kind']}")


@dataclass
class DecisionRule:
    minimum_score: float
    minimum_margin: float

    def choose(self, scores, class_ids):
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        best, second = order[:2]
        margin = scores[best] - scores[second]
        # A winner must score well on its own and clearly beat the runner-up.
        if (scores[best] < self.minimum_score or margin <= 1e-12
                or margin < self.minimum_margin):
            return UNKNOWN
        return class_ids[best]


class Stabilizer:
    def __init__(self, hold_ticks=1):
        if not 1 <= hold_ticks <= 7:
            raise ValueError("hold_ticks must be between 1 and 7")
        self.hold_ticks = hold_ticks
        self.reset()

    def reset(self):
        self.candidate = None
        self.emitted_class = None
        self.count = 0
        self.start = 0

    def step(self, class_id, tick):
        if class_id != self.candidate:
            self.candidate = class_id
            self.count = 1
            self.start = tick
        else:
            self.count = min(self.hold_ticks, self.count + 1)
        # Emit once per stable class change, not on every tick of a held class.
        if self.count == self.hold_ticks and class_id != self.emitted_class:
            self.emitted_class = class_id
            # Timestamp the run's start, before the hold delay, in a 12-bit counter.
            return {"class_id": class_id, "start_tick": self.start & 0xFFF}
        return None


class ReservoirReceiver:
    def __init__(self, config, readout, decision, hold_ticks=1):
        self.features = FeatureExtractor()
        self.reservoir = IntegerReservoir(config)
        self.readout = readout
        self.decision = decision
        self.stabilizer = Stabilizer(hold_ticks)
        self.observation = {}

    def reset(self):
        self.features.reset()
        self.reservoir.reset()
        self.stabilizer.reset()
        self.observation = {}

    def step(self, level, tick):
        features = self.features.step(level)
        state = self.reservoir.step(features)
        scores = self.readout.score(state)
        class_id = self.decision.choose(scores, self.readout.class_ids)
        self.observation = {"features": features, "state": state,
                            "scores": scores, "class_id": class_id}
        return self.stabilizer.step(class_id, tick)

    def to_dict(self):
        return {"schema_version": 1, "reservoir": self.reservoir.config.to_dict(),
                "readout": self.readout.to_dict(), "decision": asdict(self.decision),
                "hold_ticks": self.stabilizer.hold_ticks,
                "feature_encoding": "signed_level_signed_edge_log_age_v1"}

    @classmethod
    def from_dict(cls, data):
        if (data["schema_version"] != 1 or data["feature_encoding"]
                != "signed_level_signed_edge_log_age_v1"):
            raise ValueError("Unsupported model configuration")
        return cls(ReservoirConfig(**data["reservoir"]),
                   readout_from_dict(data["readout"]),
                   DecisionRule(**data["decision"]), data["hold_ticks"])
