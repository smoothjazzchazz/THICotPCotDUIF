"""Independent continuous-pause coverage and fixed-state output closure."""
import argparse,json,shutil,sys,hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest,source_files
from .data import build,save,load,metrics
from .shapes import make_shape,SEEDS
from .startup_audit import mismatches
from .readout_probe import trajectory
from .train import write_json,key,evaluate_stream
from .startup_margin_v5 import passed


def generate(root,profile):
    folder=root/'data_clocked_pause_v20'/profile;pi=int(profile[-1]);training=[];development=[]
    for split,count,family in [('train_pause',32,411000000),('train_mixed',8,411050000),('dev_pause',8,413000000)]:
        for index in range(count):
            path=folder/split/f'{index:03d}'
            if not path.with_suffix('.json').exists():
                stream=build(profile,family+pi*100000+index*100,condition='pauses' if split.endswith('pause') else None,messages=128 if split.endswith('pause') else 64)
                assert not mismatches(stream);save(path,stream)
            stream=load(path);assert not mismatches(stream)
            (development if split=='dev_pause' else training).append(path)
    old=json.loads((root/f'clocked_projection_v17_{profile}_pool.json').read_text())
    training=[Path(e['path']).with_suffix('') for e in old['paths']]+training
    development=[root/'data'/profile/'dev']+development
    records=lambda paths:[dict(path=str(p),metadata_sha256=digest(p.with_suffix('.json')),arrays_sha256=digest(p.with_suffix('.npz'))) for p in paths]
    result=dict(profile=profile,training=records(training),development=records(development),training_families=[411000000,411050000],development_family=413000000,
                contract='all prior fourteen corpora plus4096 pause and512 mixed messages; development adds1024 independent pause messages; no confirmation data')
    path=folder/'manifest.json'
    if path.exists():assert json.loads(path.read_text())==result
    else:write_json(path,result)
    return path


def streams(records):
    for entry in records:
        path=Path(entry['path']);assert digest(path.with_suffix('.json'))==entry['metadata_sha256'] and digest(path.with_suffix('.npz'))==entry['arrays_sha256']
        yield path,load(path)


def evaluate(sh,p,records,cw):
    rows=[];loss=ticks=0
    for path,s in streams(records):
        value,z=evaluate_stream(sh,p,s,cw);r=metrics(s,z.argmax(1));r['case']=str(path);rows.append(r);loss+=value*len(z);ticks+=len(z)
    fields=('exact_messages','valid_messages','byte_exact_messages','boundary_errors','invalid_accepted','background_accepted','false_events','missed_events')
    total={k:sum(r[k] for r in rows) for k in fields};by={}
    for row in rows:
        for condition,c in row['conditions'].items():
            v=by.setdefault(condition,dict(exact_messages=0,valid_messages=0,byte_exact_messages=0))
            for k in v:v[k]+=c[k]
    for v in by.values():v['message_accuracy']=v['exact_messages']/v['valid_messages']
    total.update(message_accuracy=total['exact_messages']/total['valid_messages'],conditions=by,cases=rows)
    return loss/ticks,total


