"""Off-chip fitting and a fixed threshold selection recipe."""
import numpy as np
from .models import Features
from .scoring import training_labels, grouped

RIDGES = (.001, .03, .3)
FLOORS = (.25, .45, .65)
MARGINS = (0., .12, .25)


def decisions(records, readout, scalar=False):
    result = []
    for r in records:
        x = r["x"]
        if readout["type"] == "template":
            prototypes = np.asarray(readout["prototypes"],np.int64)
            y = np.asarray(readout["labels"])
            dist = np.abs(x[:,None,:]//4-prototypes[None,:,:]).sum(axis=2)
            scores = np.column_stack([-dist[:,y==c].min(axis=1) for c in (0,1)])
            best = np.argmax(scores,axis=1)
            top = scores[np.arange(len(x)),best]
            margin = np.abs(scores[:,0]-scores[:,1])
            pred = np.where((top >= -readout["distance"]) & (margin >= readout["margin"]),best,7)
        else:
            integer = "bits" in readout
            w = np.asarray(readout["weights"], np.int64 if integer else float)
            bias = np.asarray(readout["bias"], np.int64 if integer else float)
            if scalar:
                cast = int if integer else float
                scores = np.asarray([[cast(bias[j])+sum(int(a)*cast(wi[j]) for a,wi in zip(row,w))
                                      for j in range(3)] for row in x]).reshape(-1,3)
            else:
                scores = x @ w + bias
            best = np.argmax(scores,axis=1)
            ordered = np.sort(scores,axis=1)
            accept = (ordered[:,-1] >= readout["floor"]) & (ordered[:,-1]-ordered[:,-2] >= readout["margin"])
            pred = np.where(accept & (best<2),best,7)
        if "support_bounds" in readout:
            bounds = readout["support_bounds"]
            z = r["support"]
            ok = ((z[:,0]>=bounds[0]) & (z[:,0]<=bounds[1]) &
                  (z[:,1]>=bounds[2]) & (z[:,2]<=bounds[3]))
            pred = np.where(ok,pred,7)
        result.append([{"class":int(c),"tick":int(t),"stamp":int(s)}
                       for c,t,s in zip(pred,r["ticks"],r["stamps"])])
    return result


def fit(streams, records, ridge, unit):
    x = np.concatenate([r["x"] for r in records]).astype(float)/unit
    y = np.concatenate([training_labels(s,r["ticks"]) for s,r in zip(streams,records)])
    x = np.column_stack([x,np.ones(len(x))])
    target = np.column_stack([y==c for c in (0,1,7)]).astype(float)
    # Each class contributes equal loss, regardless of extra glitch gates.
    sample_weight = np.asarray([1/max(1,np.count_nonzero(y==c)) for c in y])
    a = x*np.sqrt(sample_weight[:,None])
    b = target*np.sqrt(sample_weight[:,None])
    # Dual/primal equivalence avoids needlessly solving a huge feature matrix.
    if a.shape[1] > a.shape[0]:
        gram = a@a.T
        gram.flat[::len(gram)+1] += ridge
        w = a.T @ np.linalg.solve(gram,b)
    else:
        gram = a.T@a
        gram.flat[::len(gram)+1] += ridge
        w = np.linalg.solve(gram,a.T@b)
    return {"type":"ridge","weights":(w[:-1]/unit).tolist(),"bias":w[-1].tolist(),"ridge":ridge}


def selection_key(m):
    return (min(1.,m["precision"]/.85,m["recall"]/.85,m["unknown_recall"]/.8),
            m["f1"],m["unknown_recall"],-m["false_per_1000"])


def select(train, tr, dev, dr, config):
    best = best_key = None
    trials = []
    if config.get("template"):
        matrices, labels = [], []
        for s,r in zip(train,tr):
            if s["condition"] != "clean":
                continue
            y = training_labels(s,r["ticks"])
            matrices.extend(r["x"][y!=7]//4)
            labels.extend(y[y!=7])
        x,y = np.asarray(matrices),np.asarray(labels)
        protos,classes = [],[]
        for c in (0,1):
            options = np.unique(x[y==c],axis=0)
            # Deterministic farthest-first coverage; no test data involved.
            chosen = [0]
            while len(chosen) < min(len(options),config["template"]//2):
                d = np.abs(options[:,None,:]-options[chosen][None,:,:]).sum(axis=2).min(axis=1)
                d[chosen] = -1
                chosen.append(int(d.argmax()))
            protos.extend(options[chosen].tolist())
            classes.extend([c]*len(chosen))
        candidates = [{"type":"template","prototypes":protos,"labels":classes,"distance":d,"margin":m}
                      for d in (0,4,8,12,20,32,48,64,96) for m in (0,2,4,8)]
    else:
        candidates = []
        for ridge in RIDGES:
            base = fit(train,tr,ridge,Features(config).unit)
            candidates.extend([{**base,"floor":f,"margin":m} for f in FLOORS for m in MARGINS])
    if config.get("guard"):
        z = np.concatenate([r["support"][training_labels(s,r["ticks"])!=7]
                            for s,r in zip(train,tr) if s["condition"] in ("clean","jitter")])
        bounds = [int(z[:,0].min()),int(z[:,0].max()),int(z[:,1].min()),int(z[:,2].max())]
        slack = config.get("guard_slack",0)
        bounds[2],bounds[3] = max(1,bounds[2]-slack),min(31,bounds[3]+slack)
        if not config.get("guard_count",True):
            bounds[0],bounds[1] = 0,255
        candidates = [{**r,"support_bounds":bounds} for r in candidates]
    for r in candidates:
        m = grouped(dev,decisions(dr,r))["aggregate"]
        key = selection_key(m)
        trials.append({k:r[k] for k in ("ridge","floor","margin","distance") if k in r} |
                      {"f1":m["f1"],"unknown_recall":m["unknown_recall"],"key":key})
        if best_key is None or key > best_key:
            best,best_key = r,key
    return best,trials


def quantize(readout,bits,wide_bias=False):
    if readout["type"] == "template":
        return dict(readout)
    w,b = np.asarray(readout["weights"]),np.asarray(readout["bias"])
    maxval = np.max(np.abs(w)) if wide_bias else max(np.max(np.abs(w)),np.max(np.abs(b)))
    scale = 2.**np.floor(np.log2((2**(bits-1)-1)/maxval))
    qb = np.rint(b*scale).astype(int)
    bias_bits = max(2,1+int(np.ceil(np.log2(int(np.max(np.abs(qb)))+1)))) if wide_bias else bits
    return {**readout,"weights":np.rint(w*scale).astype(int).tolist(),
            "bias":np.rint(b*scale).astype(int).tolist(),
            "floor":int(np.ceil(readout["floor"]*scale)),"margin":int(np.ceil(readout["margin"]*scale)),
            "bits":bits,"bias_bits":bias_bits,"wide_bias":wide_bias,"scale":scale}
