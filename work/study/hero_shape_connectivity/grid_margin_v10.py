"""Fixed-state startup-grid coverage probe and bounded existing-output refinement."""
import json,hashlib,shutil,sys,time
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .readout_probe import trajectory
from .startup_grid_v10 import block,identity
from .startup_evaluate import evaluate
from .startup_margin_v5 import audit_training,passed
from .runtime import pulses
from .train import write_json,key


def fit(job):
    root,source,target=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from .hard_readout import objective,margin,minimize
    assert digest(source['block'])==source['block_sha256'];b=json.loads(Path(source['block']).read_text())
    assert digest(b['checkpoint'])==source['checkpoint_sha256'];a=dict(np.load(b['checkpoint']));sh=make_shape(**b['construction']);sh.leaks=a['leaks']
    assert not getattr(sh,'mixed',False) and not getattr(sh,'gated',False)
    recipe='phase_grid_margin_v10';folder=root/'models'/recipe/sh.name/b['profile']/str(b['seed']);folder.mkdir(parents=True,exist_ok=True)
    result_path=folder/f'block_{target:04d}.json'
    if result_path.exists():return json.loads(result_path.read_text())
    p=a['p'].copy();cw=np.array(b['class_weights']);offset=sh.parameters-6*sh.n-6;fixed=p[:offset].copy();prior=np.c_[p[offset:-6].reshape(6,sh.n),p[-6:]];w=prior.copy()
    cache=folder/'grid_states';cache.mkdir(exist_ok=True);dev_cache=folder/'development_states'
    provenance=dict(source=source,training_families=[391000000,392000000],cold_grid='32 initial idle lengths17–48 ×7 existing timing conditions ×256 first bytes; one independently seeded phase/jitter per combination',
        total_cases=57344,retained_source_support=len(a['support_y']),rounds=target,trust_bound=.25,absolute_bound=7.99,support_cap=100000,
        selection='original8864 development only; no confirmation; every prior failure/iterate kept',
        interpretation='coverage diagnostic on frozen learned states; not a physical-topology result or capacity proof')
    path=folder/'warm_start.json'
    if path.exists():assert json.loads(path.read_text())==provenance
    else:write_json(path,provenance)
    stamp=hashlib.sha256(fixed.tobytes()+sh.leaks.tobytes()).hexdigest();files=[]
    for idle in range(17,49):
        for ci in range(7):
            base=cache/f'{idle:02d}_{ci}';meta=base.with_suffix('.json');files.append(base)
            if meta.exists():assert json.loads(meta.read_text())['state_sha256']==stamp;continue
            streams=block(b['profile'],idle,ci);h=np.concatenate([trajectory(sh,p,s['x']) for s in streams]);y=np.concatenate([s['labels'] for s in streams]);ends=np.cumsum([len(s['labels']) for s in streams])
            np.save(base.with_suffix('.npy'),h);np.savez(base.with_suffix('.npz'),labels=y,ends=ends)
            write_json(meta,dict(idle=idle,condition_index=ci,cases=256,ticks=len(y),state_sha256=stamp,data_sha256=identity(streams),state_file_sha256=digest(base.with_suffix('.npy'))))
        print(json.dumps(dict(profile=b['profile'],seed=b['seed'],grid_idle_completed=idle)),flush=True)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else []
    x=a['support_x'].copy();y=a['support_y'].copy();ids=np.empty(0,dtype=np.int64);last=scanned=0
    def save(epoch):
        meta=json.loads(str(a['metadata']));meta.update(recipe=recipe,epoch=epoch,step=0,exposure=scanned)
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'m':np.zeros_like(p),'v':np.zeros_like(p),'metadata':json.dumps(meta),'support_x':x,'support_y':y,'support_ids':ids,'w':w,'scan_ticks':scanned})
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];w=z['w'];x=z['support_x'];y=z['support_y'];ids=z['support_ids'];scanned=int(z['scan_ticks'])
    else:
        dl,score=evaluate(sh,p,root,b['profile'],cw,dev_cache);history=[dict(epoch=0,exposure_ticks=0,dev_loss=dl,**score)];save(0)
        with journal.open('a') as f:f.write(json.dumps(history[0])+'\n')
    best=max(history,key=key);seen=set(ids.tolist());bounds=list(zip(np.maximum(-7.99,prior.ravel()-.25),np.minimum(7.99,prior.ravel()+.25)));status='bounded_coverage_fit_not_capacity_proof'
    for iteration in range(last+1,target+1):
        xx=[x];yy=[y];ii=[ids];errors=failed_cases=added=0
        for fi,base in enumerate(files):
            h=np.load(base.with_suffix('.npy'),mmap_mode='r');z=np.load(base.with_suffix('.npz'));labels=z['labels'];ends=z['ends'];features=np.c_[h,np.ones(len(h))];m=margin(features,labels,w)
            errors+=int((m<=0).sum());start=0
            for end in ends:
                failed_cases+=bool(np.any(m[start:end]<=0));start=end
            new=[int(t) for t in np.flatnonzero(m<.75) if fi*(1<<32)+int(t) not in seen]
            if len(y)+added+len(new)>100000:status='retained_support_limit_not_capacity_proof';break
            take=np.array(new,dtype=np.int64);new_ids=fi*(1<<32)+take;seen.update(new_ids.tolist());xx.append(features[take]);yy.append(labels[take]);ii.append(new_ids);added+=len(take);scanned+=len(labels)
        x=np.concatenate(xx);y=np.concatenate(yy);ids=np.concatenate(ii)
        write_json(folder/f'scan_{iteration:04d}.json',dict(canonical_errors=errors,canonical_failed_cases=failed_cases,added=added,retained_states=len(y),scan_complete=status=='bounded_coverage_fit_not_capacity_proof'))
        if status!='bounded_coverage_fit_not_capacity_proof':break
        solved=minimize(objective,w.ravel(),args=(x,y,prior),method='L-BFGS-B',jac=True,bounds=bounds,options=dict(maxiter=500,ftol=1e-12,gtol=1e-7,maxls=40))
        assert np.isfinite(solved.x).all();w=solved.x.reshape(prior.shape);p[offset:-6]=w[:,:-1].ravel();p[-6:]=w[:,-1];assert np.array_equal(p[:offset],fixed)
        dl,score=evaluate(sh,p,root,b['profile'],cw,dev_cache);row=dict(epoch=iteration,exposure_ticks=scanned,dev_loss=dl,train_loss=float(solved.fun),support_errors=int((margin(x,y,w)<=0).sum()),optimizer_success=bool(solved.success),training_grid_errors_before=errors,**score)
        save(iteration)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
        if key(row)>key(best):best=row.copy()
        print(json.dumps(dict(profile=b['profile'],seed=b['seed'],round=iteration,grid_errors_before=errors,support_errors=row['support_errors'],exact=score['message_accuracy'],boundary=score['boundary_errors'])),flush=True)
        if errors==0 and passed(row):break
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(checkpoint);dl,score=evaluate(sh,z['p'],root,b['profile'],cw)
    for field in ('exact_messages','boundary_errors','invalid_accepted','background_accepted'):assert score[field]==best[field]
    audit=audit_training(sh,z['p'],root,b['profile'],cw);write_json(folder/'selected_training_audit.json',audit)
    chosen=np.c_[z['p'][offset:-6].reshape(6,sh.n),z['p'][-6:]];grid_rows=[]
    for base in files:
        h=np.load(base.with_suffix('.npy'),mmap_mode='r');data=np.load(base.with_suffix('.npz'));labels=data['labels'];ends=data['ends'];pred=(h@chosen[:,:-1].T+chosen[:,-1]).argmax(1);start=0;canonical=pulse_errors=boundary=failed=0
        for end in ends:
            expected=labels[start:end];actual=pulses(pred[start:end]);bad=int(np.sum(actual!=expected));pulse_errors+=bad;failed+=bool(bad)
            canonical+=int(np.sum(pred[start:end]!=expected));boundary+=int(np.sum((np.isin(actual,[3,4])|np.isin(expected,[3,4]))&(actual!=expected)));start=end
        grid_rows.append(dict(block=base.name,cases=len(ends),canonical_errors=canonical,pulse_errors=pulse_errors,pulse_mismatch_cases=failed,boundary_errors=boundary))
    write_json(folder/'selected_grid_audit.json',dict(cases=sum(r['cases'] for r in grid_rows),pulse_mismatch_cases=sum(r['pulse_mismatch_cases'] for r in grid_rows),canonical_errors=sum(r['canonical_errors'] for r in grid_rows),boundary_errors=sum(r['boundary_errors'] for r in grid_rows),blocks=grid_rows))
    result=dict(shape=sh.name,construction=b['construction'],profile=b['profile'],seed=b['seed'],recipe=recipe,epochs=target,completed_rounds=history[-1]['epoch'],selected_epoch=best['epoch'],selected=best,checkpoint=str(checkpoint),class_weights=b['class_weights'],exposure_ticks=scanned,warm_start=provenance,development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status=status,scalar_replay_verified=True,selected_training_failed_cases=audit['failed_cases'])
    write_json(result_path,result);return result


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';label='grid_margin_v10_e101_8';file=root/f'{label}_jobs.json'
    if file.exists():raise ValueError('resume the original source snapshot/job list')
    sh=make_shape(**json.loads((ROOT/'readout_dense_candidate.json').read_text())[0]);source=root/'models/phase_dense_margin_v6'/sh.name/'uart_e/101/block_0032.json';b=json.loads(source.read_text())
    record=dict(block=str(source),block_sha256=digest(source),checkpoint_sha256=digest(b['checkpoint']));jobs=[(str(root),record,8)];write_json(file,jobs)
    snapshot=root/'batch_sources'/label;snapshot.mkdir(parents=True)
    for p in ROOT.rglob('*'):
        if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
            q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    result=fit(jobs[0]);write_json(root/f'{label}_ledger.json',dict(completed=[result],total=1))
