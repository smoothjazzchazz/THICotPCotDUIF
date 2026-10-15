"""A new deterministic training stream each epoch; confirmation is disjoint."""
import argparse
import numpy as np
from .run import ROOT,digest
from .extended_data import build
from .data import load,save
from .train import write_json


def generate(root,epochs):
    folder=root/'data_fresh'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for epoch in range(epochs):
            p=folder/profile/f'epoch_{epoch+1:04d}'
            if p.with_suffix('.json').exists():continue
            reference=load(root/'data_extended'/profile/f'mixed_{epoch%12:02d}')
            target=len(reference['x']);seed=241000000+pi*1000000+epoch*1000
            # Append training-only idle if the independently generated stream is
            # slightly shorter; both recipes receive the same ticks per epoch.
            s=build(profile,seed,epoch)
            if len(s['x'])<target:
                from .vendor.data import reference_labels,assemble
                from .runtime import events
                from .shapes import features
                s['lines']=np.r_[s['lines'],np.ones((target-len(s['x']),3),dtype=np.uint8)]
                s['labels']=reference_labels(s['lines'],profile);s['x']=features(s['lines'])[0]
                s['truth'],s['reference_rejections']=assemble(events(s['labels']),profile)
            for k in ('x','lines','labels'):s[k]=s[k][:target]
            s['groups']=[g for g in s['groups'] if g['end']<=target];s['truth']=[g for g in s['truth'] if g['stop']<target]
            s['paired_epoch_ticks']=target;save(p,s)
            if (epoch+1)%10==0:print(profile,epoch+1,'fresh training banks ready',flush=True)
    write_json(folder/f'manifest_{epochs:04d}.json',dict(epochs=epochs,seed_family=241000000,
        policy='each epoch uses an independent bank; same per-epoch tick counts and class weights as extended-bank refinement',
        files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and not p.name.startswith('manifest_')}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--epochs',type=int,default=60);a=ap.parse_args();generate(ROOT/'runs'/'connectivity01',a.epochs)
