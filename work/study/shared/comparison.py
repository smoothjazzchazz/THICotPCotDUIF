"""Fit on training streams, select on validation, then evaluate held-out streams."""

import numpy as np

from work.model.reservoir_model import (
    DecisionRule, FeatureExtractor, HammingReadout, IntegerReservoir,
    LinearReadout, ReservoirReceiver, Stabilizer,
)
from work.study.shared.signals import CLASS_IDS, WARMUP_TICKS, run_length_predictions


METHODS = {
    "hamming": "Hamming / 1-bit",
    "linear_bits": "Linear / 1-bit",
    "linear_full": "Linear / 6-bit",
    "run_length": "Run-length reference",
}


def collect_states(stream, config):
    # Reset once per stream; carry state through every pulse pair within it.
    features = FeatureExtractor()
    reservoir = IntegerReservoir(config)
    return np.asarray([reservoir.step(features.step(level)) for level in stream.levels])


def fit_readout(streams, states, kind, ridge=0.01, scale=32):
    samples = np.concatenate([row[WARMUP_TICKS:] for row in states])
    targets = np.concatenate([stream.targets[WARMUP_TICKS:] for stream in streams])
    classes = (0, 1, 2)
    bits = (samples >= 0).astype(float)
    if kind == "hamming":
        # Each prototype bit is the majority vote from that class's training ticks.
        prototypes = [(bits[targets == class_id].mean(axis=0) >= 0.5).astype(int).tolist()
                      for class_id in classes]
        return HammingReadout(classes, prototypes)
    encoding = "binary" if kind == "linear_bits" else "signed"
    values = bits if encoding == "binary" else samples / scale
    # The constant column lets the solve learn an offset as well as node weights.
    design = np.column_stack([values, np.ones(len(values))])
    # Class 7 has no output column: unknown examples ask all three scores to be zero.
    expected = np.column_stack([targets == class_id for class_id in classes]).astype(float)
    # Equal total weight per target class prevents background from dominating.
    counts = {class_id: np.count_nonzero(targets == class_id) for class_id in CLASS_IDS}
    weights = np.asarray([1 / counts[class_id] for class_id in targets])
    penalty = np.eye(design.shape[1]) * ridge
    penalty[-1, -1] = 0  # The bias does not need shrinkage.
    # Solve the weighted squared-error fit directly; ridge discourages large weights.
    # Only the output weights change here, not the reservoir that made these states.
    coefficients = np.linalg.solve(design.T @ (weights[:, None] * design) + penalty,
                                   design.T @ (weights[:, None] * expected))
    return LinearReadout(classes, coefficients[:-1].T.tolist(),
                         coefficients[-1].tolist(), encoding, scale)


def score_states(readout, states):
    return np.asarray([readout.score(state) for state in states])


def choose_classes(scores, class_ids, decision):
    order = np.argsort(scores, axis=1)
    rows = np.arange(len(scores))
    best = scores[rows, order[:, -1]]
    margin = best - scores[rows, order[:, -2]]
    accepted = ((best >= decision.minimum_score) & (margin > 1e-12)
                & (margin >= decision.minimum_margin))
    return np.where(accepted, np.asarray(class_ids)[order[:, -1]], 7)


def emit_events(predictions, hold_ticks):
    stabilizer = Stabilizer(hold_ticks)
    events = []
    for tick, class_id in enumerate(predictions):
        event = stabilizer.step(int(class_id), tick)
        if event is not None:
            events.append({**event, "emit_tick": tick})
    return events


def measure(streams, predictions, hold_ticks):
    confusion = np.zeros((4, 4), dtype=int)
    class_index = {value: i for i, value in enumerate(CLASS_IDS)}
    true_events = predicted_events = matches = 0
    latencies = []
    timestamp_errors = []
    ticks = 0
    all_events = []
    for stream, predicted in zip(streams, predictions, strict=True):
        events = emit_events(predicted, hold_ticks)
        all_events.append(events)
        # Tick scores cover all four classes; event scores count known patterns only.
        for actual, guess in zip(stream.targets[WARMUP_TICKS:], predicted[WARMUP_TICKS:]):
            confusion[class_index[actual], class_index[int(guess)]] += 1
        ticks += len(predicted) - WARMUP_TICKS
        expected = [window for window in stream.windows if window["class_id"] in (0, 1)]
        true_events += len(expected)
        # A second detection of the same pattern must count as a false event.
        used = set()
        for event in events:
            if event["emit_tick"] < WARMUP_TICKS or event["class_id"] not in (0, 1):
                continue
            predicted_events += 1
            for i, window in enumerate(expected):
                # Fixed six-tick detection window, independent of selected M.
                if (i not in used and event["class_id"] == window["class_id"]
                        and window["start"] <= event["emit_tick"] < window["end"] + 2):
                    used.add(i)
                    matches += 1
                    latencies.append(event["emit_tick"] - window["start"])
                    # Use the shortest signed timestamp difference across 12-bit wrap.
                    delta = (event["start_tick"] - window["start"]) & 0xFFF
                    timestamp_errors.append(delta if delta < 2048 else delta - 4096)
                    break
    recall_by_class = np.divide(np.diag(confusion), confusion.sum(axis=1),
                                out=np.zeros(4), where=confusion.sum(axis=1) != 0)
    precision = matches / predicted_events if predicted_events else 0.0
    recall = matches / true_events if true_events else 0.0
    metrics = {
        "balanced_accuracy": float(recall_by_class.mean()),
        "unknown_recall": float(recall_by_class[3]),
        "event_precision": precision, "event_recall": recall,
        "event_f1": 2 * matches / (predicted_events + true_events)
        if predicted_events + true_events else 0.0,
        "false_events_per_1000_ticks": (predicted_events - matches) * 1000 / ticks,
        "median_latency_ticks": float(np.median(latencies)) if latencies else None,
        "p95_latency_ticks": float(np.percentile(latencies, 95)) if latencies else None,
        "mean_abs_timestamp_error": float(np.mean(np.abs(timestamp_errors)))
        if timestamp_errors else None,
        "confusion": confusion.tolist(), "expected_events": true_events,
        "predicted_events": predicted_events, "matched_events": matches,
        "evaluated_ticks": ticks,
    }
    return metrics, all_events