def fit(job):
    root,source,target=job;root=Path(root);sys.path.insert(0,str(root/'dependencies'))
    from .hard_readout import objective,margin,minimize
    assert digest(source['block'])==source['block_sha256'];b=json.loads(Path(source['block']).read_text());assert digest(b['checkpoint'])==source['checkpoint_sha256']
    sh=make_shape(**b['construction']);a=dict(np.load(b['checkpoint']));p=a['p'].copy();sh.leaks=a['leaks'].copy();cw=np.array(b['class_weights'])
    recipe='phase_clocked_pause_v20';folder=root/'models'/recipe/sh.name/b['profile']/str(b['seed']);folder.mkdir(parents=True,exist_ok=True);result_path=folder/f'block_{target:04d}.json'
    if result_path.exists():return json.loads(result_path.read_text())
    manifest=root/'data_clocked_pause_v20'/b['profile']/'manifest.json';data=json.loads(manifest.read_text())
    offset=sh.parameters-6*sh.n-6;fixed=p[:offset].copy();prior=np.c_[p[offset:-6].reshape(6,sh.n),p[-6:]];w=prior.copy();cache=folder/'training_states';cache.mkdir(exist_ok=True)
    stamp=hashlib.sha256(fixed.tobytes()+sh.leaks.tobytes()).hexdigest()
    provenance=dict(source=source,data_manifest=str(manifest),data_manifest_sha256=digest(manifest),fixed_state_sha256=stamp,
                    trainable='six existing affine output rows only; all backbone/hidden weights, biases and leaks fixed',trust_bound=.5,absolute_bound=7.99,
                    maximum_rounds=target,retained_state_cap=250000,selection='full expanded development first; prefer full training-label closure among whole-development passes; then original development key',
                    matching='same full independent waveform pool, six seeds and conditional stopping rule for dense/reduced; actual exposure reported')
    warm=folder/'warm_start.json'
    if warm.exists():assert json.loads(warm.read_text())==provenance
    else:write_json(warm,provenance)
    journal=folder/'history.jsonl';history=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    x=np.empty((0,sh.n+1));y=np.empty(0,dtype=np.int32);ids=np.empty(0,dtype=np.int64);exposure=0;last=0
    def checkpoint(epoch):
        meta=json.loads(str(a['metadata']));meta.update(recipe=recipe,epoch=epoch,step=0,exposure=exposure)
        np.savez_compressed(folder/f'epoch_{epoch:04d}.npz',**{**a,'p':p,'metadata':json.dumps(meta),'support_x':x,'support_y':y,'support_ids':ids,'exposure':exposure})
    if history:
        last=history[-1]['epoch'];z=np.load(folder/f'epoch_{last:04d}.npz');p=z['p'];w=np.c_[p[offset:-6].reshape(6,sh.n),p[-6:]];x=z['support_x'];y=z['support_y'];ids=z['support_ids'];exposure=int(z['exposure'])
    else:
        dl,s=evaluate(sh,p,data['development'],cw);history=[dict(epoch=0,exposure_ticks=0,dev_loss=dl,**s)];checkpoint(0)
        with journal.open('a') as f:f.write(json.dumps(history[0])+'\n')
    seen=set(ids.tolist());bounds=list(zip(np.maximum(-7.99,prior.ravel()-.5),np.minimum(7.99,prior.ravel()+.5)));status='bounded_pause_fit_not_capacity_proof';audits={}
    def scan(epoch,collect):
        nonlocal exposure
        xx=[x];yy=[y];ii=[ids];errors=added=0;case_rows=[]
        for fi,(path,s) in enumerate(streams(data['training'])):
            target_file=cache/f'{fi:03d}.npy';meta=cache/f'{fi:03d}.json'
            if target_file.exists():assert json.loads(meta.read_text())['state_sha256']==stamp
            else:
                h=trajectory(sh,p,s['x']);np.save(target_file,h);write_json(meta,dict(state_sha256=stamp,source=data['training'][fi],state_file_sha256=digest(target_file)))
            h=np.load(target_file,mmap_mode='r');features=np.c_[h,np.ones(len(h))];labels=s['labels'];m=margin(features,labels,w);errors+=int((m<=0).sum());exposure+=len(labels)
            case_rows.append(dict(case=str(path),canonical_errors=int((m<=0).sum()),ticks=len(labels)))
            if collect:
                take=[]
                for label in range(6):
                    choices=np.flatnonzero((labels==label)&(m<.75));count=min(256,len(choices))
                    if count:
                        chosen=choices[np.argpartition(m[choices],count-1)[:count]]
                        take.extend(int(t) for t in chosen if fi*(1<<32)+int(t) not in seen)
                if len(y)+added+len(take)>250000:raise RuntimeError('retained support limit; preserve checkpoint and choose next hypothesis')
                take=np.array(take,dtype=np.int64);new_ids=fi*(1<<32)+take;seen.update(new_ids.tolist());xx.append(features[take]);yy.append(labels[take]);ii.append(new_ids);added+=len(take)
        audit=dict(epoch=epoch,canonical_errors=errors,ticks=sum(c['ticks'] for c in case_rows),cases=case_rows,added=added)
        write_json(folder/f'training_scan_{epoch:04d}.json',audit);audits[epoch]=audit
        return np.concatenate(xx),np.concatenate(yy),np.concatenate(ii),audit
    for iteration in range(last,target+1):
        x,y,ids,audit=scan(iteration,True)
        current=history[-1]
        print(json.dumps(dict(shape=sh.name,profile=b['profile'],seed=b['seed'],round=iteration,training_errors=audit['canonical_errors'],exact=current['message_accuracy'],boundary=current['boundary_errors'])),flush=True)
        if audit['canonical_errors']==0 and passed(current):status='complete_training_label_and_expanded_development_closure';break
        if iteration==target:break
        solved=minimize(objective,w.ravel(),args=(x,y,prior),jac=True,method='L-BFGS-B',bounds=bounds,options=dict(maxiter=500,ftol=1e-12,gtol=1e-7,maxls=40));assert np.isfinite(solved.x).all()
        w=solved.x.reshape(prior.shape);p[offset:-6]=w[:,:-1].ravel();p[-6:]=w[:,-1];assert np.array_equal(p[:offset],fixed)
        dl,s=evaluate(sh,p,data['development'],cw);row=dict(epoch=iteration+1,exposure_ticks=exposure,dev_loss=dl,train_loss=float(solved.fun),support_errors=int((margin(x,y,w)<=0).sum()),optimizer_iterations=int(solved.nit),optimizer_success=bool(solved.success),**s)
        checkpoint(iteration+1);history.append(row)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
    for h in history:
        f=folder/f"training_scan_{h['epoch']:04d}.json"
        if f.exists():audits[h['epoch']]=json.loads(f.read_text())
    ready=[h for h in history if passed(h) and audits.get(h['epoch'],{}).get('canonical_errors')==0]
    best=max(ready or history,key=key);selected=folder/f"epoch_{best['epoch']:04d}.npz";z=np.load(selected);dl,s=evaluate(sh,z['p'],data['development'],cw)
    for field in ('exact_messages','boundary_errors','invalid_accepted','background_accepted'):assert s[field]==best[field]
    result=dict(shape=sh.name,construction=b['construction'],profile=b['profile'],seed=b['seed'],recipe=recipe,epochs=history[-1]['epoch'],selected_epoch=best['epoch'],selected=best,checkpoint=str(selected),class_weights=b['class_weights'],exposure_ticks=exposure,warm_start=provenance,
                development_distribution='original_plus_clocked_pause_v20',status=status,scalar_replay_verified=True,selected_training_scan=audits.get(best['epoch']),full_training_closure=bool(ready))
    write_json(result_path,result);return result


def launch(profiles,seeds,workers,label):
    root=ROOT/'runs/connectivity01';manifest=root/f'{label}_jobs.json';assert not manifest.exists(),'resume immutable original batch';jobs=[]
    for profile in profiles:generate(root,profile)
    for kw in json.loads((ROOT/'readout_cost_pair_v3_candidates.json').read_text()):
        name=make_shape(**kw).name
        for profile in profiles:
            for seed in seeds:
                source=root/'models/final_portfolio_v3_readout_cost_a'/name/profile/str(seed)/'block_0000.json';b=json.loads(source.read_text())
                jobs.append((str(root),dict(block=str(source),block_sha256=digest(source),checkpoint_sha256=digest(b['checkpoint'])),12))
    write_json(manifest,jobs);snapshot=root/'batch_sources'/label;snapshot.mkdir(parents=True)
    for p in source_files():
        q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()});rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--profiles',default='spi1,spi2');ap.add_argument('--seeds',default='11,29,47,71,101,131');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--label',required=True);args=ap.parse_args()
    launch(args.profiles.split(','),list(map(int,args.seeds.split(','))),args.workers,args.label)
