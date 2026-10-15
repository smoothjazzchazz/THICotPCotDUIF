"""Matched covariance projection of nonlinear readout access on fixed training states."""
import argparse,json,shutil,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest,source_files
from .shapes import make_shape,cost,specification
from .data import load
from .readout_probe import trajectory
from .startup_evaluate import evaluate
from .train import write_json,key


def remap(source,p,target):
    result=np.zeros(target.parameters);lookup={(int(s),int(d),int(t)):k for k,(s,d,t) in enumerate(zip(source.src,source.dst,source.delay))}
    for k,edge in enumerate(zip(target.src,target.dst,target.delay)):result[k]=p[lookup[tuple(map(int,edge))]]
    result[len(target.src):]=p[len(source.src):]
    return result


def fit(job):
    root,profile,seed,source_record=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from scipy.optimize import minimize
    assert digest(source_record['block'])==source_record['block_sha256'];source=json.loads(Path(source_record['block']).read_text());assert digest(source['checkpoint'])==source_record['checkpoint_sha256']
    kw=source['construction'];dense=make_shape(**kw);weights=np.load(source['checkpoint']);p=weights['p'].copy();dense.leaks=weights['leaks'].copy();cw=np.array(source['class_weights'])
    sparse_kw={**kw,'cell':'readout16_fanin32'};sparse=make_shape(**sparse_kw);sparse.leaks=dense.leaks.copy();recipe='phase_readout_projection_v14'
    experiment=root/'readout_projection_v14'/profile/str(seed);experiment.mkdir(parents=True,exist_ok=True)
    if (experiment/'result.json').exists():return json.loads((experiment/'result.json').read_text())['models']
    pool=root/('error_grid_v13_uart_e_pool.json' if profile=='uart_e' else 'closure_v6_uart_n_pool.json');record=json.loads(pool.read_text());paths=[Path(e['path']) for e in record['paths']]
    provenance=dict(source=source_record,pool=str(pool),pool_sha256=digest(pool),ridge=1e-6,
        target='source hidden preactivations on independent training states',bound=7.99,
        comparison='same source backbone/profile/seed and every training tick for both32-parent and intact48-parent projection; intact source has exactly zero residual',
        inference='same48-state backbone,16 current-sample tanh outputs, six affine logits; physical edges actually removed')
    warm=experiment/'provenance.json'
    if warm.exists():assert json.loads(warm.read_text())==provenance
    else:write_json(warm,provenance)
    covariance=experiment/'training_covariance.npz'
    if covariance.exists():a=np.load(covariance);gram=a['gram'];ticks=int(a['ticks'])
    else:
        base_kw={**kw,'cell':'plain'};base=make_shape(**base_kw);base.leaks=dense.leaks[:48].copy();bp=np.zeros(base.parameters);bp[:len(base.src)]=p[:len(base.src)];bp[len(base.src):len(base.src)+48]=p[len(dense.src):len(dense.src)+48]
        gram=np.zeros((49,49));ticks=0
        for fi,(path,entry) in enumerate(zip(paths,record['paths'])):
            assert digest(path)==entry['metadata_sha256'] and digest(path.with_suffix('.npz'))==entry['arrays_sha256']
            s=load(path.with_suffix(''));h=trajectory(base,bp,s['x'])
            if fi==0:
                hh=trajectory(dense,p,s['x'][:1024]);assert np.array_equal(h[:1024],hh[:,:48]),'backbone extraction changed states'
            for start in range(0,len(h),8192):
                x=np.c_[h[start:start+8192],np.ones(min(8192,len(h)-start))];gram+=x.T@x;ticks+=len(x)
        gram/=ticks;np.savez_compressed(covariance,gram=gram,ticks=ticks)
    teacher=np.zeros((16,49))
    for k,(s,d) in enumerate(zip(dense.src,dense.dst)):
        if d>=48:teacher[int(d)-48,int(s)]=p[k]
    teacher[:,-1]=p[len(dense.src)+48:len(dense.src)+64]
    fitted=remap(dense,p,sparse);residuals=[]
    for j,d in enumerate(range(48,64)):
        edges=np.flatnonzero(sparse.dst==d);indices=np.r_[sparse.src[edges],48].astype(int);prior=teacher[j,indices];missing=teacher[j].copy();missing[indices]=0
        g=gram[np.ix_(indices,indices)];rhs=gram[indices]@missing;matrix=g+np.eye(len(indices))*1e-6
        delta=np.linalg.solve(matrix,rhs);coefficient=prior+delta
        if np.max(np.abs(coefficient))>7.99:
            def objective(v):
                diff=v-prior
                return float(diff@matrix@diff-2*diff@rhs),2*(matrix@diff-rhs)
            result=minimize(objective,np.clip(coefficient,-7.99,7.99),jac=True,method='L-BFGS-B',bounds=[(-7.99,7.99)]*len(indices),options=dict(maxiter=2000,ftol=1e-14,gtol=1e-10));assert np.isfinite(result.x).all();coefficient=result.x
        fitted[edges]=coefficient[:-1];fitted[len(sparse.src)+d]=coefficient[-1]
        error=teacher[j].copy();error[indices]-=coefficient;residuals.append(float(error@gram@error))
    write_json(experiment/'projection.json',dict(training_ticks=ticks,preactivation_mse=residuals,max_parameter_change=float(np.max(np.abs(fitted-remap(dense,p,sparse)))),resources=[cost(dense),cost(sparse)],intact_control_residual=0.0))
    results=[]
    for sh,kwargs,options in [(dense,kw,[p]),(sparse,sparse_kw,[remap(dense,p,sparse),fitted])]:
        folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);history=[]
        write_json(folder/'warm_start.json',provenance);write_json(root/'shapes'/f'{sh.name}.json',specification(sh,kwargs))
        for epoch,parameters in enumerate(options):
            dl,score=evaluate(sh,parameters,root,profile,cw,None);row=dict(epoch=epoch,dev_loss=dl,exposure_ticks=ticks if epoch or sh is dense else 0,**score);history.append(row)
            metadata=dict(recipe=recipe,epoch=epoch,step=0,exposure=ticks,seed=seed,profile=profile)
            np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',p=parameters,leaks=sh.leaks,m=np.zeros_like(parameters),v=np.zeros_like(parameters),metadata=json.dumps(metadata))
            print(json.dumps(dict(shape=sh.name,profile=profile,seed=seed,stage='intact' if sh is dense else ('projected' if epoch else 'removed'),exact=score['message_accuracy'],boundary=score['boundary_errors'])),flush=True)
        (folder/'history.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in history));best=max(history,key=key)
        b=dict(shape=sh.name,construction=kwargs,profile=profile,seed=seed,recipe=recipe,epochs=1,selected_epoch=best['epoch'],selected=best,checkpoint=str(folder/f"epoch_{best['epoch']:04d}.npz"),class_weights=cw.tolist(),exposure_ticks=ticks,warm_start=provenance,development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',status='paired_teacher_projection_development_only',scalar_replay_verified=True)
        write_json(folder/'block_0001.json',b);results.append(b)
    write_json(experiment/'result.json',dict(profile=profile,seed=seed,models=results));return results


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=3);ap.add_argument('--seeds',default='11,29,47');ap.add_argument('--label',default='readout_projection_v14_pilot');a=ap.parse_args()
    root=ROOT/'runs/connectivity01';manifest=root/f'{a.label}_jobs.json';assert not manifest.exists(),'resume original frozen batch'
    kw=json.loads((ROOT/'readout_dense_candidate.json').read_text())[0];name=make_shape(**kw).name;jobs=[]
    for profile in ('uart_n','uart_e'):
        for seed in map(int,a.seeds.split(',')):
            block=root/'models/final_portfolio_v3_dense_a'/name/profile/str(seed)/'block_0000.json';b=json.loads(block.read_text());source=dict(block=str(block),block_sha256=digest(block),checkpoint_sha256=digest(b['checkpoint']))
            jobs.append((str(root),profile,seed,source))
    write_json(manifest,jobs);snapshot=root/'batch_sources'/a.label;snapshot.mkdir(parents=True)
    for p in source_files():
        target=snapshot/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    write_json(root/f'{a.label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()});rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{a.label}_ledger.json',dict(completed=rows,total=len(jobs)))
