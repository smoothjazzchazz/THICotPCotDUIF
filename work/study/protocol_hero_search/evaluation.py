"""Freeze-before-generation confirmation, diagnostic controls, and replay audits."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import platform
import subprocess
import sys
import numpy as np
from .shapes import make_shape,features,SEEDS,PROFILES,initialize
from .network import run,pulses,events,Receiver
from .data import Builder,reference_labels,assemble,score
from .training import write_json,load_data
from .run import ROOT,digest


def conditions(profile):
    if profile.startswith('uart'):return ['nominal','minus','plus','jitter','minus_jitter','plus_jitter','gaps']
    return ['nominal','duty','pauses','phase']+(['repeated'] if profile=='i2c' else [])


def final_selection(root):
    advanced=json.loads((root/'screen_selection.json').read_text())['advanced'];ranking=[]
    for candidate in advanced:
        profiles={}
        for profile in PROFILES:
            regime=candidate['profiles'][profile]['regime']
            rows=[json.loads((root/'models'/candidate['shape']/profile/f'{regime}_{s}'/'finalist_done.json').read_text()) for s in SEEDS]
            profiles[profile]=dict(regime=regime,accuracy=float(np.mean([r['selected']['message_accuracy'] for r in rows])),
                boundary=float(np.mean([r['selected']['boundary_f1'] for r in rows])),
                false_rate=float(np.mean([r['selected']['false_events']/r['selected']['ticks'] for r in rows])),
                exact_dev_seeds=sum(r['selected']['exact_messages']==r['selected']['valid_messages'] and
                                    r['selected']['boundary_errors']==0 and r['selected']['invalid_accepted']==0 and
                                    r['selected']['background_accepted']==0 for r in rows))
        rank=(min(p['exact_dev_seeds'] for p in profiles.values()),min(p['accuracy'] for p in profiles.values()),
              min(p['boundary'] for p in profiles.values()),-max(p['false_rate'] for p in profiles.values()),
              -make_shape(candidate['variant'],candidate['nodes']).parameters)
        ranking.append(dict(**{k:candidate[k] for k in ('shape','variant','nodes')},profiles=profiles,rank=rank))
    ranking.sort(key=lambda r:r['rank'],reverse=True)
    result=dict(ranking=ranking,top_two=ranking[:2],selection_data='development only; no confirmation generated yet')
    write_json(root/'final_selection.json',result);return result


def freeze(root):
    if (root/'freeze.json').exists():return
    selection=final_selection(root);source=root/'frozen_source';source.mkdir()
    for p in ROOT.iterdir():
        if p.is_file():shutil.copy2(p,source/p.name)
    shutil.copy2(ROOT/'build'/'kernel.so',source/'kernel.so')
    write_json(root/'environment.json',dict(python=sys.version,numpy=np.__version__,
        platform=platform.platform(),machine=platform.machine(),
        compiler=subprocess.check_output(['g++','--version'],text=True).splitlines()[0],
        compiler_flags=['-O3','-std=c++17','-shared','-fPIC'],blas_threads=1,
        screen_workers=8,initial_finalist_workers=8,resumed_finalist_workers=16,confirmation_workers=8))
    hashes={str(p.relative_to(root)):digest(p) for p in source.iterdir()}
    hashes['environment.json']=digest(root/'environment.json')
    for candidate in selection['top_two']:
        for profile in PROFILES:
            regime=candidate['profiles'][profile]['regime']
            for seed in SEEDS:
                p=root/'models'/candidate['shape']/profile/f'{regime}_{seed}'/'selected.npz'
                hashes[str(p.relative_to(root))]=digest(p)
    hashes['final_selection.json']=digest(root/'final_selection.json')
    write_json(root/'freeze.json',dict(hashes=hashes,confirmation_seed_family=91_000_000,
        valid_messages_per_timing_condition=1000,threshold='all messages exact, all boundary ticks exact, no accepted invalid/background; >=5/6 seeds every profile',
        quantization='signed Q3.12 weights/states, Q24 64-bit accumulators, nearest rounding, 4097-entry Q12 tanh LUT over [-8,8] at 1/256 spacing; integer replay, no RTL/hardware claim'))


def save_stream(root,name,s):
    base=root/'confirmation_data'/name
    x=features(s['lines'])[0]
    np.savez_compressed(base.with_suffix('.npz'),lines=s['lines'],labels=s['labels'],x=x)
    write_json(base.with_suffix('.json'),{k:v for k,v in s.items() if k not in ('lines','labels')})


def generate_confirmation(root):
    if not (root/'freeze.json').exists():raise ValueError('freeze required before fresh data')
    folder=root/'confirmation_data';folder.mkdir(exist_ok=True)
    manifest=[]
    for pi,profile in enumerate(PROFILES):
        for ci,condition in enumerate(conditions(profile)):
            name=f'{profile}_{condition}'
            if not (folder/f'{name}.json').exists():
                seed=91_000_000+pi*100_000+ci*1000;b=Builder(profile,seed)
                for i in range(1000):
                    if i==0:payload=b.rng.integers(0,256,1024).tolist()
                    elif i==1:payload=list(range(256))
                    elif i<6:payload=[(0,255,85,170)[i-2]]*64
                    elif i%100==0:payload=b.rng.integers(0,256,128).tolist()
                    else:payload=b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist()
                    b.message(payload,condition)
                if profile=='i2c' and condition=='nominal':
                    for i in range(50):
                        b.message([],condition='address_nack')
                        b.message([int(b.rng.integers(0,256))],condition='write_nack')
                s=b.finish();s['seed']=seed;save_stream(root,name,s)
            manifest.append(dict(name=name,profile=profile,condition=condition,kind='valid',required_messages=1000))
            print(json.dumps(dict(generated=name)),flush=True)
        # Invalid bursts and then recovery, together in one continuous stream.
        name=f'{profile}_invalid_recovery'
        if not (folder/f'{name}.json').exists():
            b=Builder(profile,92_000_000+pi*100_000)
            errors=(['framing','break']+(['parity'] if profile=='uart_e' else [])) if profile.startswith('uart') else ['partial']
            for i in range(100):
                b.message([int(b.rng.integers(0,256))],invalid=errors[i%len(errors)])
                b.message(b.rng.integers(0,256,4).tolist())
                if i%10==0:b.idle(4096)
            save_stream(root,name,b.finish())
        manifest.append(dict(name=name,profile=profile,condition='invalid_recovery',kind='invalid_and_recovery',required_messages=100))
        # Midstream prefix is inherently ambiguous; only the subsequent synchronized messages are gated.
        name=f'{profile}_midstream'
        if not (folder/f'{name}.json').exists():
            b=Builder(profile,93_000_000+pi*100_000)
            for i in range(101):b.message(b.rng.integers(0,256,4).tolist())
            s=b.finish();cut=s['groups'][0]['start']+37
            lines=s['lines'][cut:];labels=reference_labels(lines,profile)
            groups=[{**g,'start':g['start']-cut,'end':g['end']-cut} for g in s['groups'][1:]]
            truth,rejections=assemble(events(labels),profile)
            s=dict(lines=lines,labels=labels,groups=groups,truth=truth,profile=profile,
                   startup_ambiguous_until=groups[0]['start'],reference_rejections=rejections)
            save_stream(root,name,s)
        manifest.append(dict(name=name,profile=profile,condition='midstream',kind='startup_recovery',required_messages=100))
    write_json(root/'confirmation_data'/'manifest.json',manifest)
    write_json(root/'confirmation_data_hashes.json',{str(p.relative_to(root)):digest(p) for p in folder.iterdir() if p.is_file()})


def load_confirmation(root,name):
    base=root/'confirmation_data'/name
    a=dict(np.load(base.with_suffix('.npz'),allow_pickle=False));a.update(json.loads(base.with_suffix('.json').read_text()));return a


def infer(shape,p,x,quantize=False):
    state=np.zeros(shape.n);kinds=np.empty(len(x),dtype=np.int32)
    for t in range(0,len(x),8192):
        _,state,logits,_,_=run(shape,p,x[t:t+8192],h=state,quantize=quantize)
        kinds[t:t+8192]=logits.argmax(1)
    return kinds


def evaluate_job(job):
    root,candidate,profile,seed,arithmetic=job;root=Path(root)
    directory=root/'confirmation'/candidate['shape']/profile/f'{arithmetic}_{seed}'
    directory.mkdir(parents=True,exist_ok=True)
    if (directory/'summary.json').exists():return json.loads((directory/'summary.json').read_text())
    regime=candidate['profiles'][profile]['regime'];shape=make_shape(candidate['variant'],candidate['nodes'])
    model=root/'models'/shape.name/profile/f'{regime}_{seed}'/'selected.npz'
    with np.load(model,allow_pickle=False) as a:p=a['p'].copy()
    if arithmetic=='quantized':p=np.round(p*4096)/4096
    elif arithmetic=='no_recurrence':
        group_of={node:i for i,group in enumerate(shape.groups) for node in group}
        recurrent=np.array([s>=0 and group_of[s]==group_of[int(d)] for s,d in zip(shape.src,shape.dst)])
        p[:len(shape.src)][recurrent]=0
    dev=load_data(root,profile,'dev');prefix=dev['x'][:1024];q=arithmetic=='quantized'
    whole=run(shape,p,prefix,quantize=q)[2]
    _,state,left,_,_=run(shape,p,prefix[:317],quantize=q)
    right=run(shape,p,prefix[317:],h=state,quantize=q)[2]
    altered=prefix.copy();altered[317:]*=-1
    causal=run(shape,p,altered,quantize=q)[2]
    audit=dict(batch_chunk_agreement=bool(np.array_equal(whole,np.r_[left,right])),
               causal_prefix=bool(np.array_equal(whole[:317],causal[:317])),
               model_sha256=digest(model))
    if arithmetic=='float':
        online=Receiver(shape,p);out=[]
        for t in range(0,1024,37):out+=online.samples(dev['lines'][t:min(t+37,1024)])
        audit['online_sample_agreement']=out==events(pulses(whole.argmax(1)))
    write_json(directory/'replay_audit.json',audit)
    if not all(v for k,v in audit.items() if k!='model_sha256'):raise AssertionError(audit)
    rows=[]
    manifest=json.loads((root/'confirmation_data'/'manifest.json').read_text())
    for c in manifest:
        if c['profile']!=profile:continue
        stream=load_confirmation(root,c['name']);kinds=infer(shape,p,stream['x'],arithmetic=='quantized')
        r=score(stream,kinds,True)
        if 'startup_ambiguous_until' in stream:
            until=stream['startup_ambiguous_until']
            count=sum(a['start']<until for a in r['accepted'])
            r['startup_prefix_accepted']=count;r['background_accepted']-=count
            # Only recovery boundaries after observable idle/select/START are qualified.
            expected=stream['labels'][until:];pred=pulses(kinds)[until:]
            r['boundary_errors']=int(np.sum((np.isin(expected,[3,4])|np.isin(pred,[3,4]))&(expected!=pred)))
        r.update(condition=c['condition'],kind=c['kind'],profile=profile,seed=seed,arithmetic=arithmetic)
        r['pass']=(r['exact_messages']==r['valid_messages'] and r['boundary_errors']==0 and
                   r['invalid_accepted']==0 and r['background_accepted']==0)
        # Keep full accepted/truth records and the complete prediction trace for replay.
        write_json(directory/f"{c['condition']}.json",r)
        np.savez_compressed(directory/f"{c['condition']}_trace.npz",predicted=kinds)
        rows.append({k:v for k,v in r.items() if k not in ('accepted','expected','first_event_errors')})
    result=dict(shape=shape.name,profile=profile,seed=seed,arithmetic=arithmetic,pass_all=all(r['pass'] for r in rows),conditions=rows)
    write_json(directory/'summary.json',result);return result


def diagnostics(root):
    chosen=json.loads((root/'final_selection.json').read_text())['top_two'];rows=[]
    for candidate in chosen:
        sh=make_shape(candidate['variant'],candidate['nodes'])
        for profile in PROFILES:
            regime=candidate['profiles'][profile]['regime'];path=root/'models'/sh.name/profile/f'{regime}_11'/'selected.npz'
            p=np.load(path,allow_pickle=False)['p'];dev=load_data(root,profile,'dev');x=dev['x']
            full=run(sh,p,x[:2048])[2];cut=773
            _,h,a,_,_=run(sh,p,x[:cut]);b=run(sh,p,x[cut:2048],h=h)[2]
            online=Receiver(sh,p);e=[]
            for t in range(2048):e+=online.samples(dev['lines'][t:t+1])
            replay=np.load(path,allow_pickle=False)['p']
            horizons={}
            for lag in (16,64,176,512,1024):
                y=np.zeros(lag,dtype=np.int32);y[-1]=int(dev['labels'][lag-1]) or 1
                cw=np.ones(6);cw[0]=0
                r=run(sh,p,x[:lag],y,cw,backward=True)
                horizons[str(lag)]=float(np.linalg.norm(r[4]))
            # Closest opposite-label states with the same instantaneous nine-feature vector.
            states=[];h=np.zeros(sh.n)
            for t in range(1024):
                _,h,_,_,_=run(sh,p,x[t:t+1],h=h);states.append(h.copy())
            states=np.asarray(states);minimum=None;pair=None;groups={}
            for t,row in enumerate(x[:1024]):groups.setdefault(tuple(row),[]).append(t)
            for indices in groups.values():
                for ai,i in enumerate(indices):
                    for j in indices[ai+1:]:
                        if dev['labels'][i]==dev['labels'][j]:continue
                        distance=float(np.linalg.norm(states[i]-states[j]))
                        if minimum is None or distance<minimum:minimum=distance;pair=[i,j]
            row=dict(shape=sh.name,profile=profile,checkpoint_replay=bool(np.array_equal(p,replay)),
                batch_chunk_agreement=bool(np.array_equal(full,np.r_[a,b])),
                online_tick_agreement=e==events(pulses(full.argmax(1))),
                terminal_loss_initial_state_gradient=horizons,
                closest_opposite_label_same_features_distance=minimum,closest_pair=pair,
                interpretation='small distances/gradients diagnose this configuration; do not establish architectural impossibility')
            rows.append(row)
    write_json(root/'diagnostics.json',rows)
    if not all(r['checkpoint_replay'] and r['batch_chunk_agreement'] and r['online_tick_agreement'] for r in rows):raise AssertionError('replay agreement failed')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','generate','evaluate','diagnostics'])
    ap.add_argument('--output',type=Path,default=ROOT/'runs'/'run01');ap.add_argument('--workers',type=int,default=8)
    args=ap.parse_args();root=args.output
    if args.action=='freeze':freeze(root)
    elif args.action=='generate':generate_confirmation(root)
    elif args.action=='diagnostics':diagnostics(root)
    else:
        selected=json.loads((root/'final_selection.json').read_text())['top_two']
        jobs=[(str(root),c,p,s,a) for c in selected for p in PROFILES for s in SEEDS for a in ('float','quantized')]
        jobs += [(str(root),c,p,11,'no_recurrence') for c in selected for p in PROFILES]
        rows=[]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for r in pool.map(evaluate_job,jobs):
                rows.append(r);write_json(root/'confirmation_ledger.json',rows)
                print(json.dumps({k:r[k] for k in ('shape','profile','seed','arithmetic','pass_all')}),flush=True)

if __name__=='__main__':main()
