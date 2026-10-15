"""Disjoint broad timing development and many independent cold-start cases."""
import json
import numpy as np
from .run import ROOT,digest
from .data import conditions,save,load,metrics
from .vendor.data import Builder
from .extended_data import finish_cut
from .shapes import features
from .train import write_json


def evaluate(shape,p,root,profile,cw,corpus='data_precision'):
    from .train import evaluate_stream
    cases=[];total_loss=0.;ticks=0
    fields=('exact_messages','valid_messages','byte_exact_messages','boundary_errors','invalid_accepted','background_accepted','false_events','missed_events')
    total={k:0 for k in fields};total['conditions']={}
    for base in sorted((root/corpus/profile/'dev').glob('*.json')):
        s=load(base.with_suffix(''));loss,z=evaluate_stream(shape,p,s,cw);r=metrics(s,z.argmax(1));r['case']=base.stem;cases.append(r)
        total_loss+=loss*len(z);ticks+=len(z)
        for k in fields:total[k]+=r[k]
        for condition,row in r['conditions'].items():
            dest=total['conditions'].setdefault(condition,dict(valid_messages=0,exact_messages=0,byte_exact_messages=0))
            for k in ('valid_messages','exact_messages','byte_exact_messages'):dest[k]+=row[k]
    for row in total['conditions'].values():row['message_accuracy']=row['exact_messages']/row['valid_messages']
    total['message_accuracy']=total['exact_messages']/total['valid_messages']
    # This field is diagnostic only; selection uses exact errors, not F1.
    total['boundary_f1']=min(r['boundary_f1'] for r in cases)
    total['cases']=cases;total['ticks']=ticks
    return total_loss/ticks,total


def cold(profile,seed,count=8):
    b=Builder(profile,seed);b.message(b.rng.integers(0,256,4).tolist())
    cut=b.groups[0]['start']+int(b.rng.integers(1,b.groups[0]['end']-b.groups[0]['start']-1))
    for i in range(count):
        if i%3==2:b.message([int(b.rng.integers(256))],invalid=['framing','break'][i%2])
        b.message(b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist(),conditions(profile)[i%7])
    s=finish_cut(b,cut);s['seed']=seed;s['startup_cut']=cut;return s


def generate(root):
    folder=root/'data_precision'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for i,c in enumerate(conditions(profile)):
            base=folder/profile/'dev'/c
            if base.with_suffix('.json').exists():continue
            b=Builder(profile,303000000+pi*100000+i*1000)
            for j in range(256):
                payload=b.rng.integers(0,256,1024 if j==0 else int(b.rng.integers(1,9))).tolist()
                if j==1:payload=list(range(256))
                elif 2<=j<6:payload=[(0,255,85,170)[j-2]]*64
                b.message(payload,c)
            s=b.finish();s['x']=features(s['lines'])[0];save(base,s)
        for i in range(64):
            base=folder/profile/'dev'/f'cold_{i:03d}'
            if not base.with_suffix('.json').exists():save(base,cold(profile,304000000+pi*100000+i*100,8))
        for i in range(256):
            base=folder/profile/'train'/f'cold_{i:03d}'
            if not base.with_suffix('.json').exists():save(base,cold(profile,301000000+pi*100000+i*100,8))
        print('Precision/startup coverage ready',profile,flush=True)
    write_json(folder/'manifest.json',dict(training_family=301000000,development_families=[303000000,304000000],
        confirmation_family_excluded=261000000,policy='each file is one independently cold-started continuous stream; no resets within a stream',
        files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}))

if __name__=='__main__':generate(ROOT/'runs'/'connectivity01')
