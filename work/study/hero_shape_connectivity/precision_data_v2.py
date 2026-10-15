"""Cold startup with an explicit observable synchronization opportunity."""
import argparse
import numpy as np
from .run import ROOT,digest
from .data import conditions,save
from .vendor.data import Builder
from .extended_data import finish_cut
from .shapes import features
from .train import write_json
from .startup_audit import mismatches


def prefix(profile,seed):
    b=Builder(profile,seed);b.message(b.rng.integers(0,256,4).tolist())
    cut=b.groups[0]['start']+int(b.rng.integers(1,b.groups[0]['end']-b.groups[0]['start']-1))
    b.idle(256)
    return b,cut


def finish(b,cut,seed):
    s=finish_cut(b,cut);bad=mismatches(s)
    if bad:raise AssertionError(('post-synchronization payload contract',bad))
    s['seed']=seed;s['startup_cut']=cut;s['observable_sync_high_ticks']=256
    return s


def cold(profile,seed,count=8):
    b,cut=prefix(profile,seed)
    for i in range(count):
        if i%3==2:b.message([int(b.rng.integers(256))],invalid=['framing','break'][i%2])
        b.message(b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist(),conditions(profile)[i%7])
    return finish(b,cut,seed)


def long(profile,seed,bank):
    b,cut=prefix(profile,seed);choices=conditions(profile)
    payload=b.rng.integers(0,256,1024).tolist() if bank%3 else [(0,255,85,170)[bank//3%4]]*1024
    b.message(payload,choices[bank%7]);errors=['framing','break']+(['parity'] if profile=='uart_e' else [])
    for i in range(24):
        b.message([int(b.rng.integers(256))],invalid=errors[i%len(errors)])
        b.message(b.rng.integers(0,256,4).tolist());b.idle(4096 if i%8==0 else 17)
    i=0
    while len(b.lines)-cut<262144:
        payload=b.rng.integers(0,256,int(b.rng.integers(1,17))).tolist()
        if i%11==0:payload=[(0,255,85,170)[i//11%4]]*64
        b.message(payload,choices[i%7]);i+=1
    return finish(b,cut,seed)


def generate(root,epochs=60):
    folder=root/'data_precision_v2'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for i,c in enumerate(conditions(profile)):
            base=folder/profile/'dev'/c
            if base.with_suffix('.json').exists():continue
            b=Builder(profile,313000000+pi*100000+i*1000)
            for j in range(256):
                payload=b.rng.integers(0,256,1024 if j==0 else int(b.rng.integers(1,9))).tolist()
                if j==1:payload=list(range(256))
                elif 2<=j<6:payload=[(0,255,85,170)[j-2]]*64
                b.message(payload,c)
            s=b.finish();s['x']=features(s['lines'])[0];save(base,s)
        for i in range(64):
            base=folder/profile/'dev'/f'cold_{i:03d}'
            if not base.with_suffix('.json').exists():save(base,cold(profile,314000000+pi*100000+i*100,8))
        for i in range(256):
            base=folder/profile/'train'/f'cold_{i:03d}'
            if not base.with_suffix('.json').exists():save(base,cold(profile,311000000+pi*100000+i*100,8))
        for i in range(epochs):
            base=folder/profile/'train'/f'long_{i+1:04d}'
            if not base.with_suffix('.json').exists():save(base,long(profile,315000000+pi*1000000+i*1000,i))
        print('Verified observable-startup coverage ready',profile,flush=True)
    write_json(folder/f'manifest_{epochs:04d}.json',dict(epochs=epochs,training_families=[311000000,315000000],development_families=[313000000,314000000],
        observable_sync_high_ticks=256,post_cut_payload_contract='asserted for every declared valid message',
        reason='original qualification requires recovery after an observable synchronization opportunity; short gaps did not guarantee it',
        files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and not p.name.startswith('manifest')}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--epochs',type=int,default=60);a=ap.parse_args();generate(ROOT/'runs'/'connectivity01',a.epochs)
