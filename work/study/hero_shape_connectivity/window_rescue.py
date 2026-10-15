"""Paired TBPTT windows with full training coverage and a coherent gradient batch."""
import argparse,json,time,shutil
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,features
from .data import load
from .error_mining import training_case
from .readout_probe import trajectory
from .runtime import run,pulses
from .precision_data import evaluate
from .train import write_json,key


def pool_cases(root,profile,iteration):
    rows=[]
    for i in range(64):
        s=training_case(profile,iteration,i);s['lines']=np.r_[s['lines'],np.ones((512,3),dtype=np.uint8)]
        s['labels']=np.r_[s['labels'],np.zeros(512,dtype=np.int32)];s['x']=features(s['lines'])[0]
        rows.append((f'generated_{iteration}_{i}',s))
    paths=[root/'data_precision_v2'/profile/'train'/f'long_{181+(iteration-1)%60:04d}']
    paths += [root/'data_precision_v2'/profile/'train'/f'cold_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256)]
    paths += [root/'data_startup_modes'/profile/f'idle_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256)]
    paths += [root/'data_startup_modes'/profile/f'errors_{i:03d}' for i in ((np.arange(8)+(iteration-1)*8)%64)]
    rows += [(str(path),load(path)) for path in paths]
    return rows


def fit(job):
    root,kw,profile,seed,window,target=job;root=Path(root);sh=make_shape(**kw);recipe=f'phase_window{window}_v4'
    folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    source=root/'models'/'phase_margin_calibration_v3'/sh.name/profile/str(seed)/'block_0001.json';b=json.loads(source.read_text());a=dict(np.load(b['checkpoint']));p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights'])
    provenance=dict(source_block=str(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),window=window,
        optimized_ticks_per_round=32768,lr=.0003,optimizer_steps_per_round=1,training_pool='64 generated + one verified long + 16 mid-frame cold + 16 known-idle + eight recovery',
        source_provenance=b.get('warm_start'),target_rounds=target)
    if (folder/'warm_start.json').exists():
        if json.loads((folder/'warm_start.json').read_text())!=provenance:raise ValueError('window rescue source changed')
    else:write_json(folder/'warm_start.json',provenance)
    passed=b['selected']['message_accuracy']==1 and not any(b['selected'][k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
    if passed:target=0
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    mask=np.ones_like(p);mid=sh.groups[1]
    for k,(src,dst) in enumerate(zip(sh.src,sh.dst)):
        if src in mid and dst in mid:mask[k]=0
    for node in mid[1:]:mask[len(sh.src)+node]=0
    m=np.zeros_like(p);v=np.zeros_like(p);step=exposure=scan_ticks=last=0
    def save(epoch):
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',p=p,m=m,v=v,leaks=sh.leaks,ending_state=np.zeros(sh.n),
            aux_weights=a['aux_weights'],aux_m=np.zeros_like(a['aux_m']),aux_v=np.zeros_like(a['aux_v']),
            metadata=json.dumps(dict(epoch=epoch,step=step,exposure=exposure,scan_ticks=scan_ticks,window=window,recipe=recipe,frozen_parameter_indices=np.flatnonzero(mask==0).tolist())))
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];m=z['m'];v=z['v'];meta=json.loads(str(z['metadata']));step=meta['step'];exposure=meta['exposure'];scan_ticks=meta['scan_ticks']
    else:
        row={**b['selected'],'epoch':0,'exposure_ticks':0,'scan_ticks':0};history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    best=max((r for r in history if 'dev_loss' in r),key=key);started=time.monotonic();number=32768//window
    for iteration in range(last+1,target+1):
        cached=pool_cases(root,profile,iteration);hard=[];anchors=[];states=[];errors=0
        for i,(identity,s) in enumerate(cached):
            x=s['x'];y=s['labels'];h=trajectory(sh,p,x);states.append(h);scan_ticks+=len(x)
            offset=sh.parameters-6*sh.n-6;z=h@p[offset:-6].reshape(6,sh.n).T+p[-6:];pred=pulses(z.argmax(1));bad=np.flatnonzero((pred!=y)&(np.arange(len(y))>=s.get('startup_ambiguous_until',0)));errors+=len(bad)
            assert len(x)>=window
            rng=np.random.default_rng([seed,iteration,i,811]);anchor=int(rng.integers(len(x)-window+1));anchors.append((i,anchor,0))
            starts=sorted({max(0,min(len(x)-window,int(t)-window//2)) for t in bad})
            ranked=sorted(((int(np.sum((bad>=start)&(bad<start+window))),start) for start in starts),reverse=True);picked=[]
            for count,start in ranked:
                if all(abs(start-other)>=window//2 for other in picked):hard.append((i,start,count));picked.append(start)
                if len(picked)==4:break
        hard.sort(key=lambda r:(-r[2],r[0],r[1]));chosen=hard[:number//2];rng=np.random.default_rng([seed,iteration,881]);permutation=rng.permutation(len(anchors))
        chosen += [anchors[int(i)] for i in np.resize(permutation,number-len(chosen))]
        grad=np.zeros_like(p);losses=[]
        for i,start,count in chosen:
            s=cached[i][1];before=np.zeros(sh.n) if start==0 else states[i][start-1]
            loss,_,_,g,_=run(sh,p,s['x'][start:start+window],s['labels'][start:start+window],cw,before,backward=True)
            grad+=g/number;losses.append(loss)
        grad*=mask;norm=float(np.linalg.norm(grad));grad/=max(1,norm);step+=1;m=.9*m+.1*grad;v=.999*v+.001*grad*grad
        p-=.0003*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8);np.clip(p,-7.99,7.99,out=p);exposure+=32768
        write_json(folder/f'windows_{iteration:04d}.json',[dict(case=cached[i][0],start=start,end=start+window,training_errors=count) for i,start,count in chosen])
        row=dict(epoch=iteration,exposure_ticks=exposure,scan_ticks=scan_ticks,training_pulse_errors=errors,hard_windows=min(len(hard),number//2),
            anchor_windows=number-min(len(hard),number//2),train_loss=float(np.mean(losses)),gradient_norm=norm,elapsed_call=time.monotonic()-started)
        if iteration%5==0 or iteration==target:
            dl,score=evaluate(sh,p,root,profile,cw,'data_precision_v2');row.update(score);row['dev_loss']=dl
            if key(row)>key(best):best=row.copy()
            print(json.dumps(dict(profile=profile,seed=seed,window=window,round=iteration,exact=row['message_accuracy'],boundary=row['boundary_errors'],training_errors=errors)),flush=True)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint);np.savez_compressed(folder/'selected.npz',p=z['p'],leaks=z['leaks'])
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=target,selected_epoch=best['epoch'],selected=best,
        checkpoint=str(checkpoint),class_weights=cw.tolist(),exposure_ticks=exposure,scan_ticks=scan_ticks,warm_start=provenance,
        development_distribution='precision_v2',status='window_rescue_not_capacity_proof')
    write_json(folder/f'block_{target:04d}.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=4);ap.add_argument('--rounds',type=int,default=120);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];label=f'paired_window_v4_{a.rounds}'
    jobs=[(str(root),kw,'uart_e',s,w,a.rounds) for s in (71,131) for w in (512,1024)];write_json(root/f'{label}_jobs.json',jobs)
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
