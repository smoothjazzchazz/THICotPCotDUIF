"""Small deterministic offline prototype fit and declared development screen."""

from copy import deepcopy
from statistics import median

from work.model.decision import DecisionStage

from .models import simulate
from .scoring import observations, passes, score_events


def mse(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def fit(config, training):
    config = deepcopy(config)
    if config["kind"].startswith("stream_"):
        return config, {"method": "loaded waveform definitions; no statistical fit"}
    trace = simulate(training["samples"], config)
    captured = observations(trace, training)
    labels = {case["id"]: case["class_id"] for case in training["cases"]}
    provenance = {}
    for class_id in (0, 1):
        unique = {}
        for point in captured:
            if (labels.get(point["case_id"]) == class_id and point["frame_valid"]
                    and point["frame_run_count"] == config["expected_runs"]):
                unique.setdefault(tuple(point["state"]), point["case_id"])
        vectors = list(unique)
        if not vectors:
            raise ValueError(f"no valid training observations for class {class_id}")
        # Farthest-first coverage keeps real observed states, avoiding a mean
        # waveform which need not correspond to any actual temporal sequence.
        chosen = [vectors[0]]
        while len(chosen) < min(8, len(vectors)):
            remaining = [v for v in vectors if v not in chosen]
            chosen.append(max(remaining, key=lambda v: min(mse(v, c) for c in chosen)))
        config["prototypes"][class_id] = chosen
        provenance[class_id] = [unique[v] for v in chosen]
    return config, {"method": "at most eight farthest-first observed vectors/class",
                    "source_case_ids": provenance, "training_observations": len(captured)}


def classify_observations(points, minimum_score, minimum_margin):
    decision = DecisionStage(minimum_score, minimum_margin)
    return [{"class_id": decision.classify(point["scores"]).class_id,
             "start_tick": point["start_tick"], "decision_tick": point["tick"]}
            for point in points]


def selection_key(result):
    totals = result["totals"]
    known = [row["known_recall"] for row in result["conditions"].values()
             if row["known_recall"] is not None]
    return (totals["false_known_events"] + totals["background_known"],
            totals["duplicates"], totals["wrong_class_events"],
            -min(known, default=0), -totals["correct_known"],
            -totals["explicit_unknown"], totals["missed_observations"])


def calibrate(config, development):
    points = observations(simulate(development["samples"], config), development)
    cases = {case["id"]: case for case in development["cases"]}
    known_scores = sorted(dict(p["scores"])[cases[p["case_id"]]["class_id"]]
                          for p in points if p["case_id"] in cases
                          and cases[p["case_id"]]["class_id"] is not None
                          and cases[p["case_id"]]["class_id"] in dict(p["scores"]))
    if config["kind"] == "stream_intervals":
        thresholds = [0.0, -.5, -1.0, -1.5, -2.0, -3.0]
    elif config["kind"] == "stream_templates":
        thresholds = [0.0, -.125, -.25, -.34, -.5, -.75]
    elif known_scores:
        thresholds = sorted(set(known_scores[round(q * (len(known_scores) - 1))]
                                for q in (0, .1, .25, .5, .75, 1)))
    else:
        thresholds = [0.0]
    margins = [abs(p["scores"][0][1] - p["scores"][1][1])
               for p in points if len(p["scores"]) == 2]
    margin_choices = sorted(set([0.0, median(margins) * .1 if margins else 0.0]))
    trials = []
    for threshold in thresholds:
        for margin in margin_choices:
            result = score_events(classify_observations(points, threshold, margin), development)
            trials.append({"minimum_score": threshold, "minimum_margin": margin,
                           "passes": passes(result), "result": result})
    best = min(trials, key=lambda row: selection_key(row["result"]))
    selected = deepcopy(config)
    selected.update(minimum_score=best["minimum_score"], minimum_margin=best["minimum_margin"])
    return selected, trials, collision_diagnostic(points, cases)


def collision_diagnostic(points, cases):
    known = [p for p in points if p["case_id"] in cases
             and cases[p["case_id"]]["class_id"] is not None]
    unknown = [p for p in points if p["case_id"] in cases
               and cases[p["case_id"]]["class_id"] is None]
    closest = None
    exact = []
    for a in known:
        for b in unknown:
            distance = mse(a["state"], b["state"])
            pair = {"known": a["case_id"], "unknown": b["case_id"],
                    "mean_squared_distance": distance,
                    "same_run_count": a["frame_run_count"] == b["frame_run_count"]}
            if closest is None or distance < closest["mean_squared_distance"]:
                closest = pair
            if a["state"] == b["state"] and pair["same_run_count"]:
                exact.append(pair)
    cross_class = []
    for a in known:
        for b in known:
            if (cases[a["case_id"]]["class_id"] < cases[b["case_id"]]["class_id"]
                    and a["state"] == b["state"]):
                cross_class.append({"left": a["case_id"], "right": b["case_id"]})
    return {"closest_known_unknown": closest, "exact_same_count_collisions": exact,
            "exact_cross_class_collisions": cross_class,
            "note": "numeric memory only; template recognizer bypasses this state and has its own run-error state"}
