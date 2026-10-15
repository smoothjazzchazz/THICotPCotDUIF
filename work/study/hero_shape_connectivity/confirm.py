"""Immutable comparison snapshots with disjoint confirmation seed families."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
from pathlib import Path
import shutil
import numpy as np
from .shapes import make_shape,features,SEEDS,PROFILES,specification
from .runtime import run,Receiver,pulses,events
from .vendor.data import Builder,reference_labels,assemble,score
from .data import save,load,conditions
from .train import write_json
from .run import digest,ROOT,source_files


def freeze(root,label,candidates,seed_family,recipe='matched',profiles=PROFILES):
    out=root/'confirmations'/label
    if out.exists():raise ValueError('confirmation already exists; choose a fresh label')
    # Check prerequisites before making a partial snapshot.
    entries=[]
    for kwargs in candidates:
        sh=make_shape(**kwargs)
        for profile in profiles:
            for seed in SEEDS:
                active_recipe=recipe[profile] if isinstance(recipe,dict) else recipe
                folder=root/'models'/active_recipe/sh.name/profile/str(seed)
                paths=sorted(folder.glob('block_*.json'))
                if not paths:raise ValueError(('missing six-seed trained model',sh.name,profile,seed))
                row=json.loads(paths[-1].read_text())
                entries.append(dict(shape=sh.name,construction=kwargs,profile=profile,seed=seed,
                    checkpoint=row['checkpoint'],selected_epoch=row['selected_epoch'],epochs=row['epochs'],
                    development=row['selected'],development_distribution=row.get('development_distribution','original'),recipe=active_recipe))
    out.mkdir(parents=True)
    for e in entries:
        path=out/'weights'/e['shape']/e['profile']/f"{e['seed']}.npz";path.parent.mkdir(parents=True,exist_ok=True)
        source_checkpoint=np.load(e['checkpoint'],allow_pickle=False);p=source_checkpoint['p']
        leaks=source_checkpoint['leaks'] if 'leaks' in source_checkpoint else make_shape(**e['construction']).leaks
        np.savez_compressed(path,p=p,leaks=leaks);e['configured_leaks']=leaks.tolist()
        e['weight_path']=str(path.relative_to(out));e['weight_sha256']=digest(path)
    source=out/'source'
    for p in source_files():
        q=source/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(out/'freeze.json',dict(entries=entries,seed_family=seed_family,candidates=candidates,profiles=list(profiles),
        source_hashes={str(p.relative_to(source)):digest(p) for p in source.rglob('*') if p.is_file()},
        threshold='all exact messages and boundaries; zero accepted invalid/background; five of six seeds each profile',
        meaningful_threshold='README.md unchanged; partial-profile result never establishes a qualifying shape',
        data_generated_after_freeze=True))
    return out


def generate(out):
    config=json.loads((out/'freeze.json').read_text());family=config['seed_family'];manifest=[]
    folder=out/'data';folder.mkdir(exist_ok=True)
    for pi,profile in enumerate(config['profiles']):
        for ci,condition in enumerate(conditions(profile)):
            name=f'{profile}_{condition}';base=folder/name
            if not base.with_suffix('.json').exists():
                b=Builder(profile,family+pi*100000+ci*1000)
                for i in range(1000):
                    if i==0:payload=b.rng.integers(0,256,1024).tolist()
                    elif i==1:payload=list(range(256))
                    elif i<6:payload=[(0,255,85,170)[i-2]]*64
                    elif i%100==0:payload=b.rng.integers(0,256,128).tolist()
                    else:payload=b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist()
                    if condition=='address_nack':payload=[]
                    b.message(payload,condition)
                s=b.finish();s['x']=features(s['lines'])[0];s['seed']=family+pi*100000+ci*1000;save(base,s)
            manifest.append(dict(name=name,profile=profile,condition=condition,kind='valid',required_messages=1000))
        name=f'{profile}_invalid_recovery';base=folder/name
        if not base.with_suffix('.json').exists():
            b=Builder(profile,family+2000000+pi*100000)
            errors=['framing','break']+(['parity'] if profile=='uart_e' else []) if profile.startswith('uart') else ['partial']
            for i in range(100):
                b.message([int(b.rng.integers(0,256))],invalid=errors[i%len(errors)])
                b.message(b.rng.integers(0,256,4).tolist())
                if i%10==0:b.idle(4096)
            s=b.finish();s['x']=features(s['lines'])[0];save(base,s)
        manifest.append(dict(name=name,profile=profile,condition='invalid_recovery',kind='invalid_recovery',required_messages=100))
        name=f'{profile}_midstream';base=folder/name
        if not base.with_suffix('.json').exists():
            b=Builder(profile,family+4000000+pi*100000)
            for i in range(101):b.message(b.rng.integers(0,256,4).tolist())
            s=b.finish();cut=s['groups'][0]['start']+37;lines=s['lines'][cut:]
            labels=reference_labels(lines,profile);truth,rejections=assemble(events(labels),profile)
            groups=[{**g,'start':g['start']-cut,'end':g['end']-cut} for g in s['groups'][1:]]
            s=dict(lines=lines,labels=labels,truth=truth,groups=groups,profile=profile,reference_rejections=rejections,
                startup_ambiguous_until=groups[0]['start'],x=features(lines)[0]);save(base,s)
        manifest.append(dict(name=name,profile=profile,condition='midstream',kind='startup_recovery',required_messages=100))
        print('fresh confirmation generated',profile,flush=True)
    write_json(folder/'manifest.json',manifest)
    write_json(out/'data_hashes.json',{str(p.relative_to(folder)):digest(p) for p in folder.iterdir() if p.is_file()})


def infer(sh,p,x,quantize=False):
    state=np.zeros(sh.n);pred=np.empty(len(x),dtype=np.int32)
    for t in range(0,len(x),8192):
        _,state,z,_,_=run(sh,p,x[t:t+8192],h=state,quantize=quantize);pred[t:t+8192]=z.argmax(1)
    return pred


def remove_feedback(sh,p):
    """A post-fit feedforward control; leaks and input-age features remain."""
    p=p.copy();group={i:g for g,nodes in enumerate(sh.groups) for i in nodes}
    removed=[k for k,(s,d) in enumerate(zip(sh.src,sh.dst)) if s>=0 and group[int(s)]>=group[int(d)]]
    if getattr(sh,'mixed',False):
        # All gate inputs read prior states, including self and returning rings.
        offset=len(sh.src)+sh.n;removed.extend(range(offset,offset+len(sh.gate_src)))
    elif getattr(sh,'gated',False):
        raise ValueError('the all-gated parameter layout requires its own audited control')
    p[removed]=0
    return p,removed


def evaluate_job(job):
    out,e,arithmetic=job;out=Path(out);sh=make_shape(**e['construction'])
    folder=out/'results'/sh.name/e['profile']/f"{arithmetic}_{e['seed']}";folder.mkdir(parents=True,exist_ok=True)
    if (folder/'summary.json').exists():return json.loads((folder/'summary.json').read_text())
    path=out/e['weight_path']
    if digest(path)!=e['weight_sha256']:raise AssertionError('frozen weights changed')
    model=np.load(path,allow_pickle=False);p=model['p'];q=arithmetic=='quantized'
    if 'leaks' in model:sh.leaks=model['leaks'].copy()
    if q:p=np.rint(p*4096)/4096
    if arithmetic=='no_recurrence':
        group={i:g for g,nodes in enumerate(sh.groups) for i in nodes}
        for k,(s,d) in enumerate(zip(sh.src,sh.dst)):
            if s>=0 and group[int(s)]==group[int(d)]:p[k]=0
    if arithmetic=='no_feedback':
        p,removed=remove_feedback(sh,p)
        write_json(folder/'ablation.json',dict(removed_parameter_indices=removed,
            removed='all local and backward proposal edges; all state-dependent gate inputs',
            retained='forward inter-layer routes, configured leaks, gate biases, input ages, existing outputs',
            interpretation='post-fit intervention, not a retrained capacity comparison'))
    manifest=json.loads((out/'data'/'manifest.json').read_text());rows=[]
    for c in manifest:
        if c['profile']!=e['profile']:continue
        s=load(out/'data'/c['name']);pred=infer(sh,p,s['x'],q);r=score(s,pred,True)
        if 'startup_ambiguous_until' in s:
            until=s['startup_ambiguous_until'];count=sum(a['start']<until for a in r['accepted'])
            r['startup_prefix_accepted']=count;r['background_accepted']-=count
            y=s['labels'][until:];z=pulses(pred)[until:]
            r['boundary_errors']=int(np.sum((np.isin(y,[3,4])|np.isin(z,[3,4]))&(y!=z)))
        r.update(profile=e['profile'],seed=e['seed'],arithmetic=arithmetic,condition=c['condition'])
        r['pass']=(r['exact_messages']==r['valid_messages'] and r['valid_messages']>=c['required_messages'] and
            r['boundary_errors']==0 and r['invalid_accepted']==0 and r['background_accepted']==0)
        # Retain per-message paired outcomes as well as every predicted tick.
        outcomes=[]
        for g in s['groups']:
            if g['valid']:
                a=[a for a in r['accepted'] if g['start']<=a['start']<g['end']]
                b=[a for a in r['expected'] if g['start']<=a['start']<g['end']]
                outcomes.append(int(a==b))
        r['message_outcomes']=outcomes
        write_json(folder/f"{c['condition']}.json",r)
        np.savez_compressed(folder/f"{c['condition']}_trace.npz",predicted=pred)
        rows.append({k:v for k,v in r.items() if k not in ('accepted','expected','first_event_errors','message_outcomes')})
        if c['condition']=='nominal':
            x=s['x'][:1024];whole=run(sh,p,x,quantize=q)[2]
            _,h,left,_,_=run(sh,p,x[:317],quantize=q);right=run(sh,p,x[317:],h=h,quantize=q)[2]
            altered=x.copy();altered[317:]*=-1
            audit=dict(batch_chunk=bool(np.array_equal(whole,np.r_[left,right])),
                causal_prefix=bool(np.array_equal(whole[:317],run(sh,p,altered,quantize=q)[2][:317])))
            if arithmetic=='float':
                receiver=Receiver(sh,p);online=[]
                for t in range(0,1024,37):online+=receiver.samples(s['lines'][t:min(t+37,1024)])
                audit['online_samples']=online==events(pulses(whole.argmax(1)))
            if not all(audit.values()):raise AssertionError(audit)
            write_json(folder/'replay_audit.json',audit)
    result=dict(shape=sh.name,profile=e['profile'],seed=e['seed'],arithmetic=arithmetic,pass_all=all(r['pass'] for r in rows),conditions=rows)
    write_json(folder/'summary.json',result);return result


def evaluate(out,workers,arithmetic):
    config=json.loads((out/'freeze.json').read_text())
    jobs=[(str(out),e,a) for e in config['entries'] for a in arithmetic.split(',') if a not in ('no_recurrence','no_feedback') or e['seed']==11]
    results=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(evaluate_job,jobs):
            results.append(r);print(r['shape'],r['profile'],r['seed'],r['arithmetic'],r['pass_all'],flush=True)
            write_json(out/'ledger.json',dict(completed=results,total=len(jobs)))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','generate','evaluate'])
    ap.add_argument('--output',type=Path,default=ROOT/'runs'/'connectivity01');ap.add_argument('--label',required=True)
    ap.add_argument('--candidates',type=Path);ap.add_argument('--seed-family',type=int,default=171000000)
    ap.add_argument('--profiles',default=','.join(PROFILES));ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--arithmetic',default='float');ap.add_argument('--recipe',default='matched');a=ap.parse_args()
    out=a.output/'confirmations'/a.label
    if a.action=='freeze':freeze(a.output,a.label,json.loads(a.candidates.read_text()),a.seed_family,
        json.loads(Path(a.recipe).read_text()) if a.recipe.endswith('.json') else a.recipe,a.profiles.split(','))
    elif a.action=='generate':generate(out)
    else:evaluate(out,a.workers,a.arithmetic)
