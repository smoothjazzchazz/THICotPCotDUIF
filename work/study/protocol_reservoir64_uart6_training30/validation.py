"""Independent evidence checks; no weight fitting or final-driven selection."""
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import MASK, LEAKS, ARCHITECTURE_HASH, StreamReceiver, load_weights, features
from work.study.protocol_reservoir64.profiles import load_config
from work.study.protocol_reservoir64.training import batch, class_weights, loss_gradient
from .data import load_split, cases
from .training import write_json, SEEDS, MULTIPLIERS, restore_optimizer, adam_step
from .metrics import score_case


def frame_credit(w, stream):
    # Actual first STOP (rather than an arbitrary end-of-prefix STOP logit).
    end=int(np.flatnonzero(stream['labels']==4)[0]); x=features(stream['lines'][:end+1])
    h=np.zeros(64); proposals=[]
    for sample in x:
        z=np.tanh(w['wx']@sample+w['wh']@h+w['b']);proposals.append(z)
        h=(1-LEAKS)*h+LEAKS*z
    dh=w['wo'][4].copy(); norms={0:float(np.linalg.norm(dh))}
    for t in range(end,-1,-1):
        dh=dh*(1-LEAKS)+(dh*LEAKS*(1-proposals[t]**2))@w['wh']
        lag=end-t+1
        if lag in (16,64,128,144,152,160,168,176): norms[lag]=float(np.linalg.norm(dh))
    return dict(stop_tick=end,sensitivity=norms,scope='STOP-logit derivative with respect to prior recurrent state; one real development frame')


def pre_main(output):
    from .investigation import initialize
    from .run import sha, ROOT
    output=Path(output);rows=[]
    previous=output.parents[2]/'protocol_reservoir64_training30/runs/run01'
    # Explicit corpus equality, including teacher labels and metadata.
    files=[]
    for p in (output/'data').rglob('*.npz'):
        q=previous/'data'/p.relative_to(output/'data')
        assert sha(p)==sha(q);files.append(str(p.relative_to(output)))
    for profile in ('uart_n','uart_e'):
        s=load_split(output,profile,'dev')[0]
        for recipe in ('previous','memory095','memory105'):
            rows.append(dict(profile=profile,recipe=recipe,**frame_credit(initialize(11,recipe),s)))
        for seed in (11,29,47):
            w,_=load_weights(previous/'models'/profile/f'seed_{seed}/epoch_30.npz')
            rows.append(dict(profile=profile,recipe=f'previous30_epoch30_seed{seed}',**frame_credit(w,s)))
    write_json(output/'audit/complete_frame_credit.json',dict(rows=rows,identical_corpus_files=files,
        note='Prior zero-byte failure investigated with preserved labels and trained weights; no prior final cases used for tuning.'))


