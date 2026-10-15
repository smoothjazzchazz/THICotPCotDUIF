"""Long continuous UART traffic and cold mid-frame startup coverage."""
import numpy as np
from .run import ROOT,digest
from .data import load,save,conditions
from .vendor.data import Builder,reference_labels,assemble
from .runtime import events
from .shapes import features
from .train import write_json


def finish_cut(builder,cut):
    full=builder.finish();lines=full['lines'][cut:];labels=reference_labels(lines,builder.profile)
    truth,rejected=assemble(events(labels),builder.profile)
    groups=[{**g,'start':g['start']-cut,'end':g['end']-cut} for g in full['groups'][1:]]
    return dict(lines=lines,labels=labels,x=features(lines)[0],truth=truth,groups=groups,profile=builder.profile,
        reference_rejections=rejected,startup_ambiguous_until=groups[0]['start'])


def build(profile,seed,bank,development=False):
    b=Builder(profile,seed);b.message(b.rng.integers(0,256,4).tolist())
    cut=b.groups[0]['start']+int(b.rng.integers(17,145));choices=conditions(profile)
    if development:
        for condition in choices:
            for j in range(32):
                payload=b.rng.integers(0,256,1024 if j==0 else 256 if j==1 else int(b.rng.integers(1,9))).tolist()
                if j==2:payload=[(0,255,85,170)[choices.index(condition)%4]]*64
                b.message(payload,condition)
    else:
        condition=choices[bank%len(choices)]
        payload=b.rng.integers(0,256,1024).tolist() if bank%3 else [(0,255,85,170)[bank//3%4]]*1024
        b.message(payload,condition)
    errors=['framing','break']+(['parity'] if profile=='uart_e' else [])
    for j in range(24):
        b.message([int(b.rng.integers(0,256))],invalid=errors[j%len(errors)])
        b.message(b.rng.integers(0,256,4).tolist());b.idle(4096 if j%8==0 else 17)
    i=0
    while not development and len(b.lines)-cut<262144:
        condition=choices[i%len(choices)]
        payload=b.rng.integers(0,256,int(b.rng.integers(1,17))).tolist()
        if i%11==0:payload=[(0,255,85,170)[i//11%4]]*64
        b.message(payload,condition);i+=1
    stream=finish_cut(b,cut);stream['seed']=seed;stream['startup_cut']=cut
    return stream


def generate(root):
    folder=root/'data_extended'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for i in range(12):
            p=folder/profile/f'mixed_{i:02d}'
            if not p.with_suffix('.json').exists():save(p,build(profile,223000000+pi*100000+i*100,i))
        p=folder/profile/'dev'
        if not p.with_suffix('.json').exists():save(p,build(profile,224000000+pi*100000,0,True))
        print('Extended coverage generated',profile,flush=True)
    write_json(folder/'manifest.json',dict(training_family=223000000,development_family=224000000,
        confirmation_family_not_reused=211000000,
        purpose='continuous 1024-byte traffic, repeated patterns, mid-frame cold startup and invalid recovery',
        files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}))

if __name__=='__main__':generate(ROOT/'runs'/'connectivity01')
