"""Readout-margin diagnostic; does not modify or qualify a configuration."""
import argparse
import json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load,metrics
from .runtime import pulses
from .train import evaluate_stream,write_json


def inspect(block,output,root):
    output.mkdir(parents=True,exist_ok=False)
    b=json.loads(block.read_text());sh=make_shape(**b['construction']);a=np.load(b['checkpoint']);p=a['p'];sh.leaks=a['leaks'].copy()
    data=load(root/('data_extended' if b.get('development_distribution')=='extended' else 'data')/b['profile']/'dev')
    _,z=evaluate_stream(sh,p,data,np.ones(6));k=z.argmax(1);pred=pulses(k);y=data['labels'];base=metrics(data,k)
    bad=np.flatnonzero((np.isin(y,[3,4])|np.isin(pred,[3,4]))&(y!=pred))
    bad=bad[bad>=data.get('startup_ambiguous_until',0)]
    windows=[];probes=[0.]
    for tick in bad[:64]:
        lo=max(0,tick-4);hi=min(len(y),tick+5)
        margin=float(z[tick,int(k[tick])]-z[tick,0])
        windows.append(dict(tick=int(tick),expected=int(y[tick]),predicted=int(pred[tick]),none_margin=margin,
            rx=data['lines'][lo:hi,0].tolist(),truth=y[lo:hi].tolist(),classes=k[lo:hi].tolist(),logits=z[lo:hi].tolist()))
        if 0<margin<1:probes.extend([margin+1e-6,margin+.001,margin+.01])
    rows=[]
    for delta in sorted(set(probes)):
        zz=z.copy();zz[:,0]+=delta;r=metrics(data,zz.argmax(1));r['none_bias_delta']=delta
        r['no_new_event_errors']=r['false_events']<=base['false_events'] and r['missed_events']<=base['missed_events']
        rows.append(r)
    write_json(output/'diagnosis.json',dict(source_block=str(block),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
        boundary_windows=windows,base=base,probes=rows,
        status='development-only readout-margin ablation; no weights changed and no qualification claim'))
    print([(r['none_bias_delta'],r['message_accuracy'],r['boundary_errors'],r['no_new_event_errors']) for r in rows],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('block',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
    inspect(a.block,a.output,ROOT/'runs'/'connectivity01')
