"""Score only after inference; report each condition, including missed events."""


def score_trace(trace, expected, stable_ticks, delay_ticks):
    events = [row["event"] for row in trace if row["event"] is not None]
    results = []
    assigned = set()
    false_known = 0
    for pulse in expected:
        # Here the synthetic low gaps exceed the filter length. A surviving pulse
        # has both edges delayed equally; this is not a universal filter model.
        offset = delay_ticks + stable_ticks - 1
        completion_tick = pulse.start_tick + pulse.width + offset
        matches = [event for event in events if event.decision_tick == completion_tick]
        assigned.update(event.decision_tick for event in matches)
        event = matches[0] if matches else None
        suppressed = pulse.width < stable_ticks
        if suppressed:
            correct = not matches
        else:
            correct = len(matches) == 1 and event.class_id == pulse.class_id
        if pulse.class_id is None:
            false_known += sum(event.class_id is not None for event in matches)
        results.append({
            "condition": pulse.name,
            "expected_class": pulse.class_id,
            "observed": "no event" if event is None else (
                "unknown" if event.class_id is None else event.class_id),
            "filtered_out": suppressed,
            "correct": correct,
            "raw_start_tick": pulse.start_tick,
            "event_start_tick": None if event is None else event.start_tick,
            "decision_tick": None if event is None else event.decision_tick,
            "raw_start_to_decision": None if event is None else (
                event.decision_tick - pulse.start_tick),
        })
    extra_events = [event for event in events if event.decision_tick not in assigned]
    false_known += sum(event.class_id is not None for event in extra_events)
    return {"conditions": results, "false_known_events_on_unfamiliar_or_background": false_known,
            "extra_events": len(extra_events),
            "all_expected": all(row["correct"] for row in results) and not extra_events}
