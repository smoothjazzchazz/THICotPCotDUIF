"""Broader deterministic training streams; historical timing/labels unchanged."""
import json
from pathlib import Path
import numpy as np
from .vendor.data import Builder, score
from .shapes import features, PROFILES


def conditions(profile):
    if profile.startswith('uart'):return ['nominal','minus','plus','jitter','minus_jitter','plus_jitter','gaps']
    return ['nominal','duty','pauses','phase']+(['repeated','address_nack','write_nack'] if profile=='i2c' else [])


def build(profile,seed,ticks=32768,stage='mixed',condition=None,messages=None):
    b=Builder(profile,seed);i=0;choices=conditions(profile)
    while len(b.lines)<ticks if messages is None else i<messages:
        size=int(b.rng.integers(1,3 if stage=='clean' else 9))
        payload=b.rng.integers(0,256,size).tolist()
        if i%5==0:payload=[(0,255,85,170)[(i//5)%4]]*size
        c=condition or (choices[i%len(choices)] if stage=='mixed' else 'nominal')
        if c=='address_nack':payload=[]
        invalid=None
        if stage=='mixed' and condition is None and i%13==12:
            invalid=(['framing','break']+(['parity'] if profile=='uart_e' else []))[i//13%(3 if profile=='uart_e' else 2)] if profile.startswith('uart') else 'partial'
            c='nominal';payload=payload[:1] or [0]
        b.message(payload,c,invalid)
        if i%29==28:b.idle(4096)
        i+=1
    s=b.finish();s['x']=features(s['lines'])[0];s['seed']=seed
    return s


def save(base,stream):
    base=Path(base);base.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(base.with_suffix('.npz'),**{k:stream[k] for k in ('lines','labels','x')})
    base.with_suffix('.json').write_text(json.dumps({k:v for k,v in stream.items() if k not in ('lines','labels','x')}))


def load(base):
    base=Path(base);a=dict(np.load(base.with_suffix('.npz'),allow_pickle=False))
    a.update(json.loads(base.with_suffix('.json').read_text()));return a


def metrics(stream,kinds):
    row=score(stream,kinds)
    if 'startup_ambiguous_until' in stream:
        from .vendor.network import pulses,events
        from .vendor.data import assemble
        until=stream['startup_ambiguous_until'];pred=pulses(kinds)
        accepted,_=assemble(events(pred),stream['profile'])
        row['startup_prefix_accepted']=sum(a['start']<until for a in accepted)
        row['background_accepted']-=row['startup_prefix_accepted']
        y=stream['labels'][until:];z=pred[until:]
        row['boundary_errors']=int(np.sum((np.isin(y,[3,4])|np.isin(z,[3,4]))&(y!=z)))
    by={}
    for condition in sorted({g['condition'] for g in stream['groups'] if g['valid']}):
        groups=[g for g in stream['groups'] if g['valid'] and g['condition']==condition]
        subset={**stream,'groups':groups}
        r=score(subset,kinds)
        by[condition]={k:r[k] for k in ('valid_messages','exact_messages','byte_exact_messages','message_accuracy')}
    row['conditions']=by
    return row


def generate(folder):
    for pi,profile in enumerate(PROFILES):
        for stage in ('clean','patterns'):
            path=folder/profile/stage
            if not path.with_suffix('.json').exists():save(path,build(profile,141_000_000+pi*10000+(stage=='patterns')*100,stage=stage))
        for i in range(12):
            path=folder/profile/f'mixed_{i:02d}'
            if not path.with_suffix('.json').exists():save(path,build(profile,142_000_000+pi*10000+i*100))
        path=folder/profile/'dev'
        if not path.with_suffix('.json').exists():
            b=Builder(profile,151_000_000+pi*10000)
            for c in conditions(profile):
                for j in range(32):
                    payload=([0,255,85,170]*2 if j==0 else b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist())
                    if c=='address_nack':payload=[]
                    b.message(payload,c)
            errors=['framing','break']+(['parity'] if profile=='uart_e' else []) if profile.startswith('uart') else ['partial']
            for j in range(12):
                b.message([int(b.rng.integers(0,256))],invalid=errors[j%len(errors)])
                b.message(b.rng.integers(0,256,4).tolist());b.idle(4096)
            s=b.finish();s['x']=features(s['lines'])[0];s['seed']=151_000_000+pi*10000;save(path,s)
        print('data ready',profile,flush=True)


def generate_uart_curriculum(folder):
    for pi,profile in enumerate(('uart_n','uart_e')):
        for si,stage in enumerate(('constant','four_patterns','single_bytes','simple_dev','nominal_dev')):
            base=folder/profile/stage
            if base.with_suffix('.json').exists():continue
            b=Builder(profile,153000000+pi*10000+si*100)
            i=0
            while len(b.lines)<32768:
                if stage in ('constant','simple_dev'):payload=[0]
                elif stage=='four_patterns':payload=[(0,255,85,170)[i%4]]
                elif stage=='single_bytes':payload=[int(b.rng.integers(0,256))]
                else:payload=b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist()
                b.message(payload);i+=1
            s=b.finish();s['x']=features(s['lines'])[0];s['seed']=153000000+pi*10000+si*100;save(base,s)
