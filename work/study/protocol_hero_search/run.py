"""Reproducible dataset generation, broad search, continuation and freezing."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import numpy as np
from .shapes import VARIANTS,SEEDS,PROFILES,make_shape,features
from .data import corpus,score
from .network import compile_kernel
from .training import write_json,fit

ROOT=Path(__file__).parent


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generate(root):
    root.mkdir(parents=True,exist_ok=False);(root/'data').mkdir();(root/'shapes').mkdir()
    for variant in VARIANTS:
        for n in (32,48,64):
            sh=make_shape(variant,n);write_json(root/'shapes'/f'{sh.name}.json',sh.config())
    for pi,profile in enumerate(PROFILES):
        for si,split in enumerate(('clean','patterns','mixed','dev')):
            seed=(71_000_000 if split=='dev' else 61_000_000)+pi*10_000+si*100
            stream=corpus(profile,seed,ticks=8192,stage=split if split!='dev' else 'mixed')
            stream['x']=features(stream['lines'])[0]
            arrays={k:stream.pop(k) for k in ('lines','labels','x')}
            base=root/'data'/f'{profile}_{split}'
            np.savez_compressed(base.with_suffix('.npz'),**arrays)
            write_json(base.with_suffix('.json'),dict(**stream,seed=seed))
    tracked=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')
    historical=[]
    for folder in ('protocol_reservoir64','protocol_reservoir64_training30','protocol_reservoir32_i2c_training30','protocol_reservoir64_uart6_training30'):
        historical.extend(p for p in (ROOT.parent/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p))
    historical.extend(Path(p) for p in tracked if p and Path(p).is_file() and str(ROOT) not in p)
    write_json(root/'preservation.json',{str(p):digest(p) for p in sorted(set(historical))})
    write_json(root/'config.json',dict(screen_variants=list(VARIANTS),nodes=[32,48,64],seeds=list(SEEDS),
        screen_seeds=list(SEEDS[:3]),profiles=list(PROFILES),regimes=['esn','trained'],screen_epochs=60,
        first_block=30,window=512,lr=.003,train_ticks_minimum=8192,development_ticks_minimum=8192,
        checkpoint_selection=['complete message accuracy','boundary errors','false accepted','false events','loss'],
        qualification=dict(min_messages_per_valid_timing=1000,min_successful_seeds=5,total_seeds=6),
        jitter='bounded independent edge perturbation +/-1 tick',frozen=False))
    snapshot=root/'source_at_launch';snapshot.mkdir()
    for p in ROOT.iterdir():
        if p.is_file():shutil.copy2(p,snapshot/p.name)
    write_json(root/'source_hashes_at_launch.json',{p.name:digest(p) for p in snapshot.iterdir()})


def execute(jobs,workers,root,stage):
    completed=[];failures=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(fit,j):j for j in jobs}
        for f in as_completed(futures):
            try:
                r=f.result();completed.append(r)
                print(json.dumps({k:r[k] for k in ('shape','profile','seed','regime','epochs','status')}),flush=True)
            except Exception as e:
                failures.append(dict(job=list(futures[f]),error=repr(e)))
            write_json(root/f'{stage}_ledger.json',dict(completed=completed,failures=failures,total=len(jobs)))
    if failures:raise RuntimeError(f'{len(failures)} jobs failed; see preserved ledger')


def select(root):
    rows=[json.loads(p.read_text()) for p in (root/'models').rglob('screen_done.json')]
    rankings=[]
    for variant in VARIANTS:
        for n in (32,48,64):
            name=f'{variant}_{n}';subset=[r for r in rows if r['shape']==name]
            profiles={}
            for profile in PROFILES:
                options=[]
                for regime in ('trained','esn'):
                    matches=[r for r in subset if r['profile']==profile and r['regime']==regime]
                    if len(matches)!=3:raise ValueError('incomplete screen')
                    metrics=[r['selected'] for r in matches]
                    options.append(dict(regime=regime,accuracy=float(np.mean([m['message_accuracy'] for m in metrics])),
                        boundary=float(np.mean([m['boundary_f1'] for m in metrics])),
                        false_events=float(np.mean([m['false_events']/m['ticks'] for m in metrics]))))
                profiles[profile]=max(options,key=lambda r:(r['accuracy'],r['boundary'],-r['false_events']))
            rank=(min(p['accuracy'] for p in profiles.values()),min(p['boundary'] for p in profiles.values()),
                  -max(p['false_events'] for p in profiles.values()),-make_shape(variant,n).parameters)
            rankings.append(dict(shape=name,variant=variant,nodes=n,rank=rank,profiles=profiles))
    rankings.sort(key=lambda r:r['rank'],reverse=True)
    write_json(root/'screen_selection.json',dict(ranking=rankings,advanced=rankings[:4],
        rule='worst-profile mean complete-message accuracy, worst boundary F1, worst false-event rate, parameter cost; regimes selected per profile on development only'))
    return rankings[:4]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['generate','screen','select','finalists'])
    ap.add_argument('--output',type=Path,default=ROOT/'runs'/'run01');ap.add_argument('--workers',type=int,default=8)
    args=ap.parse_args();root=args.output
    if args.action=='generate':compile_kernel();generate(root)
    elif args.action=='screen':
        jobs=[(str(root),v,n,p,s,r,'screen') for v in VARIANTS for n in (32,48,64)
              for p in PROFILES for s in SEEDS[:3] for r in ('esn','trained')]
        execute(jobs,args.workers,root,'screen')
    elif args.action=='select':select(root)
    elif args.action=='finalists':
        advanced=json.loads((root/'screen_selection.json').read_text())['advanced']
        jobs=[(str(root),a['variant'],a['nodes'],p,s,a['profiles'][p]['regime'],'finalist')
              for a in advanced for p in PROFILES for s in SEEDS]
        execute(jobs,args.workers,root,'finalists')

if __name__=='__main__':main()
