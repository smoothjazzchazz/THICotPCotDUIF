"""Suite-local CLI. Run via run.sh so caches, temporary files and bytecode stay local."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import time
import numpy as np
from .signals import TASKS, CONDITIONS, dataset, training
from .models import collect, configurations
from .learning import select, decisions, quantize
from .scoring import grouped
from .resources import count

ROOT = Path(__file__).resolve().parent


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    text = json.dumps(data,indent=2,allow_nan=False)+"\n"
    if path.suffix == ".gz":
        with gzip.open(path,"wt") as f:
            f.write(text)
    else:
        path.write_text(text)


def read(path):
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path,"rt") as f:
            return json.load(f)
    return json.loads(path.read_text())


def hashes():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [*ROOT.glob("*.py"),ROOT/"PLAN.md",ROOT/"run.sh"]}


def reserve(name):
    out = ROOT/"artifacts"/name
    out.mkdir(exist_ok=False)
    save(out/"manifest.json",{"utc":datetime.now(timezone.utc).isoformat(),"source_sha256":hashes(),
                             "python":platform.python_version(),"numpy":np.__version__,
                             "threads":os.environ.get("OPENBLAS_NUM_THREADS"),"purpose":name})
    return out


def screen(name="screen", extra=None, seeds=(11,)):
    out = reserve(name)
    configs = configurations() if extra is None else extra
    allrows = []
    for task_index,task in enumerate(TASKS):
        train = training(task,1010000+task_index*10000)
        dev = dataset(task,2020000+task_index*10000,1,72)
        save(out/f"{task}_data.json.gz",{"train":train,"dev":dev})
        for base in configs:
            for seed in seeds if base["kind"] in ("recurrent","boolean") else (11,):
                config = {**base,"seed":seed}
                start = time.monotonic()
                tr,dr = collect(train,config),collect(dev,config)
                fitted,trials = select(train,tr,dev,dr,config)
                variants = [("integer",fitted)] if config.get("template") else [
                    ("float",fitted),("q8",quantize(fitted,8)),("q12",quantize(fitted,12))]
                if config.get("wide_bias") and not config.get("template"):
                    variants.extend([(f"q{bits}w",quantize(fitted,bits,True)) for bits in (6,8)])
                key = f"{task}_{config['name']}_s{seed}"
                save(out/f"{key}_fit.json",{"config":config,"readout":fitted,"trials":trials})
                for arithmetic,readout in variants:
                    metrics = grouped(dev,decisions(dr,readout))
                    row = {"task":task,"name":base["name"],"seed":seed,"arithmetic":arithmetic,
                           "config":config,"metrics":metrics,"resources":count(config,readout),
                           "seconds":time.monotonic()-start}
                    save(out/f"{key}_{arithmetic}.json",{"config":config,"readout":readout,**row})
                    allrows.append(row)
                m = allrows[-1]["metrics"]["aggregate"]
                print(task,base["name"],seed,"F1",round(m["f1"],3),"unknown",round(m["unknown_recall"],3),flush=True)
                save(out/"summary.json",allrows)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("stage",choices=["screen","refine"])
    p.add_argument("--name")
    p.add_argument("--config",type=Path)
    p.add_argument("--seeds",default="11")
    args = p.parse_args()
    screen(args.name or args.stage,read(args.config) if args.config else None,tuple(map(int,args.seeds.split(","))))


if __name__ == "__main__":
    main()
