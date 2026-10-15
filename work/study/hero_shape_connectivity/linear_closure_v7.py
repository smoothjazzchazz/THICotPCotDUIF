"""Minimum-change linear constraints with full-pool verification, frozen state."""
import argparse,hashlib,json,shutil,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .data import load
from .readout_probe import trajectory
from .startup_evaluate import evaluate
from .startup_margin_v5 import passed,audit_training
from .train import key,write_json


def training_paths(root,profile):
    paths=sorted((root/'data_stationary_train_v6'/profile).glob('*.json'))
    paths += [root/'data_precision_v2'/profile/'train'/f'long_{i:04d}.json' for i in range(365,397)]
    paths += sorted((root/'data_startup_modes'/profile).glob('*.json'))
    paths += [root/'data_precision_v2'/profile/'train'/f'cold_{i:03d}.json' for i in range(256)]
    assert len(paths)==624 and all(p.exists() for p in paths),'complete training pool required'
    return paths


def verify_training(sh,p,paths,cache):
    """Independent full-pool check of the actually selected readout."""
    offset=sh.parameters-6*sh.n-6;w=p[offset:-6].reshape(6,sh.n);bias=p[-6:];rows=[]
    for fi,path in enumerate(paths):
        data=load(path.with_suffix(''));file=cache/f'{fi:04d}.npy'
        h=np.load(file,mmap_mode='r') if file.exists() else trajectory(sh,p,data['x']);errors=0;until=data.get('startup_ambiguous_until',0)
        for start in range(0,len(h),8192):
            end=min(len(h),start+8192);pred=(h[start:end]@w.T+bias).argmax(1)
            errors+=int(np.sum((pred!=data['labels'][start:end])&(np.arange(start,end)>=until)))
        rows.append(dict(file_index=fi,canonical_errors=errors));del h,data
    return dict(cases=rows,canonical_errors=sum(r['canonical_errors'] for r in rows))


