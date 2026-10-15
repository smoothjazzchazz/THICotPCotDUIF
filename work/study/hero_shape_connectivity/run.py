"""Isolated launch, reproducible batches, and non-destructive continuation."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import sys
import platform
import subprocess
import traceback
import numpy as np
import os
from .shapes import make_shape,specification,SEEDS,PROFILES
from .vendor.network import compile_kernel
from .data import generate
from .train import fit,write_json

ROOT=Path(__file__).parent
INITIAL=[dict(code=code,schedule=schedule) for schedule in ('registered','current') for code in ('sss','srr','ssr','srs','rsr')]


def source_files(base=ROOT):
    """Do not descend into hundreds of thousands of historical run artifacts."""
    for directory,folders,names in os.walk(base):
        folders[:]=sorted(n for n in folders if n not in ('runs','__pycache__'))
        for name in sorted(names):
            path=Path(directory)/name
            if path.is_file():yield path


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def launch(root):
    root.mkdir(parents=True,exist_ok=False)
    compile_kernel()
    source=root/'source_at_launch';source.mkdir()
    for p in source_files():
        q=source/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(root/'source_hashes.json',{str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file()})
    write_json(root/'environment.json',dict(python=sys.version,numpy=np.__version__,platform=platform.platform(),
        compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],flags='-O3 -std=c++17; no fast-math',
        baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()))
    old=ROOT.parent/'protocol_hero_search'
    paths=[p for p in old.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    # All old files are hashed once. Later verification can prove they were untouched.
    write_json(root/'historical_sha256.json',{str(p):digest(p) for p in paths})
    (root/'shapes').mkdir()
    for kwargs in INITIAL:
        sh=make_shape(**kwargs);write_json(root/'shapes'/f'{sh.name}.json',specification(sh,kwargs))
    write_json(root/'experiment.json',dict(candidates=INITIAL,seeds=list(SEEDS),profiles=list(PROFILES),
        first_epochs=30,window=512,lr=.003,train_corpora=12,minimum_ticks_each=32768,
        initialization='edge-keyed random weights; per-layer recurrent spectral radius 0.95',
        meaningful='paired >=20pp unresolved exact-message gain >=5/6 seeds; no >2pp regression; or >=15% lower MACs and parameters within1pp every condition and >=95% on claimed conditions; fresh replication',
        qualification='unchanged from ../protocol_hero_search/PLAN.md; >=5/6 seeds all seven profiles; all exact messages/boundaries; no accepted invalid/background; >=1000 messages/valid timing; max1024 bytes'))
    generate(root/'data')


def batch(root,candidates,seeds,profiles,epochs,workers,recipe,label):
    jobs=[(str(root),kwargs,p,s,epochs,recipe) for kwargs in candidates for p in profiles for s in seeds]
    return batch_jobs(root,jobs,workers,label)


def batch_jobs(root,jobs,workers,label):
    manifest=root/f'{label}_jobs.json'
    if manifest.exists():
        if json.loads(manifest.read_text())!=json.loads(json.dumps(jobs)):raise ValueError('batch label already describes different jobs')
    else:write_json(manifest,jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in source_files():
            q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    candidates=list({json.dumps(j[1],sort_keys=True):j[1] for j in jobs}.values())
    for kwargs in candidates:
        sh=make_shape(**kwargs);path=root/'shapes'/f'{sh.name}.json'
        if not path.exists():write_json(path,specification(sh,kwargs))
    results=[];failures=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(fit,j):j for j in jobs}
        for f in as_completed(futures):
            try:
                r=f.result();results.append(r)
                print(json.dumps(dict(shape=r['shape'],profile=r['profile'],seed=r['seed'],epoch=r['epochs'],
                    exact=r['selected']['message_accuracy'],worst=min(c['message_accuracy'] for c in r['selected']['conditions'].values()),
                    boundary=r['selected']['boundary_errors'])),flush=True)
            except Exception:
                failures.append(dict(job=futures[f],traceback=traceback.format_exc()));print(failures[-1],flush=True)
            write_json(root/f'{label}_ledger.json',dict(completed=results,failures=failures,total=len(jobs)))
    if failures:raise RuntimeError(f'{len(failures)} failed jobs retained')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['launch','train','summary'])
    ap.add_argument('--output',type=Path,default=ROOT/'runs'/'connectivity01')
    ap.add_argument('--candidates',type=Path);ap.add_argument('--seeds',default='11,29,47')
    ap.add_argument('--profiles',default=','.join(PROFILES));ap.add_argument('--epochs',type=int,default=30)
    ap.add_argument('--workers',type=int,default=12);ap.add_argument('--recipe',default='matched');ap.add_argument('--label',default='initial30')
    a=ap.parse_args()
    if a.action=='launch':launch(a.output)
    elif a.action=='train':batch(a.output,json.loads(a.candidates.read_text()) if a.candidates else INITIAL,
        list(map(int,a.seeds.split(','))),a.profiles.split(','),a.epochs,a.workers,a.recipe,a.label)
    else:
        rows=json.loads((a.output/f'{a.label}_ledger.json').read_text())['completed']
        for shape in sorted({r['shape'] for r in rows}):
            group=[r for r in rows if r['shape']==shape]
            print(shape,{p:round(float(np.mean([r['selected']['message_accuracy'] for r in group if r['profile']==p])),3) for p in PROFILES if any(r['profile']==p for r in group)})

if __name__=='__main__':main()
