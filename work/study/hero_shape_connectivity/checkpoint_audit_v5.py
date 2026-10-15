"""Audit bounded saved-checkpoint alternatives against expanded development."""
import argparse,json,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .train import key,write_json
from .shapes import make_shape
from .startup_margin_v5 import passed
from .startup_evaluate import evaluate


def audit(job):
    root,label,kw,profile,seed,record=job;root=Path(root);sh=make_shape(**kw);assert digest(record['checkpoint'])==record['checkpoint_sha256']
    a=np.load(record['checkpoint']);sh.leaks=a['leaks'];dl,score=evaluate(sh,a['p'],root,profile,np.array(record['class_weights']));score.update(dev_loss=dl,epoch=0,exposure_ticks=0)
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=label,epochs=0,selected_epoch=0,selected=score,checkpoint=record['checkpoint'],class_weights=record['class_weights'],
        exposure_ticks=0,warm_start=record,development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status='bounded_saved_checkpoint_development_selection_not_confirmation')
    folder=root/'diagnostics'/label/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);write_json(folder/(record['id']+'.json'),result)
    print(json.dumps(dict(profile=profile,seed=seed,id=record['id'],exact=score['exact_messages'],messages=score['valid_messages'],boundary=score['boundary_errors'])),flush=True);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--label',default='checkpoint_audit_dense_v5a');ap.add_argument('--source-label',default='audit_enlarged_dense_v5a');a=ap.parse_args()
    root=ROOT/'runs/connectivity01';label=a.label;file=root/f'{label}_jobs.json';kw=json.loads((ROOT/'readout_dense_candidate.json').read_text())[0];sh=make_shape(**kw)
    if file.exists():jobs=json.loads(file.read_text())
    else:
        jobs=[]
        for source in sorted((root/'models'/a.source_label/sh.name).glob('*/*/block_0000.json')):
            b=json.loads(source.read_text())
            if passed(b['selected']):continue
            profile=b['profile'];seed=b['seed'];seen={digest(b['checkpoint'])}
            for recipe in ('phase_native_v3','phase_native_refine_v3'):
                folder=root/'models'/recipe/sh.name/profile/str(seed);blocks=sorted(folder.glob('block_*.json'))
                if not blocks:continue
                block=json.loads(blocks[-1].read_text());history=folder/'history.jsonl';rows=[json.loads(s) for s in history.read_text().splitlines()];good=[r for r in rows if 'dev_loss'in r and passed(r)]
                if not good:continue
                for row in (good[0],good[-1]):
                    checkpoint=folder/f"epoch_{row['epoch']:04d}.npz";sha=digest(checkpoint)
                    if sha in seen:continue
                    seen.add(sha);record=dict(id=f"{recipe}_{row['epoch']:04d}",checkpoint=str(checkpoint),checkpoint_sha256=sha,source_history=str(history),source_history_sha256=digest(history),
                        source_block=str(blocks[-1]),source_block_sha256=digest(blocks[-1]),class_weights=block['class_weights'],source_epoch=row['epoch'],source_exposure_ticks=row['exposure_ticks'],
                        selection_rule='first and last original-suite-passing checkpoint of each completed native/refine history; candidate list frozen before enlarged scoring')
                    jobs.append((str(root),label,kw,profile,seed,record))
        write_json(file,jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(audit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
    for profile,seed in sorted({(r['profile'],r['seed']) for r in rows}):
        source=root/'models'/a.source_label/sh.name/profile/str(seed)/'block_0000.json';old=json.loads(source.read_text());options=[old]+[r for r in rows if r['profile']==profile and r['seed']==seed];best=max(options,key=lambda r:key(r['selected']))
        result={**best,'recipe':label,'alternatives':[dict(checkpoint=r['checkpoint'],exact=r['selected']['exact_messages'],boundaries=r['selected']['boundary_errors']) for r in options]}
        folder=root/'models'/label/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);path=folder/'block_0000.json'
        if path.exists():assert json.loads(path.read_text())==result,'saved checkpoint selection changed'
        else:write_json(path,result)