def selection_key(metrics):
    return (metrics["event_f1"], metrics["balanced_accuracy"],
            -metrics["false_events_per_1000_ticks"])


def train_and_select(train, train_states, validation, validation_states, config, include_reference=True):
    selected = {}
    scale = 1 << (config.state_bits - 1)
    for kind in ("hamming", "linear_bits", "linear_full"):
        best_key = None
        for ridge in ([None] if kind == "hamming" else [0.0001, 0.01, 1.0]):
            readout = fit_readout(train, train_states, kind, ridge, scale)
            scores = [score_states(readout, state) for state in validation_states]
            # Reuse these scores while trying acceptance thresholds and hold times.
            floors = [-16, -12, -8, -6, -4, -2, 0] if kind == "hamming" else [0, .2, .4, .6, .8]
            margins = [0, 1, 2] if kind == "hamming" else [0, .1, .2]
            for floor in floors:
                for margin in margins:
                    decision = DecisionRule(floor, margin)
                    predictions = [choose_classes(row, readout.class_ids, decision) for row in scores]
                    for hold in (1, 2, 3):
                        metrics, _ = measure(validation, predictions, hold)
                        key = selection_key(metrics)
                        if best_key is None or key > best_key:
                            best_key = key
                            receiver = ReservoirReceiver(config, readout, decision, hold)
                            selected[kind] = {"receiver": receiver.to_dict(), "ridge": ridge,
                                              "validation": metrics}
    if include_reference:
        selected["run_length"] = select_reference(validation)
    return selected


def select_reference(validation):
    best_key = None
    selected = None
    for tolerance in (0, 1, 2, 3, 4, 6):
        predictions = [run_length_predictions(stream.levels, tolerance) for stream in validation]
        for hold in (1, 2, 3):
            metrics, _ = measure(validation, predictions, hold)
            key = selection_key(metrics)
            if best_key is None or key > best_key:
                best_key = key
                selected = {"tolerance": tolerance, "hold_ticks": hold, "validation": metrics}
    return selected


def evaluate(streams, states, selected):
    metrics = {}
    traces = {}
    for name, settings in selected.items():
        if name == "run_length":
            predictions = [run_length_predictions(stream.levels, settings["tolerance"])
                           for stream in streams]
            hold = settings["hold_ticks"]
            scores = None
        else:
            receiver = ReservoirReceiver.from_dict(settings["receiver"])
            scores = [score_states(receiver.readout, state) for state in states]
            predictions = [choose_classes(row, receiver.readout.class_ids, receiver.decision)
                           for row in scores]
            hold = receiver.stabilizer.hold_ticks
        metrics[name], events = measure(streams, predictions, hold)
        traces[name] = {"predictions": [np.asarray(row).tolist() for row in predictions],
                        "events": events, "scores": [row.tolist() for row in scores]
                        if scores is not None else None}
    return metrics, traces


def verify_reload(stream, states, selected):
    """Independent streaming path must agree with cached-state evaluation."""
    for name, settings in selected.items():
        if name == "run_length":
            continue
        receiver = ReservoirReceiver.from_dict(settings["receiver"])
        scores = score_states(receiver.readout, states)
        expected = choose_classes(scores, receiver.readout.class_ids, receiver.decision).tolist()
        expected_events = emit_events(expected, receiver.stabilizer.hold_ticks)
        actual_events = []
        for tick, level in enumerate(stream.levels):
            event = receiver.step(level, tick)
            if receiver.observation["state"] != tuple(states[tick]):
                raise AssertionError(f"Reloaded state differs at tick {tick}")
            if receiver.observation["class_id"] != expected[tick]:
                raise AssertionError(f"Reloaded decision differs at tick {tick}")
            if event:
                actual_events.append({**event, "emit_tick": tick})
        if actual_events != expected_events:
            raise AssertionError(f"Reloaded events differ for {name}")
