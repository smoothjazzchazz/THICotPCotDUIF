"""Independent training-case mining with causal model-state windows and easy anchors."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
from pathlib import Path
import shutil
import time
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,features,SEEDS
from .vendor.data import Builder
from .precision_data_v2 import prefix,finish
from .data import conditions
from .readout_probe import trajectory
from .runtime import run,pulses
from .precision_data import evaluate
from .train import write_json,key


def training_case(profile,iteration,index):
    pi=int(profile=='uart_e');seed=351000000+pi*1000000+iteration*1000+index
    # Each four rounds visits every byte; seven such blocks rotate every timing.
    value=((iteration-1)%4)*64+index;condition=conditions(profile)[((iteration-1)//4+index)%7]
    if index%3==1:b,cut=prefix(profile,seed)
    else:
        b=Builder(profile,seed);cut=None
        if index%3==2:b.message(b.rng.integers(0,256,4).tolist())
    if index%2:
        errors=['framing','break']+(['parity'] if profile=='uart_e' else [])
        b.message([value],invalid=errors[((iteration-1)//4+index//2)%len(errors)])
        b.idle(int(b.rng.integers(0,5))*16)
    b.message([value],condition);b.message(b.rng.integers(0,256,4).tolist(),condition)
    if index%7==0:b.idle(4096)
    if cut is not None:return finish(b,cut,seed)
    s=b.finish();s['x']=features(s['lines'])[0];s['seed']=seed;return s


def fit(job):
    root,kw,profile,seed,rounds=job;root=Path(root);sh=make_shape(**kw)
    recipe='phase_error_mining_v3';folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    source=root/'models'/'phase_coverage_v3'/sh.name/profile/str(seed)
    b=json.loads(sorted(source.glob('block_*.json'))[-1].read_text());a=np.load(b['checkpoint']);p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights'])
    passing=b['selected']['message_accuracy']==1 and not any(b['selected'][k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
    target=0 if passing else rounds
    manifest=dict(source_block=str(sorted(source.glob('block_*.json'))[-1]),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
        reset_optimizer=True,seed_family=351000000,rounds=target,lr=.0001,window=512,hard_windows=32,anchor_windows=32,
        source_provenance=b.get('warm_start'),state_policy='model-only continuous trajectory recomputed per round; truncated initial states held within round')
    if (folder/'warm_start.json').exists():
        if json.loads((folder/'warm_start.json').read_text())!=manifest:raise ValueError('mining source changed')
    else:write_json(folder/'warm_start.json',manifest)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    trainable=np.ones_like(p);mid=sh.groups[1]
    for k,(src,dst) in enumerate(zip(sh.src,sh.dst)):
        if src in mid and dst in mid:trainable[k]=0
    for node in mid[1:]:trainable[len(sh.src)+node]=0
    m=np.zeros_like(p);v=np.zeros_like(p);step=exposure=scan_ticks=last=0
    def save(epoch):
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',p=p,m=m,v=v,leaks=sh.leaks,ending_state=np.zeros(sh.n),
            aux_weights=a['aux_weights'],aux_m=np.zeros_like(a['aux_m']),aux_v=np.zeros_like(a['aux_v']),
            metadata=json.dumps(dict(epoch=epoch,step=step,exposure=exposure,scan_ticks=scan_ticks,recipe=recipe,
                frozen_parameter_indices=np.flatnonzero(trainable==0).tolist())))
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];m=z['m'];v=z['v'];meta=json.loads(str(z['metadata']));step=meta['step'];exposure=meta['exposure'];scan_ticks=meta['scan_ticks']
    else:
        dl,score=evaluate(sh,p,root,profile,cw,'data_precision_v2');row=dict(epoch=0,exposure_ticks=0,scan_ticks=0,dev_loss=dl,**score);history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    best=max((r for r in history if 'dev_loss' in r),key=key);started=time.monotonic()
    for iteration in range(last+1,target+1):
        hard=[];anchors=[];training_errors=0;cached={}
        for i in range(64):
            s=training_case(profile,iteration,i);x=s['x'];y=s['labels'];h=trajectory(sh,p,x);scan_ticks+=len(x)
            offset=sh.parameters-6*sh.n-6;z=h@p[offset:-6].reshape(6,sh.n).T+p[-6:];pred=pulses(z.argmax(1))
            bad=np.flatnonzero((pred!=y)&(np.arange(len(y))>=s.get('startup_ambiguous_until',0)));training_errors+=len(bad)
            rng=np.random.default_rng([seed,iteration,i,912]);anchor=int(rng.integers(max(1,len(x)-511)))
            anchors.append((i,anchor,0,None));cached[i]=(s,h)
            # At most two distinct causal windows per case, scored by pulse errors.
            starts=sorted({max(0,min(len(x)-512,int(t)-256)) for t in bad})
            ranked=sorted(((int(np.sum((bad>=start)&(bad<start+512))),start) for start in starts),reverse=True)
            picked=[]
            for count,start in ranked:
                if all(abs(start-other)>=256 for other in picked):
                    hard.append((i,start,count,int(bad[(bad>=start)&(bad<start+512)][0])));picked.append(start)
                if len(picked)==2:break
        rng=np.random.default_rng([seed,iteration,981]);hard.sort(key=lambda r:(-r[2],r[0],r[1]));chosen=hard[:32]
        chosen+= [anchors[i] for i in rng.permutation(len(anchors))[:32]]
        chosen=[chosen[i] for i in rng.permutation(len(chosen))];losses=[]
        for i,start,count,error in chosen:
            s,h=cached[i];end=min(len(h),start+512);before=np.zeros(sh.n) if start==0 else h[start-1]
            loss,_,_,g,_=run(sh,p,s['x'][start:end],s['labels'][start:end],cw,before,backward=True)
            g*=trainable;norm=float(np.linalg.norm(g));g/=max(1,norm);step+=1;m=.9*m+.1*g;v=.999*v+.001*g*g
            p-=.0001*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8);np.clip(p,-7.99,7.99,out=p);exposure+=end-start;losses.append(loss)
        selection=[dict(case=i,data_seed=cached[i][0]['seed'],start=start,end=min(len(cached[i][1]),start+512),training_errors=count,first_error=error) for i,start,count,error in chosen]
        write_json(folder/f'windows_{iteration:04d}.json',selection)
        row=dict(epoch=iteration,exposure_ticks=exposure,scan_ticks=scan_ticks,training_pulse_errors=training_errors,
            mined_windows=len(hard[:32]),anchor_windows=32,train_loss=float(np.mean(losses)),elapsed_call=time.monotonic()-started)
        if iteration%5==0 or iteration==target:
            dl,score=evaluate(sh,p,root,profile,cw,'data_precision_v2');row.update(score);row['dev_loss']=dl
            if key(row)>key(best):best=row.copy()
            print(json.dumps(dict(profile=profile,seed=seed,round=iteration,exact=row['message_accuracy'],boundary=row['boundary_errors'],training_errors=training_errors)),flush=True)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint);np.savez_compressed(folder/'selected.npz',p=z['p'],leaks=z['leaks'])
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=target,selected_epoch=best['epoch'],selected=best,
        checkpoint=str(checkpoint),class_weights=cw.tolist(),exposure_ticks=exposure,scan_ticks=scan_ticks,warm_start=manifest,
        development_distribution='precision_v2',status='bounded_error_mining_not_capacity_proof')
    write_json(folder/f'block_{target:04d}.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);ap.add_argument('--rounds',type=int,default=56);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];label=f'error_mining_v3_{a.rounds}'
    jobs=[(str(root),kw,p,s,a.rounds) for p in ('uart_n','uart_e') for s in SEEDS];write_json(root/f'{label}_jobs.json',jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    results=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):
            results.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=results,total=len(jobs)))
