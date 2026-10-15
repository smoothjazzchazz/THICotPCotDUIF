"""Recovery-heavy off-chip fitting; never imported by the deployed receiver."""
import argparse
import json
import numpy as np
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape,SEEDS,features
from .vendor.data import Builder
from .data import load,save,metrics
from .extended_data import finish_cut
from .train import evaluate_stream,write_json,key


def build(profile,seed,epoch):
    b=Builder(profile,seed);b.message(b.rng.integers(0,256,4).tolist())
    cut=b.groups[0]['start']+int(b.rng.integers(17,145))
    errors=['framing','break']+(['parity'] if profile=='uart_e' else [])
    choices=['nominal','minus','plus','jitter','minus_jitter','plus_jitter','gaps']
    values=b.rng.permutation(256);i=0
    while len(b.lines)-cut<65536:
        # Uniform byte/error combinations over epochs, not copied failure bytes.
        value=int(values[i%256]);error=errors[(i+epoch)%len(errors)]
        b.message([value],invalid=error)
        b.message(b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist(),choices[i%7])
        if i%11==0:b.message([(0,255,85,170)[i//11%4]]*64,choices[(i+3)%7])
        b.idle(4096 if i%31==0 else int(b.rng.integers(0,65)))
        i+=1
    s=finish_cut(b,cut);s['seed']=seed;s['startup_cut']=cut
    return s


def generate(root,epochs):
    folder=root/'data_recovery'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for epoch in range(1,epochs+1,2):
            path=folder/profile/f'epoch_{epoch:04d}'
            if not path.with_suffix('.json').exists():save(path,build(profile,271000000+pi*1000000+epoch*1000,epoch))
        print('Recovery training ready',profile,flush=True)
    write_json(folder/f'manifest_{epochs:04d}.json',dict(seed_family=271000000,epochs=epochs,
        files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and not p.name.startswith('manifest_')}))


def passed(r):
    return r['message_accuracy']==1 and r['boundary_errors']==0 and r['invalid_accepted']==0 and r['background_accepted']==0


def prepare(root,candidates,recipe):
    jobs=[]
    for kwargs in candidates:
        sh=make_shape(**kwargs)
        for profile in ('uart_n','uart_e'):
            dev=load(root/'data_extended'/profile/'dev')
            for seed in SEEDS:
                folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
                path=folder/'warm_start.json'
                if path.exists():record=json.loads(path.read_text())
                else:
                    options=[]
                    for source in ('phase_profile_fresh','phase_ring_fixed','phase_extended'):
                        files=sorted((root/'models'/source/sh.name/profile/str(seed)).glob('block_*.json'))
                        b=json.loads(files[-1].read_text());model=np.load(b['checkpoint']);sh.leaks=model['leaks'].copy()
                        loss,z=evaluate_stream(sh,model['p'],dev,np.ones(6));score=metrics(dev,z.argmax(1));score['dev_loss']=loss
                        options.append(dict(source_block=str(files[-1]),source_recipe=source,checkpoint=b['checkpoint'],
                            checkpoint_sha256=digest(b['checkpoint']),extended_development=score,epochs_spent=b['epochs'],
                            exposure_ticks=b['exposure_ticks'],prior_warm_start=b.get('warm_start')))
                    best=max(options,key=lambda x:key(x['extended_development']))
                    record=dict(checkpoint=best['checkpoint'],checkpoint_sha256=best['checkpoint_sha256'],reset_optimizer=True,
                        selected_source=best,candidates=options,source_profile=profile,target_profile=profile,
                        policy='latest native, profile-fresh, or extended checkpoint selected by the unchanged extended development key')
                    write_json(path,record)
                # Preserve passing weights at epoch zero and avoid unnecessary updates.
                target=0 if passed(record['selected_source']['extended_development']) else 60
                jobs.append((str(root),kwargs,profile,seed,target,recipe))
    return jobs


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['generate','train']);ap.add_argument('--recipe',default='phase_recovery')
    ap.add_argument('--workers',type=int,default=8);ap.add_argument('--epochs',type=int,default=60);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01'
    if a.action=='generate':generate(root,a.epochs)
    else:
        candidates=json.loads((ROOT/'phase_route_candidates.json').read_text())
        batch_jobs(root,prepare(root,candidates,a.recipe),a.workers,a.recipe+'60')