def i2c_fresh(output):
    """Frozen I2C comparison using precisely the imported receiver class."""
    from work.study.protocol_reservoir64.evaluation import save_trace
    from work.study.protocol_reservoir64.test_experiment import EdgeReference
    from work.study.protocol_reservoir64_training30.simulation import run_i2c
    output=Path(output);final=output/'final'; root=final/'i2c_compatibility';root.mkdir(exist_ok=True)
    previous=output.parents[2]/'protocol_reservoir64_training30/runs/run01'
    all_rows=[]
    for variant in ('seed_11','seed_29','seed_47','original_loss_11'):
        w,meta=load_weights(previous/'models/i2c'/variant/'selected.npz')
        for mode in ('float','quantized'):
            path=root/f'{variant}_{mode}.json'
            if path.exists(): all_rows.extend(json.loads(path.read_text())); continue
            rows=[]
            for c in cases('i2c','final'):
                metrics,result=score_case('i2c',c,StreamReceiver(w,mode),load_config(output,'i2c'))
                metrics['cold_start_events']=[dict(kind=e.kind,tick=e.decision_tick) for e in result['events'] if e.decision_tick<8]
                row=dict(profile='i2c',variant=variant,mode=mode,condition=c['name'],valid=c['valid'],seed=c['seed'],**metrics)
                rows.append(row)
                if c['name']=='phrase':
                    dest=root/'traces'/variant;dest.mkdir(parents=True,exist_ok=True)
                    save_trace(dest,'i2c',mode,meta['seed'],c,result,metrics)
            write_json(path,rows);all_rows.extend(rows)
            print(json.dumps(dict(i2c=variant,mode=mode,exact=sum(r['bytes']['exact'] for r in rows if r['valid']),strict=sum(r['passes'] for r in rows if r['valid']))),flush=True)
    write_json(root/'summary.json',dict(architecture_hash=ARCHITECTURE_HASH,rows=all_rows))
    # Verify the seed spaces against actual old case manifests, and timing settings
    # via an oracle peer run. The oracle never enters the learned inference path.
    timing=[]
    for c in cases('i2c','final'):
        if 'clock' not in c['name'] and 'jitter' not in c['name']:continue
        a=run_i2c(b'\x00\xff\x55\xaa',EdgeReference(),low=c.get('low',10),high=c.get('high',10),
                  jitter=bool(c.get('jitter',0)),peer_seed=c['seed'])
        scl=a['lines'][:,0];edges=np.r_[0,np.flatnonzero(np.diff(scl)!=0)+1,len(scl)]
        spans=[dict(level=int(scl[l]),ticks=int(r-l)) for l,r in zip(edges[:-1],edges[1:])]
        timing.append(dict(condition=c['name'],requested_low=c.get('low',10),requested_high=c.get('high',10),jitter=bool(c.get('jitter',0)),
                          measured_high_durations=sorted(set(v['ticks'] for v in spans[1:-1] if v['level'])),
                          measured_low_durations=sorted(set(v['ticks'] for v in spans[1:-1] if not v['level'])),
                          note='Low cells may include the unchanged target stretch. I2C ratio is inapplicable; explicit low/high fields set timing.'))
    write_json(root/'effective_timing.json',timing)


def cold_idle(output):
    output=Path(output);rows=[]
    for p in ('uart_n','uart_e'):
        for v in [*(f'seed_{s}' for s in SEEDS),'previous_recipe_11']:
            w,_=load_weights(output/'models'/p/v/'selected.npz')
            for mode in ('float','quantized'):
                rx=StreamReceiver(w,mode);events=[]
                for t in range(2048):
                    e=rx.step((1,1),t)
                    if e:events.append(dict(kind=e.kind,tick=t))
                rows.append(dict(profile=p,variant=v,mode=mode,ticks=2048,false_events=len(events),events=events))
    write_json(output/'final/cold_idle.json',rows)


