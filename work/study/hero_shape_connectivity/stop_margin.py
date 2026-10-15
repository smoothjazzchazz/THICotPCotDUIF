"""Fit one existing boundary output against fixed competing logits and states."""
import argparse,json,time,sys,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .data import load
from .readout_probe import trajectory
from .corner_evaluate import evaluate
from .train import key,write_json


def objective(w,x,sign,threshold,prior):
    if len(x)==0:
        delta=w-prior
        return float(1e-6*np.sum(delta*delta)),2e-6*delta
    gap=np.maximum(0.,.5-sign*(x@w-threshold));delta=w-prior
    return float(np.mean(gap*gap)+1e-6*np.sum(delta*delta)), -2*(sign*gap)@x/len(x)+2e-6*delta


def fit(job):
    root,kw,profile,seed,target=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from scipy.optimize import minimize
    sh=make_shape(**kw)
    if getattr(sh,'mixed',False) or getattr(sh,'gated',False):raise ValueError('this fixed-state diagnostic requires ordinary tanh nodes')
    recipe='phase_stop_margin_v4';folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    source=root/'models'/'phase_margin_calibration_v3'/sh.name/profile/str(seed)/'block_0001.json';b=json.loads(source.read_text());a=dict(np.load(b['checkpoint']))
    p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights']);offset=sh.parameters-6*sh.n-6
    indices=np.r_[np.arange(offset+4*sh.n,offset+5*sh.n),len(p)-2];prior=p[indices].copy();fixed=p.copy()
    provenance=dict(source_block=str(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_provenance=b.get('warm_start'),
        objective='STOP signed squared margin0.5 against strongest unchanged competing logit plus1e-6 distance to initial row',
        fixed='all recurrent weights/leaks and the other five output rows/biases',trainable_parameter_indices=indices.tolist(),
        development='precision_v2 plus independent corner_development family361000000',rounds=target,
        training='long301 onward plus16 midframe,16 known-idle and4 recovery cases per round; ambiguous prefix carried but unscored',
        budget='32 rounds; max150 bounded L-BFGS iterations per round; retain100000 worst-margin training states',selection='unchanged complete-message/boundary/false-event/development-loss key on enlarged development')
    path=folder/'warm_start.json'
    if path.exists():
        if json.loads(path.read_text())!=provenance:raise ValueError('STOP fit source changed')
    else:write_json(path,provenance)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    w=prior.copy();x=np.empty((0,sh.n+1));sign=np.empty(0);threshold=np.empty(0);last=exposure=0;cache=folder/'development_states'
    def save(epoch):
        meta=json.loads(str(a['metadata']));meta.update(epoch=epoch,step=0,exposure=exposure,recipe=recipe)
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'m':np.zeros_like(p),'v':np.zeros_like(p),'metadata':json.dumps(meta)},
            support_x=x,support_sign=sign,support_threshold=threshold,w=w,scan_ticks=exposure)
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];w=z['w'];x=z['support_x'];sign=z['support_sign'];threshold=z['support_threshold'];exposure=int(z['scan_ticks'])
    else:
        dl,score=evaluate(sh,p,root,profile,cw,cache);row=dict(epoch=0,exposure_ticks=0,dev_loss=dl,**score);history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    best=max((r for r in history if 'dev_loss' in r),key=key);s=history[0]
    if s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted')):target=0
    started=time.monotonic();other=[0,1,2,3,5];weights=fixed[offset:-6].reshape(6,sh.n)[other];bias=fixed[-6:][other]
    for iteration in range(last+1,target+1):
        paths=[root/'data_precision_v2'/profile/'train'/f'long_{300+iteration:04d}']
        paths.extend(root/'data_precision_v2'/profile/'train'/f'cold_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256))
        paths.extend(root/'data_startup_modes'/profile/f'idle_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256))
        paths.extend(root/'data_startup_modes'/profile/f'errors_{i:03d}' for i in ((np.arange(4)+(iteration-1)*4)%64))
        xx=[x];ss=[sign];tt=[threshold];mistakes=0
        for path in paths:
            data=load(path);h=trajectory(sh,p,data['x']);features=np.c_[h,np.ones(len(h))];sy=np.where(data['labels']==4,1.,-1.);tau=(h@weights.T+bias).max(1)
            margin=sy*(features@w-tau);scored=np.arange(len(h))>=data.get('startup_ambiguous_until',0);exposure+=len(h);mistakes+=int(((margin<=0)&scored).sum())
            take=np.flatnonzero((margin<.75)&scored)
            if len(take)>16000:take=take[np.argpartition(margin[take],16000)[:16000]]
            xx.append(features[take]);ss.append(sy[take]);tt.append(tau[take])
        x=np.concatenate(xx);sign=np.concatenate(ss);threshold=np.concatenate(tt);margin=sign*(x@w-threshold)
        if len(x)>100000:
            keep=np.argpartition(margin,100000)[:100000];x=x[keep];sign=sign[keep];threshold=threshold[keep]
        solved=minimize(objective,w,args=(x,sign,threshold,prior),method='L-BFGS-B',jac=True,bounds=[(-7.99,7.99)]*len(w),options=dict(maxiter=150,ftol=1e-12,gtol=1e-7,maxls=40))
        w=solved.x;p[indices]=w;unchanged=np.ones(len(p),dtype=bool);unchanged[indices]=False;assert np.array_equal(p[unchanged],fixed[unchanged])
        row=dict(epoch=iteration,exposure_ticks=exposure,train_loss=float(solved.fun),training_stop_errors_before_fit=mistakes,
            support_errors=int(np.sum(sign*(x@w-threshold)<=0)),retained_training_states=len(x),optimizer_success=bool(solved.success),optimizer_message=str(solved.message),solver_iterations=int(solved.nit),elapsed_call=time.monotonic()-started)
        if iteration%4==0 or iteration==target:
            dl,score=evaluate(sh,p,root,profile,cw,cache);row.update(score);row['dev_loss']=dl
            if key(row)>key(best):best=row.copy()
            print(json.dumps(dict(profile=profile,seed=seed,round=iteration,exact=row['message_accuracy'],boundary=row['boundary_errors'],support_errors=row['support_errors'])),flush=True)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint)
    dl,scalar=evaluate(sh,z['p'],root,profile,cw,None)
    for field in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted','false_events'):assert scalar[field]==best[field],('cached readout disagrees with scalar receiver',field)
    np.savez_compressed(folder/'selected.npz',p=z['p'],leaks=z['leaks'])
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=target,selected_epoch=best['epoch'],selected=best,checkpoint=str(checkpoint),class_weights=cw.tolist(),
        exposure_ticks=exposure,warm_start=provenance,development_distribution='precision_v2_plus_corners_v4',status='fixed_state_stop_only_diagnostic_not_capacity_proof',scalar_replay_verified=True)
    write_json(folder/f'block_{target:04d}.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);ap.add_argument('--rounds',type=int,default=32);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];label=f'stop_margin_v4_{a.rounds}'
    if not (root/'data_corner_dev_v4'/'manifest.json').exists():raise ValueError('corner development must finish before fitting')
    jobs=[(str(root),kw,p,s,a.rounds) for p in ('uart_n','uart_e') for s in SEEDS];write_json(root/f'{label}_jobs.json',jobs)
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
