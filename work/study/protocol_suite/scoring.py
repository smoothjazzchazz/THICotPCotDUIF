"""Event matching is independent of the feature engines and classifier fitting."""
import numpy as np


def in_window(tick, truth):
    return truth["end"]+8 <= tick <= truth["end"]+14


def training_labels(stream, ticks):
    return np.asarray([next((e["class"] for e in stream["events"] if in_window(int(t),e)),7)
                       for t in ticks],dtype=int)


def score(stream, predictions):
    truth = stream["events"]
    used = set()
    tp = fp = unknown_tp = unknown_accept = spurious_unknown = 0
    latency, errors = [], []
    matches = {}
    for i,p in enumerate(predictions):
        valid = [(j,e) for j,e in enumerate(truth) if j not in used and
                 e["class"] == p["class"] and in_window(p["tick"],e)]
        if valid:
            j,e = min(valid,key=lambda z:abs(z[1]["end"]+10-p["tick"]))
            used.add(j)
            matches[j] = i
            if p["class"] != 7:
                tp += 1
                latency.append(p["tick"]-e["end"])
                errors.append(p["stamp"]-e["end"])
            else:
                unknown_tp += 1
        elif p["class"] != 7:
            fp += 1
        else:
            spurious_unknown += 1
    unknown_accept = sum(any(p["class"] != 7 and in_window(p["tick"],e) for p in predictions)
                         for e in truth if e["class"] == 7)
    groups = {}
    for j,e in enumerate(truth):
        groups.setdefault(e["group"],[]).append(j)
    success = total = 0
    group_list = list(groups.values())
    for gi,indices in enumerate(group_list):
        if len(indices) != 4:
            continue
        total += 1
        # Partition the full stream at next-group starts, including idle extras.
        lo = 0 if gi==0 else truth[indices[0]]["start"]
        hi = truth[group_list[gi+1][0]]["start"]-1 if gi+1<len(group_list) else stream["ticks"]-1
        pred_ids = [i for i,p in enumerate(predictions) if lo <= p["tick"] <= hi]
        expected = [matches.get(j,-1) for j in indices]
        success += int(pred_ids == expected and -1 not in expected)
    known = sum(e["class"] != 7 for e in truth)
    return {"tp":tp,"fp":fp,"known":known,"unknown":len(truth)-known,
            "unknown_tp":unknown_tp,"unknown_accept":unknown_accept,
            "spurious_unknown":spurious_unknown,"ticks":stream["ticks"],
            "transactions":total,"transaction_ok":success,"latencies":latency,"timing_errors":errors}


def summarize(rows):
    sums = {k:sum(r[k] for r in rows) for k in
            ("tp","fp","known","unknown","unknown_tp","unknown_accept","spurious_unknown",
             "ticks","transactions","transaction_ok")}
    tp,fp,k = (sums[x] for x in ("tp","fp","known"))
    latency = [x for r in rows for x in r["latencies"]]
    errors = [abs(x) for r in rows for x in r["timing_errors"]]
    return {**sums,"precision":tp/max(1,tp+fp),"recall":tp/max(1,k),
            "f1":2*tp/max(1,k+tp+fp),"unknown_recall":sums["unknown_tp"]/max(1,sums["unknown"]),
            "unknown_acceptance":sums["unknown_accept"]/max(1,sums["unknown"]),
            "false_per_1000":1000*fp/max(1,sums["ticks"]),
            "transaction_success":sums["transaction_ok"]/max(1,sums["transactions"]),
            "latency_median":float(np.median(latency)) if latency else None,
            "latency_p95":float(np.percentile(latency,95)) if latency else None,
            "timestamp_abs_p95":float(np.percentile(errors,95)) if errors else None}


def grouped(streams, predictions):
    rows = [score(s,p) for s,p in zip(streams,predictions)]
    return {"aggregate":summarize(rows),"conditions":{
        c:summarize([r for s,r in zip(streams,rows) if s["condition"]==c])
        for c in dict.fromkeys(s["condition"] for s in streams)},"rows":rows}
