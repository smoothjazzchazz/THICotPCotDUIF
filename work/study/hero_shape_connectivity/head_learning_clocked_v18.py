"""Supervised nonlinear-readout fitting; the recurrent backbone remains exactly fixed."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest,source_files
from .shapes import make_shape
from .readout_probe import trajectory
from .data import load,metrics
from .train import write_json,key
from .train import evaluate_stream
from .startup_margin_v5 import passed


def evaluate(shape,p,root,profile,cw,cache=None):
    stream=load(root/'data'/profile/'dev');loss,z=evaluate_stream(shape,p,stream,cw)
    return loss,metrics(stream,z.argmax(1))


def parts(shape,p):
    edge=np.flatnonzero(shape.dst>=48);w=np.zeros((16,48));w[shape.dst[edge]-48,shape.src[edge]]=p[edge]
    e=len(shape.src);return edge,w,p[e+48:e+64],p[e+64:-6].reshape(6,64),p[-6:]


def indices(shape):
    e=len(shape.src)
    return np.r_[np.flatnonzero(shape.dst>=48),np.arange(e+48,shape.parameters)].astype(int)


def logits(shape,p,x):
    edge,w,b,v,c=parts(shape,p);u=np.tanh(x@w.T+b)
    return x@v[:,:48].T+u@v[:,48:].T+c


def objective(free,shape,fixed,x,y,prior,weights):
    active=indices(shape);p=fixed.copy();p[active]=free;edge,w,b,v,c=parts(shape,p)
    u=np.tanh(x@w.T+b);z=x@v[:,:48].T+u@v[:,48:].T+c;truth=z[np.arange(len(y)),y]
    gap=np.maximum(0.,.5+z-truth[:,None]);gap[np.arange(len(y)),y]=0
    dz=2*gap*weights[:,None];dz[np.arange(len(y)),y]=-dz.sum(1)
    du=(dz@v[:,48:])*(1-u*u);dw=du.T@x;dv=np.c_[dz.T@x,dz.T@u]
    gradient=np.r_[dw[shape.dst[edge]-48,shape.src[edge]],du.sum(0),dv.ravel(),dz.sum(0)]
    delta=free-prior
    return float(np.sum(weights*np.sum(gap*gap,axis=1))+1e-6*np.sum(delta*delta)),gradient+2e-6*delta


def backbone(shape,p):
    kw=dict(code='srr',schedule='registered',sizes=(16,16,16),leaks=(1.,1.,.125),routing='port_firstlast4',feedback='both2')
    base=make_shape(**kw);base.leaks=shape.leaks[:48].copy();bp=np.zeros(base.parameters);bp[:len(base.src)]=p[:len(base.src)];bp[len(base.src):len(base.src)+48]=p[len(shape.src):len(shape.src)+48]
    stamp=hashlib.sha256(bp[:len(base.src)+48].tobytes()+base.leaks.tobytes()).hexdigest()
    return base,bp,stamp


def bank(root,profile,seed,record):
    folder=root/'head_training_clocked_v18'/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);file=folder/'samples.npz'
    b=json.loads(Path(record['block']).read_text());assert digest(record['block'])==record['block_sha256'] and digest(b['checkpoint'])==record['checkpoint_sha256']
    sh=make_shape(**b['construction']);a=np.load(b['checkpoint']);p=a['p'];sh.leaks=a['leaks'];base,bp,stamp=backbone(sh,p)
    pool=root/f'clocked_projection_v17_{profile}_pool.json';data=json.loads(pool.read_text())
    identity=dict(source=record,pool_sha256=digest(pool),backbone_sha256=stamp,selection='perfile/class16 uniform plus16 lowest source-label margins; training only; fixed48-dimensional causal states',seed=seed)
    meta=folder/'identity.json'
    if meta.exists():assert json.loads(meta.read_text())==identity
    else:write_json(meta,identity)
    if not file.exists():
        xx=[];yy=[];ids=[];ticks=0
        for fi,entry in enumerate(data['paths']):
            path=Path(entry['path']);assert digest(path)==entry['metadata_sha256'] and digest(path.with_suffix('.npz'))==entry['arrays_sha256'];s=load(path.with_suffix(''));h=trajectory(base,bp,s['x']);margin=np.empty(len(h))
            for start in range(0,len(h),8192):
                z=logits(sh,p,h[start:start+8192]);labels=s['labels'][start:start+len(z)];truth=z[np.arange(len(z)),labels].copy();z[np.arange(len(z)),labels]=-np.inf;margin[start:start+len(z)]=truth-z.max(1)
            valid=np.arange(len(h))>=s.get('startup_ambiguous_until',0);rng=np.random.default_rng([seed,fi,16061])
            for label in range(6):
                choices=np.flatnonzero(valid&(s['labels']==label))
                if not len(choices):continue
                count=min(16,len(choices));hard=choices[np.argpartition(margin[choices],count-1)[:count]];random=rng.choice(choices,count,replace=False);take=np.unique(np.r_[hard,random])
                xx.append(h[take]);yy.append(np.full(len(take),label,dtype=np.int32));ids.append(fi*(1<<32)+take)
            ticks+=len(h)
        temporary=file.with_name('samples.pending.npz');np.savez_compressed(temporary,x=np.concatenate(xx),y=np.concatenate(yy),ids=np.concatenate(ids),ticks=ticks);temporary.replace(file)
    return file,stamp


def fit(job):
    root,kw,profile,seed,target,source,teacher=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from scipy.optimize import minimize
    sh=make_shape(**kw);recipe='phase_readout_supervised_clocked_v18';folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);block=folder/f'block_{target:04d}.json'
    if block.exists():return json.loads(block.read_text())
    assert digest(source['block'])==source['block_sha256'];b=json.loads(Path(source['block']).read_text());assert digest(b['checkpoint'])==source['checkpoint_sha256'];a=dict(np.load(b['checkpoint']));p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights']);active=indices(sh);fixed=p.copy();prior=p[active].copy()
    sample_file,stamp=bank(root,profile,seed,teacher);assert backbone(sh,p)[2]==stamp,'different backbone from shared training bank';samples=np.load(sample_file);x=samples['x'];y=samples['y'];counts=np.bincount(y,minlength=6);sample_weights=1/np.maximum(1,counts[y]);sample_weights/=sample_weights.sum()
    provenance=dict(source=source,teacher_for_shared_sampling=teacher,training_bank=str(sample_file),training_bank_sha256=digest(sample_file),backbone_sha256=stamp,
        training_rows=len(y),training_ticks_scanned=int(samples['ticks']),rounds=target,iterations_per_round=80,objective='class-balanced squared multiclass margin0.5 plus1e-6 distance to starting trainable head',
        trainable='only existing hidden readout input weights/biases and six affine outputs; all48 recurrent states/proposals/leaks and physical graph remain fixed',
        conditional_stop='whole original clocked development pass and zero sampled-training canonical errors; full-pool/fresh tests still required')
    warm=folder/'warm_start.json'
    if warm.exists():assert json.loads(warm.read_text())==provenance
    else:write_json(warm,provenance)
    journal=folder/'history.jsonl';history=[json.loads(l) for l in journal.read_text().splitlines()] if journal.exists() else [];last=0;exposure=0
    def save(epoch):
        metadata=json.loads(str(a['metadata']));metadata.update(recipe=recipe,epoch=epoch,step=0,exposure=exposure)
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'metadata':json.dumps(metadata)})
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];exposure=history[-1]['exposure_ticks']
    else:
        score=b['selected'];training_errors=int((logits(sh,p,x).argmax(1)!=y).sum());row={**score,'epoch':0,'exposure_ticks':0,'sampled_training_errors':training_errors};history=[row];save(0)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    best=max(history,key=key);protected=np.ones(sh.parameters,dtype=bool);protected[active]=False
    for iteration in range(last+1,target+1):
        if passed(history[-1]) and history[-1]['sampled_training_errors']==0:break
        result=minimize(objective,p[active],args=(sh,fixed,x,y,prior,sample_weights),method='L-BFGS-B',jac=True,bounds=[(-7.99,7.99)]*len(active),options=dict(maxiter=80,ftol=1e-11,gtol=1e-7,maxls=30));assert np.isfinite(result.x).all();p[active]=result.x;assert np.array_equal(p[protected],fixed[protected]);exposure+=len(y)*int(result.nfev)
        training_errors=int((logits(sh,p,x).argmax(1)!=y).sum());dl,score=evaluate(sh,p,root,profile,cw,None);row=dict(epoch=iteration,exposure_ticks=exposure,dev_loss=dl,train_loss=float(result.fun),sampled_training_errors=training_errors,optimizer_iterations=int(result.nit),optimizer_evaluations=int(result.nfev),optimizer_message=str(result.message),**score)
        save(iteration);history.append(row)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        if key(row)>key(best):best=row.copy()
        print(json.dumps(dict(shape=sh.name,profile=profile,seed=seed,round=iteration,training_errors=training_errors,exact=score['message_accuracy'],boundary=score['boundary_errors'])),flush=True)
    checkpoint=folder/f"epoch_{best['epoch']:04d}.npz";result=dict(shape=sh.name,construction=kw,profile=profile,seed=seed,recipe=recipe,epochs=history[-1]['epoch'],requested_rounds=target,selected_epoch=best['epoch'],selected=best,checkpoint=str(checkpoint),class_weights=cw.tolist(),exposure_ticks=exposure,warm_start=provenance,development_distribution='original_matched_clocked',status='fixed_backbone_supervised_head_fit_not_capacity_proof',scalar_replay_verified=True)
    write_json(block,result);return result


def launch(root,profiles,seeds,workers,label,target=8):
    manifest=root/f'{label}_jobs.json';assert not manifest.exists(),'resume existing frozen batch';jobs=[];banks=[]
    dense_kw=json.loads((ROOT/'readout_dense_candidate.json').read_text())[0];dense_name=make_shape(**dense_kw).name
    for profile in profiles:
        for seed in seeds:
            teacher_block=root/'models/final_portfolio_v3_dense_a'/dense_name/profile/str(seed)/'block_0000.json';t=json.loads(teacher_block.read_text());teacher=dict(block=str(teacher_block),block_sha256=digest(teacher_block),checkpoint_sha256=digest(t['checkpoint']))
            banks.append((root,profile,seed,teacher))
            for cell in ('readout16_dense','readout16_fanin32_fast'):
                kw={**dense_kw,'cell':cell};sh=make_shape(**kw);source_block=root/'models/phase_readout_projection_clocked_v17'/sh.name/profile/str(seed)/'block_0001.json';b=json.loads(source_block.read_text());source=dict(block=str(source_block),block_sha256=digest(source_block),checkpoint_sha256=digest(b['checkpoint']))
                jobs.append((str(root),kw,profile,seed,target,source,teacher))
    write_json(manifest,jobs);snapshot=root/'batch_sources'/label;snapshot.mkdir(parents=True)
    for p in source_files():
        q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()});rows=[]
    # Each backbone is gathered once; paired head fits then share the same file.
    with ProcessPoolExecutor(max_workers=min(3,workers)) as pool:
        for future in as_completed([pool.submit(bank,*job) for job in banks]):
            file,stamp=future.result();print('Shared training bank ready',file,flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--profiles',default='i2c,spi0,spi1,spi2,spi3');ap.add_argument('--seeds',default='11,29,47,71,101,131');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--label',required=True);a=ap.parse_args();launch(ROOT/'runs/connectivity01',a.profiles.split(','),list(map(int,a.seeds.split(','))),a.workers,a.label)
