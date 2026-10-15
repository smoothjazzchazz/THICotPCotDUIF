"""Retained constrained fitting with balanced independent invalid/recovery coverage."""
import json,hashlib,shutil,sys,os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest,source_files
from .shapes import make_shape
from .readout_probe import trajectory
from .closure_v6 import training_paths,verify_training
from .startup_evaluate import evaluate
from .startup_margin_v5 import passed,audit_training
from .data import load,metrics
from .train import key,write_json


def fit(job):
    root,kw,profile,seed,target,source=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from .hard_readout import objective,margin
    from .linear_margin_diagnostic import minimum_change
    assert digest(source['block'])==source['block_sha256'];b=json.loads(Path(source['block']).read_text());assert digest(b['checkpoint'])==source['checkpoint_sha256']
    sh=make_shape(**kw);a=dict(np.load(b['checkpoint']));p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights']);offset=sh.parameters-6*sh.n-6;fixed=p[:offset].copy()
    prior=np.c_[p[offset:-6].reshape(6,sh.n),p[-6:]];w=prior.copy();recipe='phase_gated_linear_v13';folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);result_file=folder/f'block_{target:04d}.json'
    if result_file.exists():return json.loads(result_file.read_text())
    pool=root/f'error_grid_v13_{profile}_pool.json';pool_record=json.loads(pool.read_text());paths=[Path(e['path']) for e in pool_record['paths']];assert len(paths)==1296
    for entry,path in zip(pool_record['paths'],paths):
        assert str(path)==entry['path'] and digest(path)==entry['metadata_sha256'] and digest(path.with_suffix('.npz'))==entry['arrays_sha256'],'training pool changed'
    provenance=dict(source=source,training_pool=str(pool),training_pool_sha256=digest(pool),rounds=target,trust_bound=None,absolute_bound=7.99,
        objective='minimum L1 distance from original six affine rows, required margin0.01 on all retained states',mining='one worst margin<0.75 per true class per complete training file, retain all unique constraints; at most7776 additions/scan',
        support_cap=100000,stop='complete training scan has zero canonical errors and minimum margin>=0.0099, with complete expanded-development pass',
        inference='all48 recurrent states,16 gates, proposal/gate parameters and leaks remain fixed; no confirmation samples used')
    warm=folder/'warm_start.json'
    if warm.exists():assert json.loads(warm.read_text())==provenance
    else:write_json(warm,provenance)
    cache=folder/'training_states';cache.mkdir(exist_ok=True);dev_cache=Path(source['development_cache']);assert dev_cache.is_dir();stamp=hashlib.sha256(fixed.tobytes()+sh.leaks.tobytes()).hexdigest()
    identity=dict(state_sha256=stamp,pool_sha256=digest(pool),dtype='float64')
    if (cache/'identity.json').exists():assert json.loads((cache/'identity.json').read_text())==identity
    else:
        old_cache=Path(source['state_cache']);old_identity=json.loads((old_cache/'identity.json').read_text());assert old_identity['state_sha256']==stamp and old_identity['pool_sha256']==pool_record['existing_pool_sha256']
        for fi in range(624):
            old=old_cache/f'{fi:04d}.npy';new=cache/old.name;assert old.exists()
            if not new.exists():os.link(old,new)
        write_json(cache/'identity.json',identity)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else [];x=np.empty((0,sh.n+1));y=np.empty(0,dtype=np.int32);ids=np.empty(0,dtype=np.int64);last=scanned=0
    def save(epoch):
        meta=json.loads(str(a['metadata']));meta.update(recipe=recipe,epoch=epoch,step=0,exposure=scanned)
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'m':np.zeros_like(p),'v':np.zeros_like(p),'metadata':json.dumps(meta),'support_x':x,'support_y':y,'support_ids':ids,'w':w,'scan_ticks':scanned})
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];w=z['w'];x=z['support_x'];y=z['support_y'];ids=z['support_ids'];scanned=int(z['scan_ticks'])
    else:
        assert digest(source['constraints'])==source['constraints_sha256'];initial=np.load(source['constraints']);x=initial['support_x'];y=initial['support_y'];ids=initial['support_ids']
        dl,score=evaluate(sh,p,root,profile,cw,dev_cache);history=[dict(epoch=0,exposure_ticks=0,dev_loss=dl,**score)];save(0)
        with journal.open('a') as f:f.write(json.dumps(history[0])+'\n')
    best=max(history,key=key);seen=set(ids.tolist());status='finite_constraint_fit_not_capacity_proof'
    for iteration in range(last+1,target+1):
        xx=[];yy=[];ii=[];errors=added=0;minimum=1e300;case_rows=[]
        for fi,path in enumerate(paths):
            s=load(path.with_suffix(''));state_file=cache/f'{fi:04d}.npy'
            if not state_file.exists():
                temporary=state_file.with_suffix('.pending.npy');np.save(temporary,trajectory(sh,p,s['x']));temporary.replace(state_file)
            h=np.load(state_file,mmap_mode='r');winners={};count=0;case_min=1e300;until=s.get('startup_ambiguous_until',0)
            for start in range(0,len(h),8192):
                end=min(len(h),start+8192);features=np.c_[h[start:end],np.ones(end-start)];labels=s['labels'][start:end];m=margin(features,labels,w);valid=np.arange(start,end)>=until
                if valid.any():case_min=min(case_min,float(m[valid].min()))
                count+=int(((m<=0)&valid).sum())
                for label in range(6):
                    take=np.flatnonzero(valid&(labels==label))
                    if not len(take):continue
                    t=int(take[np.argmin(m[take])])
                    if m[t]<.75 and (label not in winners or m[t]<winners[label][0]):winners[label]=(float(m[t]),start+t,features[t].copy())
            for label,(_,tick,feature) in winners.items():
                identity=fi*(1<<32)+tick
                if identity in seen:continue
                if len(y)+added>=100000:raise RuntimeError('retained support limit reached; existing checkpoints preserved')
                seen.add(identity);xx.append(feature);yy.append(label);ii.append(identity);added+=1
            scanned+=len(h);errors+=count;minimum=min(minimum,case_min);case_rows.append(dict(file_index=fi,canonical_errors=count,minimum_margin=case_min))
        if xx:x=np.r_[x,np.array(xx)];y=np.r_[y,np.array(yy,dtype=np.int32)];ids=np.r_[ids,np.array(ii,dtype=np.int64)]
        write_json(folder/f'scan_{iteration:04d}.json',dict(cases=case_rows,canonical_errors=errors,minimum_margin=minimum,added=added,retained_states=len(y)))
        closed=errors==0 and minimum>=.0099 and passed(history[-1])
        if closed:success=True;value=objective(w.ravel(),x,y,prior)[0]
        else:
            solved=minimum_change(x,y,prior,.01);success=bool(solved.success)
            write_json(folder/f'solver_{iteration:04d}.json',dict(success=success,status=int(solved.status),message=str(solved.message)))
            if not success:
                status='finite_retained_constraints_infeasible' if solved.status==2 else 'solver_limit_unresolved'
                break
            w=solved.x[:prior.size].reshape(prior.shape);value=float(solved.fun)
            p[offset:-6]=w[:,:-1].ravel();p[-6:]=w[:,-1];assert np.array_equal(p[:offset],fixed)
        dl,score=evaluate(sh,p,root,profile,cw,dev_cache);row=dict(epoch=iteration,exposure_ticks=scanned,dev_loss=dl,train_loss=value,training_errors_before_fit=errors,support_errors=int((margin(x,y,w)<=0).sum()),full_pool_verified=closed,optimizer_success=success,**score)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
        if key(row)>key(best):best=row.copy()
        print(json.dumps(dict(profile=profile,seed=seed,round=iteration,training_errors=errors,support_errors=row['support_errors'],constraints=len(y),exact=score['message_accuracy'],boundary=score['boundary_errors'],closed=closed)),flush=True)
        if closed:break
    eligible=[r for r in history if r.get('full_pool_verified') and passed(r)]
    if eligible:best=max(eligible,key=key)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint);dl,score=evaluate(sh,z['p'],root,profile,cw)
    for field in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted','false_events'):assert score[field]==best[field]
    training=verify_training(sh,z['p'],paths,cache);write_json(folder/'selected_full_training_audit.json',training);startup=audit_training(sh,z['p'],root,profile,cw);write_json(folder/'selected_startup_training_audit.json',startup)
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=history[-1]['epoch'],requested_rounds=target,selected_epoch=best['epoch'],selected=best,checkpoint=str(checkpoint),class_weights=b['class_weights'],exposure_ticks=scanned,warm_start=provenance,development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status=status,scalar_replay_verified=True,selected_full_training_canonical_errors=training['canonical_errors'],selected_startup_failed_cases=startup['failed_cases'])
    write_json(result_file,result);return result


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';label='gated_linear_v13_e131_16';manifest=root/f'{label}_jobs.json'
    if manifest.exists():raise ValueError('resume original frozen batch')
    kw=json.loads((ROOT/'mixed_first_gated_candidate.json').read_text())[0];sh=make_shape(**kw);jobs=[]
    for seed in (131,):
        path=root/'models/final_portfolio_v3_first_gate_a'/sh.name/'uart_e'/str(seed)/'block_0000.json';b=json.loads(path.read_text());source=dict(block=str(path),block_sha256=digest(path),checkpoint_sha256=digest(b['checkpoint']),policy='unchanged development-selected checkpoint frozen before first_gate_full_v3a; confirmation used only to identify unresolved seed/profile, never as fitting/selection data')
        cache=root/'models/phase_gated_margin_v11'/sh.name/'uart_e'/str(seed);constraints=root/'models/phase_gated_linear_v12'/sh.name/'uart_e'/str(seed)/'epoch_0005.npz';source.update(state_cache=str(cache/'training_states'),development_cache=str(cache/'development_states'),constraints=str(constraints),constraints_sha256=digest(constraints))
        jobs.append((str(root),kw,'uart_e',seed,16,source))
    write_json(manifest,jobs);snapshot=root/'batch_sources'/label;snapshot.mkdir(parents=True)
    for p in source_files():
        q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=1) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
