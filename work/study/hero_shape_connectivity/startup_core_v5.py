"""Matched cold-prefix learning with state fixed or trainable; coherent batches."""
import argparse,json,time,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load
from .runtime import run
from .readout_probe import trajectory
from .startup_evaluate import evaluate
from .startup_margin_v5 import audit_training
from .train import write_json,key


def fit(job):
    root,kw,profile,seed,mode,target,*override=job;root=Path(root);sh=make_shape(**kw);recipe=override[0]['recipe'] if override else f'phase_startup_{mode}_v5'
    folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    source=Path(override[0]['source_block']) if override else root/'models'/'final_portfolio_v2a'/sh.name/profile/str(seed)/'block_0000.json'
    if override:assert digest(source)==override[0]['source_block_sha256']
    b=json.loads(source.read_text());a=dict(np.load(b['checkpoint']))
    if override:assert digest(b['checkpoint'])==override[0]['checkpoint_sha256']
    p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights']);offset=sh.parameters-6*sh.n-6;mask=np.ones_like(p);mid=sh.groups[1]
    for k,(src,dst) in enumerate(zip(sh.src,sh.dst)):
        if src in mid and dst in mid:mask[k]=0
    for i in mid[1:]:mask[len(sh.src)+i]=0
    if mode=='readout':mask[:offset]=0
    provenance=dict(source_block=str(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),mode=mode,rounds=target,
        lr=.0003,window=512,updates_per_round=1,optimized_ticks_per_round=180224,
        training='all320 training-startup first512ticks plus32 causal continuous anchors from long365–428',
        development='precision_v2 plus corners_v4 plus startup_v5',state_policy='each complete file starts cold; continuous anchor state recomputed with current weights; all batch gradients use those same weights')
    warm=folder/'warm_start.json'
    if warm.exists():assert json.loads(warm.read_text())==provenance,'source changed'
    else:write_json(warm,provenance)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    m=np.zeros_like(p);v=np.zeros_like(p);step=exposure=last=0
    def save(epoch):
        meta=json.loads(str(a['metadata']));meta.update(epoch=epoch,step=step,exposure=exposure,recipe=recipe,frozen_parameter_indices=np.flatnonzero(mask==0).tolist())
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'m':m,'v':v,'metadata':json.dumps(meta)})
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];m=z['m'];v=z['v'];meta=json.loads(str(z['metadata']));step=meta['step'];exposure=meta['exposure']
    else:
        dl,score=evaluate(sh,p,root,profile,cw);training=audit_training(sh,p,root,profile,cw);write_json(folder/'source_training_audit.json',training)
        row=dict(epoch=0,exposure_ticks=0,dev_loss=dl,training_startup_failed_cases=training['failed_cases'],**score);history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    best=max((r for r in history if 'dev_loss' in r),key=key);started=time.monotonic()
    prefixes=[]
    for path in sorted((root/'data_startup_modes'/profile).glob('*.json')):
        s=load(path.with_suffix(''));assert len(s['x'])>=512;prefixes.append((s['x'][:512],s['labels'][:512]))
    assert len(prefixes)==320
    for iteration in range(last+1,target+1):
        path=root/'data_precision_v2'/profile/'train'/f'long_{364+iteration:04d}';s=load(path);states=trajectory(sh,p,s['x']);rng=np.random.default_rng([seed,iteration,51027])
        starts=rng.integers(max(512,s.get('startup_ambiguous_until',0)),len(states)-511,size=32)
        batch=[(x,y,np.zeros(sh.n)) for x,y in prefixes]
        batch.extend((s['x'][t:t+512],s['labels'][t:t+512],states[t-1]) for t in starts)
        g=np.zeros_like(p);losses=[]
        for x,y,h in batch:
            loss,_,_,gradient,_=run(sh,p,x,y,cw,h,backward=True,readout_only=mode=='readout');g+=gradient/len(batch);losses.append(loss)
        g*=mask;norm=float(np.linalg.norm(g));g/=max(1.,norm);step+=1;m=.9*m+.1*g;v=.999*v+.001*g*g
        p-=.0003*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8);np.clip(p,-7.99,7.99,out=p);exposure+=512*len(batch)
        write_json(folder/f'anchors_{iteration:04d}.json',dict(path=str(path),starts=starts.tolist(),window=512))
        row=dict(epoch=iteration,exposure_ticks=exposure,train_loss=float(np.mean(losses)),gradient_norm=norm,elapsed_call=time.monotonic()-started)
        if iteration%8==0 or iteration==target:
            dl,score=evaluate(sh,p,root,profile,cw);row.update(score);row['dev_loss']=dl
            if key(row)>key(best):best=row.copy()
            print(json.dumps(dict(profile=profile,seed=seed,mode=mode,round=iteration,exact=row['message_accuracy'],boundary=row['boundary_errors'])),flush=True)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
        history.append(row)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint);training=audit_training(sh,z['p'],root,profile,cw);write_json(folder/'selected_training_audit.json',training)
    np.savez_compressed(folder/'selected.npz',p=z['p'],leaks=z['leaks'])
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=target,selected_epoch=best['epoch'],selected=best,
        checkpoint=str(checkpoint),class_weights=cw.tolist(),exposure_ticks=exposure,warm_start=provenance,selected_training_failed_cases=training['failed_cases'],
        development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status='parameter_learning_diagnostic_not_capacity_proof')
    write_json(folder/f'block_{target:04d}.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);ap.add_argument('--rounds',type=int,default=64);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];label=f'startup_core_v5_{a.rounds}'
    jobs=[(str(root),kw,profile,47,mode,a.rounds) for profile in ('uart_n','uart_e') for mode in ('readout','core')];write_json(root/f'{label}_jobs.json',jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
