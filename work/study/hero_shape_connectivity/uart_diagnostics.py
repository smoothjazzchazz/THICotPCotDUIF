"""Selected-checkpoint causal traces; no waveform interpretation in inference."""
import argparse
import json
from pathlib import Path
import numpy as np
from .data import load,metrics
from .run import ROOT,digest
from .runtime import run,pulses,events
from .shapes import make_shape
from .teacher import timing_targets
from .train import write_json
from .vendor.data import assemble


def inspect(block,output,root):
    output.mkdir(parents=True,exist_ok=False)
    b=json.loads(block.read_text());sh=make_shape(**b['construction'])
    a=np.load(b['checkpoint']);p=a['p']
    if 'leaks' in a:sh.leaks=a['leaks'].copy()
    d=load(root/'data'/b['profile']/'dev');z=run(sh,p,d['x'])[2]
    kinds=z.argmax(1);pred=pulses(kinds);truth=d['labels']
    got,_=assemble(events(pred),b['profile'])
    failures=[]
    for group in d['groups']:
        expected=[x for x in d['truth'] if group['start']<=x['start']<group['end']]
        received=[x for x in got if group['start']<=x['start']<group['end']]
        if expected!=received:failures.append(dict(group=group,expected=expected,received=received))
    heads=[];aux_pred=[];targets=timing_targets(d['lines'],b['profile']);offset=len(p)-6*sh.n-6
    for i in range(3):
        ap=p.copy();ap[offset:]=a['aux_weights'][i];q=run(sh,ap,d['x'])[2].argmax(1);aux_pred.append(q)
        active=(targets[i]>0)&(targets[i]<5)
        heads.append(dict(active_accuracy=float(np.mean(q[active]==targets[i,active])),all_accuracy=float(np.mean(q==targets[i]))))
    timing={}
    for kind in range(1,6):
        expected=np.flatnonzero(truth==kind);actual=np.flatnonzero(pred==kind);counts={str(i):0 for i in range(-8,9)};missing=0
        for tick in expected:
            candidates=actual[np.abs(actual-tick)<=8]
            if len(candidates):counts[str(int(candidates[np.argmin(np.abs(candidates-tick))]-tick))]+=1
            else:missing+=1
        timing[str(kind)]=dict(nearest_same_kind_within_eight_ticks=counts,no_nearby_event=missing,expected=len(expected),actual=len(actual))
    report=dict(block=str(block),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),shape=sh.name,
        profile=b['profile'],seed=b['seed'],selected_epoch=b['selected_epoch'],metrics=metrics(d,kinds),
        auxiliary_heads=heads,timing=timing,failures=failures,
        caveat='Nearest-event timing is diagnostic and may reuse an actual event; exact gates remain unchanged.')
    np.savez_compressed(output/'events.npz',expected=truth,predicted=pred,classes=kinds,logits=z,auxiliary=np.array(aux_pred),auxiliary_targets=targets)
    for j,f in enumerate(failures[:4]):
        start=max(0,f['group']['start']-32);end=min(len(d['x']),f['group']['end']+32)
        h=run(sh,p,d['x'][:start])[1] if start else np.zeros(sh.n);states=[]
        for tick in range(start,end):
            h=run(sh,p,d['x'][tick:tick+1],h=h)[1];states.append(h.copy())
        np.savez_compressed(output/f'failed_group_{j}.npz',ticks=np.arange(start,end),states=states,
            lines=d['lines'][start:end],features=d['x'][start:end],logits=z[start:end],expected=truth[start:end],predicted=pred[start:end])
    write_json(output/'diagnosis.json',report)
    print(json.dumps(dict(shape=sh.name,profile=b['profile'],seed=b['seed'],exact=report['metrics']['message_accuracy'],heads=heads)))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('block',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    inspect(a.block,a.output,ROOT/'runs'/'connectivity01')
