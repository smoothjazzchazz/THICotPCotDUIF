"""Freeze -> adapt -> fresh confirmation. All artifacts stay below this suite."""
import argparse
from datetime import datetime,timezone
import hashlib
import time
import numpy as np
from .run import ROOT,save,read,hashes,reserve
from .signals import TASKS,CONDITIONS,dataset,training,encode
from .models import collect
from .learning import select,quantize,decisions,RIDGES,FLOORS,MARGINS
from .resources import count
from .scoring import grouped


def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    selection = read(ROOT/"configs/selection.json")
    # This is the architecture/recipe freeze. It precedes ANY transfer adaptation.
    out = reserve("frozen")
    save(out/"recipe.json",{"utc":datetime.now(timezone.utc).isoformat(),"selection":selection,
            "ridges":RIDGES,"floors":FLOORS,"margins":MARGINS,
            "training_namespace":31000000,"calibration_namespace":32000000,
            "test_namespace":91000000,"splice_namespace":95000000,
            "training_bursts":144,"calibration_bursts":72,"test_bursts":48,
            "training_replicates":3,"topology_seeds":[11,29,47],"test_blocks":8,
            "sources":hashes(),"primary_tasks":TASKS,"transfer_task":"transfer",
            "confirmation_conditions":CONDITIONS,
            "primary_endpoint":"minimum core-task F1 with unknown recall >=.80; report every condition",
            "primary_comparison":"binary_duration vs raw_duration; paired seed/fit bootstrap",
            "extra_unknown_probe":"prefix splices; reported separately, no tuning",
            "note":"Generator-only transfer gate fixtures were unit-tested at seed 421; no classifier was fitted or evaluated on transfer before this freeze."})
    for ti,task in enumerate((*TASKS,"transfer")):
        for rep,toposeed in enumerate((11,29,47)):
            train = training(task,31000000+ti*100000+rep*10000)
            dev = dataset(task,32000000+ti*100000+rep*10000,1,72)
            save(out/f"data_{task}_{rep}.json.gz",{"train":train,"calibration":dev})
            for selected in selection:
                cfg = {**selected["config"],"seed":toposeed}
                tr,dr = collect(train,cfg),collect(dev,cfg)
                fitted,trials = select(train,tr,dev,dr,cfg)
                arithmetic = selected["arithmetic"]
                if arithmetic == "integer":
                    final = fitted
                else:
                    final = quantize(fitted,int(arithmetic[1:].rstrip('w')),arithmetic.endswith('w'))
                key = f"{selected['id']}_{task}_{rep}"
                save(out/f"{key}.json",{"id":selected["id"],"task":task,"replicate":rep,"config":cfg,
                     "readout":final,"float_readout":fitted,"resources":count(cfg,final),"adaptation_trials":trials,
                     "calibration":grouped(dev,decisions(dr,final))})
                print("adapted",key,flush=True)
    # Final learned parameter freeze precedes generation of all test data.
    save(out/"lock.json",{"utc":datetime.now(timezone.utc).isoformat(),"sources":hashes(),
         "files":{p.name:filehash(p) for p in out.iterdir() if p.is_file()}})


def check_lock():
    lock = read(ROOT/"artifacts/frozen/lock.json")
    for name,h in lock["files"].items():
        assert filehash(ROOT/"artifacts/frozen"/name)==h,name
    for name,h in lock["sources"].items():
        assert filehash(ROOT/name)==h,name
    return lock


def splices(task,seed,bursts=24):
    rng = np.random.default_rng(seed)
    samples = [0]*20
    events=[]
    for i in range(bursts):
        cls = int(rng.integers(2))
        start = len(samples)
        # A complete known-looking suffix with extra preceding in-burst activity.
        prefix = [(1,3),(0,3)] if task not in ("clockdata","transfer") else [(3,3),(2,3),(1,3),(0,3)]
        for v,n in prefix+encode(task,cls,rng):
            samples.extend([v]*n)
        end=len(samples)
        events.append({"class":7,"start":start,"end":end,"group":i//4})
        samples.extend([0]*int(rng.integers(14,29)))
    return {"task":task,"seed":seed,"condition":"splice","samples":samples,"events":events,"crop":0,"ticks":len(samples)}


def evaluate():
    check_lock()
    selection = read(ROOT/"artifacts/frozen/recipe.json")["selection"]
    out = reserve("confirmation")
    save(out/"start.json",{"utc":datetime.now(timezone.utc).isoformat(),"lock_sha256":filehash(ROOT/"artifacts/frozen/lock.json")})
    results=[]
    for ti,task in enumerate((*TASKS,"transfer")):
        streams=[]
        for block in range(8):
            for s in dataset(task,91000000+ti*100000+block*10000,1,48):
                s["block"]=block
                streams.append(s)
        extra=[]
        for block in range(8):
            s=splices(task,95000000+ti*100000+block*10000)
            s["block"]=block
            extra.append(s)
        save(out/f"{task}_streams.json.gz",streams)
        save(out/f"{task}_splices.json.gz",extra)
        for selected in selection:
            for rep in range(3):
                key=f"{selected['id']}_{task}_{rep}"
                model=read(ROOT/"artifacts/frozen"/f"{key}.json")
                records=collect(streams,model["config"])
                predictions=decisions(records,model["readout"])
                metrics=grouped(streams,predictions)
                extra_pred=decisions(collect(extra,model["config"]),model["readout"])
                row={"id":selected["id"],"task":task,"replicate":rep,"metrics":metrics,
                     "splice_metrics":grouped(extra,extra_pred),"resources":model["resources"],
                     "block_conditions":[[s["block"],s["condition"]] for s in streams]}
                if selected["id"] in ("binary_duration","binary_strict","raw_duration"):
                    row["float_metrics"]=grouped(streams,decisions(records,model["float_readout"]))
                results.append(row)
                save(out/f"{key}_predictions.json.gz",{"normal":predictions,"splice":extra_pred})
                save(out/f"{key}_metrics.json",row)
                m=metrics["aggregate"]
                print("confirmed",key,"F1",round(m["f1"],3),"unknown",round(m["unknown_recall"],3),flush=True)
                save(out/"summary.json",results)
    save(out/"completed.json",{"utc":datetime.now(timezone.utc).isoformat(),"source_sha256":hashes(),
                               "model_count":len(results),"lock_verified":True})


def main():
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=["freeze","evaluate"])
    a=p.parse_args()
    (freeze if a.stage=="freeze" else evaluate)()


if __name__=="__main__":
    main()
