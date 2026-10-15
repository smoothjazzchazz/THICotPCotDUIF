"""Freeze completed native candidates' selection, then audit enlarged development."""
import argparse,json,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .startup_evaluate import evaluate
from .train import key,write_json


def audit(job):
    root,label,kw,profile,seed,record=job;root=Path(root);sh=make_shape(**kw)
    assert digest(record['block'])==record['block_sha256'];b=json.loads(Path(record['block']).read_text());assert digest(b['checkpoint'])==record['checkpoint_sha256']
    a=np.load(b['checkpoint']);sh.leaks=a['leaks'];dl,score=evaluate(sh,a['p'],root,profile,np.array(b['class_weights']));score.update(epoch=0,dev_loss=dl,exposure_ticks=0)
    folder=root/'models'/label/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=label,epochs=0,selected_epoch=0,selected=score,
        checkpoint=b['checkpoint'],class_weights=b['class_weights'],exposure_ticks=0,source_training_exposure_ticks=b['exposure_ticks'],warm_start=record,
        development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status='enlarged_development_audit_no_training_not_confirmation')
    path=folder/'block_0000.json'
    if path.exists():assert json.loads(path.read_text())==result,'audit selection changed; choose a new label'
    else:write_json(path,result)
    print(json.dumps(dict(shape=sh.name,profile=profile,seed=seed,exact=score['exact_messages'],messages=score['valid_messages'],boundary=score['boundary_errors'])),flush=True);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,required=True);ap.add_argument('--label',required=True);ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--profiles',default='uart_n,uart_e');ap.add_argument('--seeds',default=','.join(map(str,SEEDS)));a=ap.parse_args()
    root=ROOT/'runs/connectivity01';file=root/f'{a.label}_jobs.json'
    if file.exists():jobs=json.loads(file.read_text())
    else:
        jobs=[];pending=[]
        for kw in json.loads(a.candidates.read_text()):
            sh=make_shape(**kw)
            for profile in a.profiles.split(','):
                for seed in map(int,a.seeds.split(',')):
                    options=[]
                    for recipe in ('phase_native_v3','phase_native_refine_v3'):
                        for path in (root/'models'/recipe/sh.name/profile/str(seed)).glob('block_*.json'):options.append((path,json.loads(path.read_text())))
                    if not options:pending.append(dict(shape=sh.name,profile=profile,seed=seed));continue
                    path,b=max(options,key=lambda v:key(v[1]['selected']));record=dict(block=str(path),block_sha256=digest(path),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
                        policy='same-seed/profile completed native blocks selected on original precision_v2 development before enlarged audit; no parameter updates')
                    jobs.append((str(root),a.label,kw,profile,seed,record))
        write_json(file,jobs);write_json(root/f'{a.label}_pending.json',pending)
    snapshot=root/'batch_sources'/a.label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{a.label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(audit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{a.label}_ledger.json',dict(completed=rows,total=len(jobs)))
