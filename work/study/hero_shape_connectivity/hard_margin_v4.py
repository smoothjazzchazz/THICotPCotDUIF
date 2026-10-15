"""Training-only multiclass margin fitting on verified fixed causal states."""
import argparse,json,time,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .hard_readout import objective,margin,minimize
from .run import ROOT,digest
from .readout_probe import trajectory
from .shapes import make_shape
from .data import load
from .precision_data import evaluate
from .train import write_json,key


def fit(job):
    root,kw,profile,seed,target=job;root=Path(root);sh=make_shape(**kw);recipe='phase_hard_margin_v4'
    folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    source=root/'models'/'phase_margin_calibration_v3'/sh.name/profile/str(seed)/'block_0001.json';b=json.loads(source.read_text())
    a=dict(np.load(b['checkpoint']));p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights'])
    offset=sh.parameters-6*sh.n-6;prior=np.c_[p[offset:-6].reshape(6,sh.n),p[-6:]]
    provenance=dict(source_block=str(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
        source_provenance=b.get('warm_start'),objective='squared multiclass margin0.5 plus1e-6 distance to initial readout',
        fixed='entire causal state transition; fit only six affine logits',corpus='precision_v2 plus both startup modes',
        policy='exclude only unscored ambiguous startup prefix from loss, while carrying its causal state; no runtime reset or flag',
        scipy_version=__import__('scipy').__version__)
    path=folder/'warm_start.json'
    if path.exists():
        if json.loads(path.read_text())!=provenance:raise ValueError('margin source changed')
    else:write_json(path,provenance)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    x=np.empty((0,sh.n+1));y=np.empty(0,dtype=np.int32);w=prior.copy();exposure=last=0
    def save(epoch):
        meta=json.loads(str(a['metadata']));meta.update(epoch=epoch,step=0,exposure=exposure,recipe=recipe,optimizer='fresh bounded L-BFGS per round; support and parameters checkpointed')
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'m':np.zeros_like(p),'v':np.zeros_like(p),'metadata':json.dumps(meta)},
            support_x=x,support_y=y,w=w,scan_ticks=exposure)
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];w=z['w'];x=z['support_x'];y=z['support_y'];exposure=int(z['scan_ticks'])
    else:
        row={**b['selected'],'epoch':0,'exposure_ticks':0};history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    best=max((r for r in history if 'dev_loss' in r),key=key);started=time.monotonic()
    for iteration in range(last+1,target+1):
        paths=[root/'data_precision_v2'/profile/'train'/f'long_{240+iteration:04d}']
        paths.extend(root/'data_precision_v2'/profile/'train'/f'cold_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256))
        paths.extend(root/'data_startup_modes'/profile/f'idle_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256))
        paths.extend(root/'data_startup_modes'/profile/f'errors_{i:03d}' for i in ((np.arange(4)+(iteration-1)*4)%64))
        candidates=[x];targets=[y];mistakes=0
        for path in paths:
            s=load(path);h=trajectory(sh,p,s['x']);xx=np.c_[h,np.ones(len(h))];yy=s['labels'];m=margin(xx,yy,w)
            scored=np.arange(len(yy))>=s.get('startup_ambiguous_until',0);exposure+=len(yy);mistakes+=int(((m<=0)&scored).sum())
            indices=np.flatnonzero((m<.75)&scored)
            if len(indices)>16000:indices=indices[np.argpartition(m[indices],16000)[:16000]]
            candidates.append(xx[indices]);targets.append(yy[indices])
        x=np.concatenate(candidates);y=np.concatenate(targets);m=margin(x,y,w)
        if len(y)>100000:
            keep=np.argpartition(m,100000)[:100000];x=x[keep];y=y[keep]
        solved=minimize(objective,w.ravel(),args=(x,y,prior),method='L-BFGS-B',jac=True,bounds=[(-7.99,7.99)]*w.size,
            options=dict(maxiter=150,ftol=1e-12,gtol=1e-7,maxls=40))
        w=solved.x.reshape(prior.shape);p[offset:-6]=w[:,:-1].ravel();p[-6:]=w[:,-1]
        row=dict(epoch=iteration,exposure_ticks=exposure,train_loss=float(solved.fun),training_misclassifications_before_fit=mistakes,
            support_misclassifications=int((margin(x,y,w)<=0).sum()),retained_training_states=len(y),
            optimizer_success=bool(solved.success),optimizer_message=str(solved.message),solver_iterations=int(solved.nit),elapsed_call=time.monotonic()-started)
        if iteration%2==0 or iteration==target:
            dl,score=evaluate(sh,p,root,profile,cw,'data_precision_v2');row.update(score);row['dev_loss']=dl
            if key(row)>key(best):best=row.copy()
            print(json.dumps(dict(seed=seed,round=iteration,exact=row['message_accuracy'],boundary=row['boundary_errors'],support_errors=row['support_misclassifications'])),flush=True)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint);np.savez_compressed(folder/'selected.npz',p=z['p'],leaks=z['leaks'])
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=target,selected_epoch=best['epoch'],selected=best,
        checkpoint=str(checkpoint),class_weights=cw.tolist(),exposure_ticks=exposure,warm_start=provenance,
        development_distribution='precision_v2',status='bounded_fixed_state_margin_fit_not_capacity_proof')
    write_json(folder/f'block_{target:04d}.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--rounds',type=int,default=20);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];label=f'hard_margin_v4_{a.rounds}'
    jobs=[(str(root),kw,'uart_e',s,a.rounds) for s in (71,131)];write_json(root/f'{label}_jobs.json',jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