def checkpoints(output):
    from .investigation import initialize
    output=Path(output);recipe=json.loads((output/'recipe.json').read_text())['selected']; rows=[]
    for profile in ('uart_n','uart_e'):
        streams=load_split(output,profile,'train');x,y,valid=batch(streams);weights=class_weights(y,valid)*MULTIPLIERS
        for variant in [*(f'seed_{s}' for s in SEEDS),'previous_recipe_11']:
            directory=output/'models'/profile/variant;fit=json.loads((directory/'fit.json').read_text())
            w0,_=load_weights(directory/'initial.npz');want=initialize(fit['seed'],recipe if variant.startswith('seed') else 'previous')
            for k in want:np.testing.assert_array_equal(w0[k],want[k])
            for epoch in range(1,31):
                w,meta=load_weights(directory/f'epoch_{epoch:02d}.npz')
                assert not np.any(w['wh']*(1-MASK))
                if variant=='previous_recipe_11':
                    old,_=load_weights(output.parents[2]/'protocol_reservoir64_training30/runs/run01/models'/profile/'seed_11'/f'epoch_{epoch:02d}.npz')
                    for k in w:np.testing.assert_array_equal(w[k],old[k])
                ow,m,v,om=restore_optimizer(directory/f'optimizer_{epoch:02d}.npz')
                assert om['epoch']==epoch and om['step']==epoch*((len(x)+511)//512)
                for k in w:np.testing.assert_array_equal(w[k],ow[k])
            selected,meta=load_weights(directory/'selected.npz');best,_=load_weights(directory/f"epoch_{fit['best_epoch']:02d}.npz")
            for k in best:np.testing.assert_array_equal(selected[k],best[k])
            # Re-execute a real full epoch from the retained Adam checkpoint.
            if fit['seed']==11:
                w,m,v,meta=restore_optimizer(directory/'optimizer_29.npz');state=np.zeros((12,64));step=meta['step']
                for start in range(0,len(x),512):
                    _,state,g=loss_gradient(w,x[start:start+512],y[start:start+512],valid[start:start+512],state,weights)
                    step+=1;adam_step(w,g,m,v,step)
                rw,rm,rv,_=restore_optimizer(directory/'optimizer_30.npz')
                for a,b in ((w,rw),(m,rm),(v,rv)):
                    for k in a:np.testing.assert_array_equal(a[k],b[k])
                with np.load(directory/'optimizer_30.npz') as z:np.testing.assert_array_equal(state,z['ending_state'])
            rows.append(dict(profile=profile,variant=variant,epochs_verified=30,real_epoch_resume_exact=fit['seed']==11))
    write_json(output/'analysis/checkpoint_verification.json',rows)

def final_timing_audit(output):
    from .uart_scoring import uart_case
    output=Path(output); rows=[]; seeds=[]
    for profile in ('uart_n','uart_e','i2c'):
        for c in cases(profile,'final'):
            seeds.append(c['seed'])
            if profile=='i2c': continue
            data=uart_case(c,c['seed']-90001,profile=='uart_e')
            if c.get('malformed') or c.get('disturbance'): continue
            rng=np.random.default_rng(c['seed']);elapsed=12.+rng.random();cursor=12;durations=[];gaps=[]
            for f in data['frames']:
                assert cursor==f['start']
                for cell in range(11 if profile=='uart_e' else 10):
                    elapsed+=16*c.get('ratio',1.)+(int(rng.integers(-1,2)) if c.get('jitter') else 0)
                    end=round(elapsed);center=cursor+(end-cursor)//2
                    assert data['labels'][center]!=0
                    assert np.all(data['lines'][cursor:end,0]==data['lines'][center,0])
                    durations.append(end-cursor);cursor=end
                assert cursor-1==f['end']
                if c.get('gaps'):
                    gap=int(rng.integers(0,3))*16;gaps.append(gap);cursor+=gap;elapsed+=gap
            if c.get('jitter'):assert len(set(durations))>1
            if c.get('gaps'):assert max(gaps)>0
            values,counts=np.unique(durations,return_counts=True)
            rows.append(dict(profile=profile,condition=c['name'],seed=c['seed'],ratio=c.get('ratio',1.),jitter=c.get('jitter',0),
                measured_cell_lengths={str(v):int(n) for v,n in zip(values,counts)},gaps=sorted(set(gaps)),passed=True))
    assert len(seeds)==len(set(seeds))
    # Prior final spaces: original 90,001+, previous30 3M+, 32-node 4M+.
    # Reused fitting corpora have seeds 1M/2M; live dev uses 40M+.
    assert all(50_000_000<=s<51_000_000 for s in seeds)
    for profile in ('uart_n','uart_e'):
        assert not set(seeds)&{c['seed'] for c in cases(profile,'dev')}
        for split in ('train','dev'):
            for stream in load_split(output,profile,split):
                assert not set(seeds)&{t['seed'] for t in stream['metadata']['transactions']}
    write_json(output/'final/timing_audit.json',dict(passed=True,rows=rows,distinct_final_seeds=len(seeds),split_overlap=0,
        previous_final_families=[90001,3000000,4000000]))


if __name__=='__main__':
    import sys
    output=Path(sys.argv[2])
    {'pre_main':pre_main,'i2c':i2c_fresh,'cold_idle':cold_idle,'checkpoints':checkpoints}[sys.argv[1]](output)
