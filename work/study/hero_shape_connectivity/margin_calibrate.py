"""Training-only scalar STOP-bias calibration, preserving every state-transition weight."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import shutil
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .data import load
from .train import evaluate_stream,write_json,key
from .precision_data import evaluate

RECIPES=('phase_precision_v2','phase_precision_readout_v2','phase_coverage_v3','phase_native_v3','phase_native_refine_v3','phase_error_mining_v3')


def allowed_interval(lower,upper,forbidden):
    cursor=lower;available=[]
    for lo,hi in sorted((max(lower,lo),min(upper,hi)) for lo,hi in forbidden if lo<upper and hi>lower):
        if lo>cursor:available.append((cursor,lo))
        cursor=max(cursor,hi)
    if cursor<upper:available.append((cursor,upper))
    return available


def source(root,kw,profile,seed):
    sh=make_shape(**kw);options=[]
    for recipe in RECIPES:
        blocks=sorted((root/'models'/recipe/sh.name/profile/str(seed)).glob('block_*.json'))
        if blocks:
            b=json.loads(blocks[-1].read_text())
            if b.get('development_distribution')!='precision_v2':continue
            options.append((blocks[-1],b))
    if not options:raise ValueError('no verified source')
    path,b=max(options,key=lambda item:key(item[1]['selected']))
    return path,b,options


def fit(job):
    root,kw,profile,seed=job[:4];options=job[4] if len(job)>4 else {};recipe=options.get('recipe','phase_margin_calibration_v3')
    root=Path(root);sh=make_shape(**kw);folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    if (folder/'block_0001.json').exists():return json.loads((folder/'block_0001.json').read_text())
    if (folder/'warm_start.json').exists():
        provenance=json.loads((folder/'warm_start.json').read_text());b=json.loads(Path(provenance['source_block']).read_text())
    else:
        if 'source_block' in options:
            path=Path(options['source_block']);b=json.loads(path.read_text());source_options=[(path,b)]
        else:path,b,source_options=source(root,kw,profile,seed)
        provenance=dict(source_block=str(path),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
            candidates=[dict(block=str(path),checkpoint=x['checkpoint'],checkpoint_sha256=digest(x['checkpoint']),selected=x['selected'],recipe=x['recipe'],exposure_ticks=x['exposure_ticks'],warm_start=x.get('warm_start')) for path,x in source_options],
            source_provenance=b.get('warm_start'),selection='same verified-development key; proposed scalar bias is trained without development examples')
        write_json(folder/'warm_start.json',provenance)
    a=dict(np.load(b['checkpoint']));p=a['p'].copy();original=p.copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights'])
    s=b['selected'];passed=s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
    paths=[];lower=-7.99-p[-2];upper=7.99-p[-2];forbidden=[];ticks=0;constraints=0;files=[];offset=0.;intervals=[]
    if not passed:
        paths+=sorted((root/'data_precision_v2'/profile/'train').glob('cold_*.json'))
        paths+=sorted((root/'data_startup_modes'/profile).glob('*.json'))
        paths+=[root/'data_precision_v2'/profile/'train'/f'long_{i:04d}.json' for i in range(181,188)]
        for path in paths:
            data=load(path.with_suffix(''));_,z=evaluate_stream(sh,p,data,cw);tau=np.max(np.delete(z,4,axis=1),axis=1)-z[:,4];previous=np.r_[np.inf,tau[:-1]]
            scored=np.arange(len(tau))>=data.get('startup_ambiguous_until',0);true=(data['labels']==4)&scored;false=(data['labels']!=4)&scored&(tau<previous)
            ticks+=len(tau);constraints+=int(true.sum())
            if true.any():lower=max(lower,float(np.max(tau[true])));upper=min(upper,float(np.min(previous[true])))
            forbidden.extend(zip(tau[false].tolist(),previous[false].tolist()))
            files.append(dict(path=str(path),metadata_sha256=digest(path),arrays_sha256=digest(path.with_suffix('.npz'))))
        intervals=allowed_interval(lower,upper,forbidden) if lower<upper else []
        if intervals:
            lo,hi=max(intervals,key=lambda pair:pair[1]-pair[0]);offset=(lo+hi)/2;p[-2]+=offset
    diagnostic=dict(already_passed=passed,training_ticks=ticks,true_stop_constraints=constraints,false_onset_intervals=len(forbidden),
        required_interval=[lower,upper],available_intervals=intervals,chosen_offset=offset,training_files=files,
        objective='midpoint of widest feasible training STOP-onset bias interval; no recurrent update',
        limitation='other event classes and message assembly must still pass full development and fresh confirmation')
    write_json(folder/'calibration.json',diagnostic)
    # Keep both proposals and the complete originating checkpoint; only the bias differs.
    for epoch,parameters in ((0,original),(1,p)):
        data={**a,'p':parameters};np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**data)
    state_same=np.array_equal(original[:-6],p[:-6]);assert state_same
    if passed or offset==0:score=s.copy()
    else:
        dl,score=evaluate(sh,p,root,profile,cw,'data_precision_v2');score['dev_loss']=dl
    use_new=key(score)>key(s);selected=score if use_new else s;epoch=int(use_new)
    checkpoint=folder/f'epoch_{epoch:04d}.npz';np.savez_compressed(folder/'selected.npz',p=p if use_new else original,leaks=sh.leaks)
    result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=1,
        selected_epoch=epoch,selected=selected,proposal_score=score,checkpoint=str(checkpoint),class_weights=cw.tolist(),
        exposure_ticks=ticks,status='training_only_bias_calibration_not_capacity_proof',warm_start=provenance,
        development_distribution='precision_v2',state_transition_bitwise_unchanged=state_same,calibration=diagnostic)
    write_json(folder/'block_0001.json',result)
    print(json.dumps(dict(profile=profile,seed=seed,offset=offset,intervals=intervals,selected_epoch=epoch,exact=selected['message_accuracy'],boundary=selected['boundary_errors'])),flush=True)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);ap.add_argument('--profiles',default='uart_n,uart_e');a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];jobs=[(str(root),kw,p,s) for p in a.profiles.split(',') for s in SEEDS];label='margin_calibration_v3'
    write_json(root/f'{label}_jobs.json',jobs);snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):
            rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