def fit(job):
    root,kw,profile,seed,target,source=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from .hard_readout import objective,margin
    from .linear_margin_diagnostic import minimum_change
    sh=make_shape(**kw);assert not getattr(sh,'mixed',False) and not getattr(sh,'gated',False)
    recipe='phase_linear_closure_v7';folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    assert digest(source['block'])==source['block_sha256'];b=json.loads(Path(source['block']).read_text());assert digest(b['checkpoint'])==source['checkpoint_sha256']
    a=dict(np.load(b['checkpoint']));p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights']);offset=sh.parameters-6*sh.n-6;fixed=p[:offset].copy()
    prior=np.c_[p[offset:-6].reshape(6,sh.n),p[-6:]];w=prior.copy();paths=training_paths(root,profile)
    pool_path=root/f'closure_v6_{profile}_pool.json'
    provenance=dict(source=source,training_pool=str(pool_path),training_pool_sha256=digest(pool_path),rounds=target,
        objective='minimum L1 change from source outputs subject to correct-class margin0.01 on retained training states',constraint_policy='retain every encountered margin<0.02 state, deduplicated by file/tick; never evict',
        trust_bound=None,absolute_bound=7.99,solver_time_limit_seconds=300,max_support=100000,
        development='precision_v2 plus corners_v4 plus startup_v5; source/selection never use confirmation')
    warm=folder/'warm_start.json'
    if warm.exists():assert json.loads(warm.read_text())==provenance,'source or pool changed'
    else:write_json(warm,provenance)
    block=folder/f'block_{target:04d}.json'
    if block.exists():return json.loads(block.read_text())
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    x=np.empty((0,sh.n+1));y=np.empty(0,dtype=np.int32);ids=np.empty(0,dtype=np.int64);last=scanned=0;cache=folder/'development_states';train_cache=Path(source['training_cache'])
    def save(epoch):
        meta=json.loads(str(a['metadata']));meta.update(epoch=epoch,step=0,exposure=scanned,recipe=recipe)
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'m':np.zeros_like(p),'v':np.zeros_like(p),'metadata':json.dumps(meta),
            'support_x':x,'support_y':y,'support_ids':ids,'w':w,'scan_ticks':scanned})
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];w=z['w'];x=z['support_x'];y=z['support_y'];ids=z['support_ids'];scanned=int(z['scan_ticks'])
    else:
        assert digest(source['retained_checkpoint'])==source['retained_checkpoint_sha256']
        retained=np.load(source['retained_checkpoint']);x=retained['support_x'];y=retained['support_y'];ids=retained['support_ids']
        dl,score=evaluate(sh,p,root,profile,cw,cache);row=dict(epoch=0,exposure_ticks=0,dev_loss=dl,**score);history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    stamp=hashlib.sha256(fixed.tobytes()+sh.leaks.tobytes()).hexdigest();identity=dict(state_sha256=stamp,pool_sha256=digest(pool_path),dtype='float64')
    assert json.loads((train_cache/'identity.json').read_text())==identity
    verified_path=folder/'training_verified_epochs.json';verified=set(json.loads(verified_path.read_text())) if verified_path.exists() else set()
    seen=set(ids.tolist());best=max((r for r in history if 'dev_loss' in r),key=key);started=time.monotonic();status='minimum_change_active_constraint_diagnostic_not_capacity_proof';completed=last
    for iteration in range(last+1,target+1):
        xx=[x];yy=[y];ii=[ids];errors=added=0;minimum=1e300;cases=[];use_cache=iteration>1 or not passed(history[0])
        for fi,path in enumerate(paths):
            data=load(path.with_suffix(''));state_file=train_cache/f'{fi:04d}.npy'
            if state_file.exists():h=np.load(state_file,mmap_mode='r')
            else:
                h=trajectory(sh,p,data['x'])
                # Original v6 cache is read-only; missing derived states are recomputed.
            count=0;case_min=1e300;until=data.get('startup_ambiguous_until',0)
            for start in range(0,len(h),8192):
                end=min(len(h),start+8192);features=np.c_[h[start:end],np.ones(end-start)];labels=data['labels'][start:end];m=margin(features,labels,w);scored=np.arange(start,end)>=until
                if scored.any():case_min=min(case_min,float(m[scored].min()))
                count+=int(((m<=0)&scored).sum());take=np.flatnonzero((m<.02)&scored)
                new=np.array([int(t) for t in take if (fi*(1<<32)+start+int(t)) not in seen],dtype=np.int64)
                if len(new):
                    new_ids=fi*(1<<32)+start+new;seen.update(new_ids.tolist());xx.append(features[new]);yy.append(labels[new]);ii.append(new_ids);added+=len(new)
            scanned+=len(h);errors+=count;minimum=min(minimum,case_min);cases.append(dict(file_index=fi,canonical_errors=count,minimum_margin=case_min));del h,data
        x=np.concatenate(xx);y=np.concatenate(yy);ids=np.concatenate(ii)
        write_json(folder/f'scan_{iteration:04d}.json',dict(cases=cases,checkpoint_epoch=history[-1]['epoch'],canonical_errors=errors,minimum_margin=minimum,added_constraints=added,retained_constraints=len(y)))
        if errors==0:verified.add(history[-1]['epoch'])
        previous_score=next(r for r in reversed(history) if 'dev_loss'in r)
        closed=errors==0 and passed(previous_score)
        oversized=len(y)>100000
        if errors==0 or oversized:
            value=float(np.abs(w-prior).sum());nit=0;success=errors==0;message='full training canonical scan passes; development reported separately' if errors==0 else 'support budget exceeded; unresolved'
            if oversized:status='support_budget_exhausted_not_capacity_proof'
        else:
            solved=minimum_change(x,y,prior)
            nit=int(solved.nit);success=bool(solved.success);message=str(solved.message)
            write_json(folder/f'solver_{iteration:04d}.json',dict(success=success,status=int(solved.status),message=message,iterations=nit))
            if success:
                w=np.clip(solved.x[:prior.size].reshape(prior.shape),-7.99,7.99)
                assert margin(x,y,w).min()>=.01-1e-7
                p[offset:-6]=w[:,:-1].ravel();p[-6:]=w[:,-1]
                value=float(np.abs(w-prior).sum())
            else:
                value=None;status='retained_constraint_solver_unresolved_not_architecture_failure'
        assert np.array_equal(p[:offset],fixed);assert np.max(np.abs(w))<=7.9900001
        dl,score=evaluate(sh,p,root,profile,cw,cache)
        row=dict(epoch=iteration,exposure_ticks=scanned,train_loss=value,training_errors_before_fit=errors,retained_training_states=len(y),added_constraints=added,
            support_errors=int((margin(x,y,w)<=0).sum()),optimizer_success=success,optimizer_message=message,solver_iterations=nit,
            verified_training_closure=closed,elapsed_call=time.monotonic()-started,dev_loss=dl,**score)
        if key(row)>key(best):best=row.copy()
        save(iteration)
        if closed:verified.add(iteration)
        write_json(verified_path,sorted(verified))
        with journal.open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
        history.append(row);completed=iteration
        print(json.dumps(dict(profile=profile,seed=seed,round=iteration,training_errors_before=errors,support_errors=row['support_errors'],constraints=len(y),exact=row['message_accuracy'],boundary=row['boundary_errors'],closed=closed)),flush=True)
        if errors==0 or oversized or not success:break
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint)
    selected_audit=verify_training(sh,z['p'],paths,train_cache);write_json(folder/'best_development_training_audit.json',dict(epoch=best['epoch'],**selected_audit))
    if selected_audit['canonical_errors']==0:verified.add(best['epoch'])
    eligible=[r for r in history if 'dev_loss'in r and passed(r) and r['epoch'] in verified]
    if eligible:
        best=max(eligible,key=key);checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint)
    write_json(verified_path,sorted(verified));dl,scalar=evaluate(sh,z['p'],root,profile,cw,None)
    for field in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted','false_events'):assert scalar[field]==best[field],('scalar mismatch',field)
    training=audit_training(sh,z['p'],root,profile,cw);write_json(folder/'selected_training_startup_audit.json',training);np.savez_compressed(folder/'selected.npz',p=z['p'],leaks=z['leaks'])
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=completed,requested_rounds=target,selected_epoch=best['epoch'],selected=best,
        checkpoint=str(checkpoint),class_weights=cw.tolist(),exposure_ticks=scanned,warm_start=provenance,selected_training_failed_cases=training['failed_cases'],
        development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status=status,scalar_replay_verified=True,
        selected_full_training_verified=best['epoch'] in verified,selection='unchanged development key among jointly training-verified/development-passing checkpoints if any; otherwise best development diagnostic remains unresolved')
    write_json(block,result);return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);ap.add_argument('--rounds',type=int,default=16);args=ap.parse_args()
    root=ROOT/'runs/connectivity01';label=f'linear_closure_v7_{args.rounds}';file=root/f'{label}_jobs.json'
    if file.exists():jobs=json.loads(file.read_text())
    else:
        jobs=[]
        for profile,seed in [('uart_n',131),('uart_e',47),('uart_e',71)]:
            source=next((root/'models/phase_closure_v6').glob(f'*/{profile}/{seed}/block_0008.json'));b=json.loads(source.read_text())
            retained=source.parent/'epoch_0008.npz'
            record=dict(block=str(source),block_sha256=digest(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
                retained_checkpoint=str(retained),retained_checkpoint_sha256=digest(retained),training_cache=str(source.parent/'training_states'),
                policy='same-seed completed closure-v6 block; retained training-only constraints; no confirmation data or new runtime state')
            jobs.append((str(root),b['construction'],profile,seed,args.rounds,record))
        write_json(file,jobs)
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
