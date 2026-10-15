"""Fit existing affine outputs, requiring complete training-startup coverage."""
import argparse,json,time,shutil,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .readout_probe import trajectory
from .shapes import make_shape,SEEDS
from .data import load,metrics
from .startup_evaluate import evaluate
from .train import write_json,key,evaluate_stream


def passed(score):
    return score['exact_messages']==score['valid_messages'] and not any(score[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))


def audit_training(sh,p,root,profile,cw):
    rows=[]
    for path in sorted((root/'data_startup_modes'/profile).glob('*.json')):
        data=load(path.with_suffix(''));_,z=evaluate_stream(sh,p,data,cw);score=metrics(data,z.argmax(1))
        rows.append(dict(case=path.stem,**{k:score[k] for k in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted')}))
    fields=('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted')
    return dict(cases=rows,**{k:sum(r[k] for r in rows) for k in fields},failed_cases=sum(not passed(r) for r in rows))


def fit(job):
    root,kw,profile,seed,target,*override=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from .hard_readout import objective,margin,minimize
    sh=make_shape(**kw);recipe=override[0]['recipe'] if override else 'phase_startup_margin_v5';folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    source=Path(override[0]['source_block']) if override else root/'models'/'final_portfolio_v2a'/sh.name/profile/str(seed)/'block_0000.json'
    if override:assert digest(source)==override[0]['source_block_sha256']
    b=json.loads(source.read_text());a=dict(np.load(b['checkpoint']))
    if override:assert digest(b['checkpoint'])==override[0]['checkpoint_sha256']
    p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights']);offset=sh.parameters-6*sh.n-6;fixed=p[:offset].copy()
    prior=np.c_[p[offset:-6].reshape(6,sh.n),p[-6:]];w=prior.copy()
    provenance=dict(source_block=str(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
        objective='multiclass margin0.5 plus1e-6 prior; fixed causal state; all six affine rows trainable',
        development='precision_v2 plus corner_v4 and startup_dev_v5;8864 valid groups/profile',
        training='long333–364 plus16 midframe,16 known-idle and4 errors per round; full320-case training audit before skipping and after selection',
        budget=dict(rounds=target,max_solver_iterations=150,support_cap=100000,weight_bound=7.99),
        selection='unchanged development key; skip only if enlarged development AND complete training startup audit pass',
        confirmation='no confirmation samples in fitting, support selection or checkpoint selection')
    path=folder/'warm_start.json'
    if path.exists():assert json.loads(path.read_text())==provenance,'source changed'
    else:write_json(path,provenance)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    x=np.empty((0,sh.n+1));y=np.empty(0,dtype=np.int32);exposure=last=0;cache=folder/'development_states'
    def save(epoch):
        meta=json.loads(str(a['metadata']));meta.update(epoch=epoch,step=0,exposure=exposure,recipe=recipe)
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'m':np.zeros_like(p),'v':np.zeros_like(p),'metadata':json.dumps(meta),
            'support_x':x,'support_y':y,'w':w,'scan_ticks':exposure})
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];w=z['w'];x=z['support_x'];y=z['support_y'];exposure=int(z['scan_ticks'])
    else:
        dl,score=evaluate(sh,p,root,profile,cw,cache);training=audit_training(sh,p,root,profile,cw);write_json(folder/'source_training_audit.json',training)
        row=dict(epoch=0,exposure_ticks=0,dev_loss=dl,training_startup_failed_cases=training['failed_cases'],**score);history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    if passed(history[0]) and history[0]['training_startup_failed_cases']==0:target=0
    best=max((r for r in history if 'dev_loss' in r),key=key);started=time.monotonic()
    for iteration in range(last+1,target+1):
        paths=[root/'data_precision_v2'/profile/'train'/f'long_{332+iteration:04d}']
        paths.extend(root/'data_precision_v2'/profile/'train'/f'cold_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256))
        paths.extend(root/'data_startup_modes'/profile/f'idle_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256))
        paths.extend(root/'data_startup_modes'/profile/f'errors_{i:03d}' for i in ((np.arange(4)+(iteration-1)*4)%64))
        xx=[x];yy=[y];mistakes=0
        for path in paths:
            data=load(path);h=trajectory(sh,p,data['x']);features=np.c_[h,np.ones(len(h))];labels=data['labels'];m=margin(features,labels,w)
            scored=np.arange(len(h))>=data.get('startup_ambiguous_until',0);exposure+=len(h);mistakes+=int(((m<=0)&scored).sum());take=np.flatnonzero((m<.75)&scored)
            if len(take)>16000:take=take[np.argpartition(m[take],16000)[:16000]]
            xx.append(features[take]);yy.append(labels[take])
        x=np.concatenate(xx);y=np.concatenate(yy);m=margin(x,y,w)
        if len(y)>100000:
            keep=np.argpartition(m,100000)[:100000];x=x[keep];y=y[keep]
        solved=minimize(objective,w.ravel(),args=(x,y,prior),method='L-BFGS-B',jac=True,bounds=[(-7.99,7.99)]*w.size,
            options=dict(maxiter=150,ftol=1e-12,gtol=1e-7,maxls=40))
        assert np.isfinite(solved.fun) and np.isfinite(solved.x).all(),'nonfinite optimization result'
        w=solved.x.reshape(prior.shape);p[offset:-6]=w[:,:-1].ravel();p[-6:]=w[:,-1];assert np.array_equal(p[:offset],fixed)
        row=dict(epoch=iteration,exposure_ticks=exposure,train_loss=float(solved.fun),training_errors_before_fit=mistakes,
            support_errors=int((margin(x,y,w)<=0).sum()),retained_training_states=len(y),optimizer_success=bool(solved.success),
            optimizer_message=str(solved.message),solver_iterations=int(solved.nit),elapsed_call=time.monotonic()-started)
        if iteration%4==0 or iteration==target:
            dl,score=evaluate(sh,p,root,profile,cw,cache);row.update(score);row['dev_loss']=dl
            if key(row)>key(best):best=row.copy()
            print(json.dumps(dict(profile=profile,seed=seed,round=iteration,exact=row['message_accuracy'],boundary=row['boundary_errors'],support_errors=row['support_errors'])),flush=True)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
        history.append(row)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint);dl,scalar=evaluate(sh,z['p'],root,profile,cw,None)
    for field in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted','false_events'):assert scalar[field]==best[field],('scalar mismatch',field)
    final_training=audit_training(sh,z['p'],root,profile,cw);write_json(folder/'selected_training_audit.json',final_training)
    np.savez_compressed(folder/'selected.npz',p=z['p'],leaks=z['leaks'])
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=target,selected_epoch=best['epoch'],selected=best,
        checkpoint=str(checkpoint),class_weights=cw.tolist(),exposure_ticks=exposure,warm_start=provenance,selected_training_failed_cases=final_training['failed_cases'],
        development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status='fixed_state_diagnostic_not_capacity_proof',scalar_replay_verified=True)
    write_json(folder/f'block_{target:04d}.json',result);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);ap.add_argument('--rounds',type=int,default=32);args=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];label=f'startup_margin_v5_{args.rounds}'
    assert (root/'data_startup_dev_v5'/'manifest.json').exists(),'startup development incomplete'
    jobs=[(str(root),kw,p,s,args.rounds) for p in ('uart_n','uart_e') for s in SEEDS];write_json(root/f'{label}_jobs.json',jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
