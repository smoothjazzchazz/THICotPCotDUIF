"""All label/payload access is confined to offline scoring."""
from bisect import bisect_left
from difflib import SequenceMatcher
import numpy as np
from work.model.stream_reservoir import INVALID, NAMES


def distribution(values):
    return dict(n=len(values), minimum=min(values) if values else None,
                mean=float(np.mean(values)) if values else None,
                maximum=max(values) if values else None)


def byte_errors(expected, actual):
    counts = dict(substitutions=0, deletions=0, insertions=0)
    # Explicit sequence alignment, not a claim of minimum Levenshtein distance.
    for tag, a, b, c, d in SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes():
        if tag == 'replace':
            shared = min(b - a, d - c)
            counts['substitutions'] += shared
            counts['deletions'] += b - a - shared
            counts['insertions'] += d - c - shared
        elif tag == 'delete':
            counts['deletions'] += b - a
        elif tag == 'insert':
            counts['insertions'] += d - c
    counts.update(expected=len(expected), recovered=len(actual),
                  exact=list(expected) == list(actual),
                  alignment='difflib sequence alignment; exactness is direct byte equality')
    return counts


def score_events(expected, actual, allow_early=False):
    ticks = [t for t, _ in expected]
    used, latency, matched = set(), [], {}
    totals = dict(expected=len(expected), emitted=len(actual), correct=0, wrong_class=0,
                  missing=0, false_known=0, false_invalid=0, duplicates=0)
    by_kind = {name: dict(expected=0, correct=0, missed_or_wrong=0) for name in NAMES[1:]}
    for _, kind in expected:
        by_kind[NAMES[kind]]['expected'] += 1
    for event in actual:
        t = event.decision_tick
        start = bisect_left(ticks, t - 2)
        end = bisect_left(ticks, t + (3 if allow_early else 1))
        candidates = [i for i in range(start, end) if i not in used]
        if candidates:
            i = min(candidates, key=lambda j: (expected[j][1] != event.kind, abs(t - ticks[j])))
            used.add(i)
            if expected[i][1] == event.kind:
                totals['correct'] += 1
                by_kind[NAMES[event.kind]]['correct'] += 1
                latency.append(t - ticks[i])
                matched[t] = ticks[i]
            else:
                totals['wrong_class'] += 1
        else:
            duplicate = any(i in used and expected[i][1] == event.kind for i in range(start, end))
            totals['duplicates'] += int(duplicate)
            totals['false_invalid' if event.kind == INVALID else 'false_known'] += 1
    totals['missing'] = len(expected) - len(used)
    for values in by_kind.values():
        values['missed_or_wrong'] = values['expected'] - values['correct']
    totals['errors'] = (totals['wrong_class'] + totals['missing']
                        + totals['false_known'] + totals['false_invalid'])
    return dict(totals=totals, by_kind=by_kind, timing_error=distribution(latency)), matched
