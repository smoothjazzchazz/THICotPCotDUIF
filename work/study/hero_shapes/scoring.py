"""Offline event accounting. Annotations never enter an online model stage."""

from collections import defaultdict
from statistics import mean


WINDOW_AFTER_END = 22


def owner(tick, cases):
    eligible = [case for case in cases
                if case["start_tick"] <= tick <= case["end_tick"] + WINDOW_AFTER_END]
    # Back-to-back observable frames can overlap at the next raw onset. Prefer
    # the completed frame, not the next frame which has barely begun.
    completed = [case for case in eligible if tick >= case["end_tick"]]
    pool = completed or eligible
    return min(pool, key=lambda c: abs(tick - c["end_tick"])) if pool else None


def observations(trace, stream):
    found = []
    for row in trace:
        obs = row["receiver_state"]
        if obs.readout is None:
            continue
        case = owner(row["tick"], stream["cases"])
        found.append({"tick": row["tick"], "start_tick": obs.readout.start_tick,
                      "case_id": None if case is None else case["id"],
                      "scores": list(obs.readout.scores), "state": list(obs.memory),
                      "frame_valid": obs.temporal.frame_valid,
                      "frame_run_count": obs.temporal.frame_run_count})
    return found


def distribution(values):
    return {"n": len(values), "min": min(values) if values else None,
            "mean": mean(values) if values else None,
            "max": max(values) if values else None}


def score_events(events, stream, expected_shift=2, expected_post_end=21):
    grouped = defaultdict(list)
    background = []
    for event in events:
        case = owner(event["decision_tick"], stream["cases"])
        (background if case is None else grouped[case["id"]]).append(event)
    conditions = {}
    details = []
    latency = []
    for case in stream["cases"]:
        condition = case["condition"]
        counts = conditions.setdefault(condition, dict(
            cases=0, known_cases=0, unknown_cases=0, correct_known=0,
            wrong_class_events=0, rejected_known=0, missed_observations=0,
            explicit_unknown=0, false_known_events=0, duplicates=0,
            early_or_late_known=0, timestamp_errors=0, decision_timing_errors=0,
            exact_cases=0))
        counts["cases"] += 1
        is_known = case["class_id"] is not None
        counts["known_cases" if is_known else "unknown_cases"] += 1
        emitted = grouped[case["id"]]
        counts["duplicates"] += max(0, len(emitted) - 1)
        counts["missed_observations"] += not emitted
        correct = [e for e in emitted if e["class_id"] == case["class_id"]
                   and case["end_tick"] <= e["decision_tick"] <= case["end_tick"] + WINDOW_AFTER_END]
        if is_known:
            counts["correct_known"] += bool(correct)
            counts["rejected_known"] += any(e["class_id"] is None for e in emitted)
            counts["wrong_class_events"] += sum(e["class_id"] not in (None, case["class_id"]) for e in emitted)
            counts["early_or_late_known"] += sum(e["class_id"] is not None and e not in correct
                                                   and e["class_id"] == case["class_id"] for e in emitted)
            if correct:
                event = correct[0]
                counts["timestamp_errors"] += event["start_tick"] != case["start_tick"] + expected_shift
                counts["decision_timing_errors"] += event["decision_tick"] != case["end_tick"] + expected_post_end
                latency.append({"case_id": case["id"],
                                "from_start": event["decision_tick"] - case["start_tick"],
                                "from_end": event["decision_tick"] - case["end_tick"],
                                "timestamp_shift": event["start_tick"] - case["start_tick"]})
        else:
            counts["explicit_unknown"] += bool(correct)
            counts["false_known_events"] += sum(e["class_id"] is not None for e in emitted)
        exact = len(emitted) == 1 and bool(correct)
        counts["exact_cases"] += exact
        details.append({"case_id": case["id"], "condition": condition,
                        "expected": case["class_id"], "exact": exact, "events": emitted})
    for counts in conditions.values():
        counts["known_recall"] = (counts["correct_known"] / counts["known_cases"]
                                  if counts["known_cases"] else None)
        counts["unknown_rejection"] = (counts["explicit_unknown"] / counts["unknown_cases"]
                                       if counts["unknown_cases"] else None)
    totals = {key: sum(c[key] for c in conditions.values())
              for key in next(iter(conditions.values()), {})
              if key not in ("known_recall", "unknown_rejection")}
    totals.update(background_known=sum(e["class_id"] is not None for e in background),
                  background_unknown=sum(e["class_id"] is None for e in background),
                  background_samples=sum(owner(t, stream["cases"]) is None
                                         for t in range(len(stream["samples"]))))
    return {"conditions": conditions, "totals": totals, "details": details,
            "background_events": background,
            "latency": {key: distribution([item[key] for item in latency])
                        for key in ("from_start", "from_end", "timestamp_shift")}}


def response_check(trace, config):
    expected = [None] * len(trace)
    next_free = 0
    starts = []
    requests = []
    mismatched_requests = []
    for row in trace:
        event = row["event"]
        mapping = {int(k): v for k, v in config["mapping"].items()}
        symbol = mapping.get(event.class_id) if event is not None else None
        request = row["request"]
        if (request.symbol_id if request is not None else None) != symbol:
            mismatched_requests.append(row["tick"])
        elif request is not None and request.requested_tick != row["tick"]:
            mismatched_requests.append(row["tick"])
        if symbol is None:
            continue
        levels = config["responses"].get(symbol, config["responses"].get(str(symbol)))
        start = max(row["tick"] + 1, next_free)
        next_free = start + len(levels)
        starts.append(start - row["tick"])
        requests.append({"decision_tick": row["tick"], "symbol": symbol,
                         "start_tick": start, "end_tick": next_free})
        for offset, level in enumerate(levels):
            if start + offset < len(expected):
                expected[start + offset] = level
    mismatch = [row["tick"] for row, level in zip(trace, expected) if row["output_level"] != level]
    return {"requests": requests, "waveform_mismatch_ticks": mismatch,
            "request_mismatch_ticks": mismatched_requests,
            "decision_to_response": distribution(starts),
            "pending_tail_samples": max(0, next_free - len(trace))}


def score_trace(trace, stream, config):
    events = [{"class_id": row["event"].class_id,
               "start_tick": row["event"].start_tick,
               "decision_tick": row["event"].decision_tick}
              for row in trace if row["event"] is not None]
    shift = config["delay_ticks"] + config["stable_ticks"] - 1
    result = score_events(events, stream, shift, shift + config["idle_ticks"] - 1)
    result["responses"] = response_check(trace, config)
    return result


def passes(result):
    totals = result["totals"]
    if any(totals[k] for k in ("false_known_events", "background_known", "duplicates",
                               "wrong_class_events", "early_or_late_known",
                               "timestamp_errors", "decision_timing_errors")):
        return False
    for row in result["conditions"].values():
        if row["known_recall"] is not None and row["known_recall"] < .95:
            return False
        if row["unknown_rejection"] is not None and row["unknown_rejection"] < .95:
            return False
    responses = result.get("responses", {})
    return not any(responses.get(k) for k in ("waveform_mismatch_ticks", "request_mismatch_ticks", "pending_tail_samples"))
