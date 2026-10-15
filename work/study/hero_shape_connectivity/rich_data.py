"""Additional independent UART training coverage; never confirmation data."""
import json
import numpy as np
from .run import ROOT,digest
from .data import build,load,save
from .train import write_json


def generate(root):
    destination=root/'data_rich'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for i in range(24):
            target=len(load(root/'data'/profile/f'mixed_{i%12:02d}')['x'])
            path=destination/profile/f'mixed_{i:02d}'
            if path.with_suffix('.json').exists():continue
            stream=build(profile,203000000+pi*10000+i*100,ticks=target)
            # The paired old/new recipe sees exactly the same ticks per epoch.
            # A prefix can end inside a frame, as an ordinary training chunk can.
            for key in ('x','lines','labels'):stream[key]=stream[key][:target]
            stream['groups']=[g for g in stream['groups'] if g['end']<=target]
            stream['truth']=[g for g in stream['truth'] if g['stop']<target]
            stream['training_prefix_ticks']=target
            save(path,stream)
    write_json(destination/'manifest.json',dict(purpose='independent training coverage only; same timing support and per-epoch exposure as phase_fine',
        seed_family=203000000,banks=24,files={str(p.relative_to(destination)):digest(p) for p in destination.rglob('*') if p.is_file() and p.name!='manifest.json'}))
    print('Additional independent UART training banks recorded before fitting.')

if __name__=='__main__':generate(ROOT/'runs'/'connectivity01')
