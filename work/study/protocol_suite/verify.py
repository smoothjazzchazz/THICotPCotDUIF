"""Post-freeze verification only; cannot fit weights or change configurations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import numpy as np
from .run import ROOT,read,save
from .confirmation import check_lock
from .models import collect
from .learning import decisions
from .scoring import grouped
from .receiver import Receiver


def nominal_reference(task,x):
    """Independent, non-streaming label audit; never used as receiver features."""
    if task == "pulse":
        runs=[]
        for u in x:
            if runs and runs[-1][0]==u:
                runs[-1][1]+=1
            else:
                runs.append([u,1])
        return {(3,8):0,(8,3):1}.get(tuple(n for v,n in runs if v),7)
    if task == "biphase":
        bits=''.join(str(x[6+6*i+4]) for i in range(6))
        return {"001101":0,"110001":1}.get(bits,7)
    if task == "clockdata":
        bits=''.join(str(x[6+6*i+4]>>1) for i in range(6))
        return {"001101":0,"110001":1}.get(bits,7)
    if task == "context":
        lengths=[]
        high=0
        for u in [*x,0]:
            if u:
                high+=1
            elif high:
                lengths.append(high)
                high=0
        if len(lengths)!=8 or lengths[-2:]!=[3,6] or any(v not in (3,6) for v in lengths):
            return 7
        return int(lengths[0]!=lengths[5])
    if task == "transfer":
        levels=[x[3*i+1]&1 for i in range(9)]
        bits=''.join(str(a^b) for a,b in zip(levels,levels[1:]))
        return {"10110010":0,"01101010":1}.get(bits,7)
    raise ValueError(task)


def replay():
    check_lock()
    out=ROOT/"artifacts/verification"
    out.mkdir(exist_ok=True)
    summary=read(ROOT/"artifacts/confirmation/summary.json")
    assert len(summary)==120
    cache={}
    audited=0
    for task in dict.fromkeys(r["task"] for r in summary):
        streams=read(ROOT/"artifacts/confirmation"/f"{task}_streams.json.gz")
        extra=read(ROOT/"artifacts/confirmation"/f"{task}_splices.json.gz")
        cache[task]=(streams,extra)
        assert max(len(s["samples"]) for s in streams+extra)<65536
        for s in streams:
            if s["condition"]=="clean":
                for e in s["events"]:
                    cls=nominal_reference(task,s["samples"][e["start"]:e["end"]])
                    assert cls==e["class"],(task,e,cls)
                    audited+=1
    rows=[]
    for row in summary:
        key=f"{row['id']}_{row['task']}_{row['replicate']}"
        cfg=read(ROOT/"artifacts/frozen"/f"{key}.json")
        saved=read(ROOT/"artifacts/confirmation"/f"{key}_predictions.json.gz")
        streams,extra=cache[row["task"]]
        records=collect(streams,cfg["config"])
        predictions=decisions(records,cfg["readout"])
        assert predictions==saved["normal"],key
        assert grouped(streams,predictions)==row["metrics"],key
        extra_pred=decisions(collect(extra,cfg["config"]),cfg["readout"])
        assert extra_pred==saved["splice"],key
        scalar=stateful=bounds_checked=0
        r=cfg["readout"]
        if r["type"]!="template":
            w,b=np.asarray(r["weights"],np.int64),np.asarray(r["bias"],np.int64)
            assert np.max(np.abs(w))<2**(r["bits"]-1)
            assert np.max(np.abs(b))<2**(r.get("bias_bits",r["bits"])-1)
            bound=cfg["resources"]["score_abs_bound"]
            acc=cfg["resources"]["accumulator_bits"]
            assert bound<2**(acc-1)
            for rec in records:
                assert np.max(np.abs(rec["x"]@w+b),initial=0)<=bound
                bounds_checked+=len(rec["ticks"])
        if row["id"] in ("binary_duration","binary_strict","raw_duration"):
            assert decisions(records,cfg["readout"],scalar=True)==predictions,key
            scalar=sum(len(p) for p in predictions)
            for s,expected in zip(streams,predictions):
                if s["block"]!=0:
                    continue
                receiver=Receiver(cfg["config"],cfg["readout"])
                actual=[]
                for t,u in enumerate(s["samples"]):
                    if t in (1,19,len(s["samples"])//2):
                        receiver=Receiver.restore(json.loads(json.dumps(receiver.snapshot())))
                    p=receiver.step(u)
                    if p is not None:
                        actual.append(p)
                assert actual==expected,(key,s["condition"])
                stateful+=1
        rows.append({"model":key,"streams_replayed":len(streams)+len(extra),"scalar_gates":scalar,
                     "stateful_checkpoint_streams":stateful,"integer_bound_gates":bounds_checked})
        print("verified",key,flush=True)
        save(out/"replay.json",{"independent_nominal_labels":audited,"models":rows,
             "passed":len(rows)==len(summary),"frozen_source_hashes_unchanged":True})


def boundary():
    repo=ROOT.parents[2]
    before=read(ROOT/"artifacts/boundary_before.json")
    after={}
    for base,dirs,names in os.walk(repo):
        dirs[:]=[d for d in dirs if Path(base,d)!=ROOT]
        for name in names:
            p=Path(base,name)
            if p.is_symlink():
                after[str(p.relative_to(repo))]={"link":os.readlink(p)}
            elif p.is_file():
                after[str(p.relative_to(repo))]=hashlib.sha256(p.read_bytes()).hexdigest()
    old=before["files"]
    changed=[p for p in old.keys()&after.keys() if old[p]!=after[p]]
    added=sorted(after.keys()-old.keys())
    deleted=sorted(old.keys()-after.keys())
    result={"outside_files_compared":len(old),"changed":sorted(changed),"added":added,"deleted":deleted,
            "head":subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            "status":subprocess.check_output(['git','status','--short'],text=True),
            "passed":not changed and not added and not deleted}
    save(ROOT/"artifacts/verification/boundary.json",result)
    print(json.dumps(result,indent=2))
    assert result["passed"] and result["head"]==before["head"]


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=["replay","boundary"])
    args=p.parse_args()
    (replay if args.stage=="replay" else boundary)()
