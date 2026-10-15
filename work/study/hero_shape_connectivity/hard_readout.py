"""Convex margin fitting on fixed causal states; training-only error mining."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
from pathlib import Path
import shutil
import sys
import numpy as np
from .run import ROOT,digest
sys.path.insert(0,str(ROOT/'runs'/'connectivity01'/'dependencies'))
from scipy.optimize import minimize
from .readout_probe import trajectory
from .shapes import make_shape,SEEDS
from .data import load,metrics
from .train import write_json,evaluate_stream


def objective(flat,x,y,prior):
    if len(y)==0:
        delta=flat.reshape(prior.shape)-prior
        return float(1e-6*np.sum(delta*delta)),(2e-6*delta).ravel()
    w=flat.reshape(prior.shape);z=x@w.T;target=z[np.arange(len(y)),y]
    gap=np.maximum(0.,.5+z-target[:,None]);gap[np.arange(len(y)),y]=0
    delta=w-prior;loss=float(np.mean(np.sum(gap*gap,axis=1))+1e-6*np.sum(delta*delta))
    dz=2*gap/len(y);dz[np.arange(len(y)),y]=-dz.sum(1)
    gradient=dz.T@x+2e-6*delta
    return loss,gradient.ravel()


def margin(x,y,w):
    z=x@w.T;target=z[np.arange(len(y)),y];z[np.arange(len(y)),y]=-np.inf
    return target-z.max(1)


def score_key(r):
    return (min(c['message_accuracy'] for c in r['conditions']),r['exact_messages']/r['valid_messages'],
        -r['boundary_errors'],-r['invalid_accepted']-r['background_accepted'],-r['false_events'])


def evaluate(sh,p,root,profile,cache):
    rows=[];offset=len(sh.src)+sh.n;w=p[offset:offset+6*sh.n].reshape(6,sh.n);bias=p[-6:]
    for base in sorted((root/'data_precision'/profile/'dev').glob('*.json')):
        s=load(base.with_suffix(''));path=cache/(base.stem+'.npy')
        if not path.exists():np.save(path,trajectory(sh,p,s['x']))
        h=np.load(path,mmap_mode='r');pred=np.empty(len(h),dtype=np.int32)
        for start in range(0,len(h),8192):pred[start:start+8192]=(h[start:start+8192]@w.T+bias).argmax(1)
        r=metrics(s,pred);r['case']=base.stem;rows.append(r)
    fields=('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted','false_events','missed_events')
    total={k:sum(r[k] for r in rows) for k in fields};total['conditions']=rows
    total['message_accuracy']=total['exact_messages']/total['valid_messages'];return total


def fit(job):
    kwargs,profile,seed,rounds=job;root=ROOT/'runs'/'connectivity01';sh=make_shape(**kwargs)
    folder=root/'hard_readout'/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    cache=folder/'development_states';cache.mkdir(exist_ok=True)
    source=root/'models'/'phase_recovery_readout'/sh.name/profile/str(seed)
    block=sorted(source.glob('block_*.json'))[-1];b=json.loads(block.read_text());a=np.load(b['checkpoint']);p=a['p'].copy();sh.leaks=a['leaks'].copy()
    offset=len(sh.src)+sh.n;prior=np.c_[p[offset:offset+6*sh.n].reshape(6,sh.n),p[-6:]]
    manifest=dict(source_block=str(block),source_checkpoint=b['checkpoint'],source_sha256=digest(b['checkpoint']),
        objective='squared multiclass margin 0.5 plus 1e-6 squared distance to starting readout',
        fixed='all recurrent/input/routing/bias parameters and leaks; only the six existing affine outputs are fitted',
        scipy_version=__import__('scipy').__version__,numpy_version=np.__version__,source_hashes={n:digest(ROOT/n) for n in ('hard_readout.py','precision_data.py','state_kernel.cpp')})
    if (folder/'manifest.json').exists():
        if json.loads((folder/'manifest.json').read_text())!=manifest:raise ValueError('hard-readout source differs')
    else:
        write_json(folder/'manifest.json',manifest)
        for name in manifest['source_hashes']:shutil.copy2(ROOT/name,folder/name)
    journal=folder/'history.jsonl';history=[json.loads(s) for s in journal.read_text().splitlines()] if journal.exists() else []
    if history:
        last=history[-1]['round'];resume=np.load(folder/f'round_{last:04d}.npz');w=resume['w'];x=resume['support_x'];y=resume['support_y'];exposure=int(resume['exposure'])
    else:
        last=0;w=prior.copy();x=np.empty((0,sh.n+1));y=np.empty(0,dtype=np.int32);exposure=0
        row=dict(round=0,exposure_ticks=0,development=evaluate(sh,p,root,profile,cache));history=[row]
        np.savez_compressed(folder/'round_0000.npz',p=p,leaks=sh.leaks,w=w,support_x=x,support_y=y,exposure=exposure)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    best=max(history,key=lambda r:score_key(r['development']))
    for iteration in range(last+1,rounds+1):
        paths=[root/'data_fresh'/profile/f'epoch_{iteration:04d}',root/'data_recovery'/profile/f'epoch_{2*((iteration-1)%30)+1:04d}']
        paths.extend(root/'data_precision'/profile/'train'/f'cold_{i:03d}' for i in ((np.arange(16)+(iteration-1)*16)%256))
        candidates=[x];targets=[y];mistakes=0
        for path in paths:
            s=load(path);h=trajectory(sh,p,s['x']);xx=np.c_[h,np.ones(len(h))];yy=s['labels'];m=margin(xx,yy,w)
            exposure+=len(yy);mistakes+=int((m<=0).sum());indices=np.flatnonzero(m<.75)
            if len(indices)>16000:indices=indices[np.argpartition(m[indices],16000)[:16000]]
            candidates.append(xx[indices]);targets.append(yy[indices])
        x=np.concatenate(candidates);y=np.concatenate(targets);m=margin(x,y,w)
        if len(y)>100000:
            keep=np.argpartition(m,100000)[:100000];x=x[keep];y=y[keep]
        result=minimize(objective,w.ravel(),args=(x,y,prior),method='L-BFGS-B',jac=True,bounds=[(-7.99,7.99)]*w.size,
            options=dict(maxiter=150,ftol=1e-12,gtol=1e-7,maxls=40))
        w=result.x.reshape(prior.shape);p[offset:offset+6*sh.n]=w[:,:-1].ravel();p[-6:]=w[:,-1]
        row=dict(round=iteration,exposure_ticks=exposure,training_misclassifications_before_fit=mistakes,
            retained_training_states=len(y),optimizer_success=bool(result.success),optimizer_message=str(result.message),
            objective=float(result.fun),solver_iterations=int(result.nit),support_misclassifications=int((margin(x,y,w)<=0).sum()),
            development=evaluate(sh,p,root,profile,cache))
        if score_key(row['development'])>score_key(best['development']):best=row.copy()
        np.savez_compressed(folder/f'round_{iteration:04d}.npz',p=p,leaks=sh.leaks,w=w,support_x=x,support_y=y,exposure=exposure)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        print(json.dumps(dict(profile=profile,seed=seed,round=iteration,exact=row['development']['message_accuracy'],boundary=row['development']['boundary_errors'],support_errors=row['support_misclassifications'])),flush=True)
    selected=folder/f"round_{best['round']:04d}.npz";a=np.load(selected);p=a['p']
    # Verify the selected BLAS-readout classification using deployed scalar inference.
    scalar=[]
    for base in sorted((root/'data_precision'/profile/'dev').glob('*.json')):
        s=load(base.with_suffix(''));_,z=evaluate_stream(sh,p,s,np.ones(6));r=metrics(s,z.argmax(1));r['case']=base.stem;scalar.append(r)
    if [(r['case'],r['exact_messages'],r['boundary_errors']) for r in scalar]!=[(r['case'],r['exact_messages'],r['boundary_errors']) for r in best['development']['conditions']]:raise AssertionError('BLAS and deployed readout differ')
    write_json(folder/f'block_{rounds:04d}.json',dict(shape=sh.name,construction=kwargs,profile=profile,seed=seed,rounds=rounds,selected=best,
        checkpoint=str(selected),source_block=str(block),exposure_ticks=exposure,development_distribution='precision',qualification=False,scalar_replay_verified=True))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--rounds',type=int,default=20);ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    kwargs=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0]
    jobs=[(kwargs,profile,seed,a.rounds) for profile in ('uart_n','uart_e') for seed in SEEDS]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):f.result()
