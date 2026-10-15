"""Diagnostic state interventions; no intervention is used by deployed inference."""
import argparse,json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,features
from .data import load
from .runtime import run,pulses
from .readout_probe import trajectory
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('block',type=Path);ap.add_argument('--label',required=True);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';out=root/'diagnostics'/a.label;out.mkdir(parents=True,exist_ok=False)
    b=json.loads(a.block.read_text());sh=make_shape(**b['construction']);z=np.load(b['checkpoint']);p=z['p'];sh.leaks=z['leaks'].copy();offset=sh.parameters-6*sh.n-6
    idle=features(np.ones((4096,3),dtype=np.uint8))[0];idle_state=run(sh,p,idle)[1];results=[]
    for case in b['selected']['cases']:
        if case['exact_messages']==case['valid_messages'] and case['boundary_errors']==0:continue
        s=load(root/'data_precision_v2'/b['profile']/'dev'/case['case']);h=trajectory(sh,p,s['x']);logits=h@p[offset:-6].reshape(6,sh.n).T+p[-6:];raw=logits.argmax(1);pred=pulses(raw)
        errors=np.flatnonzero((pred!=s['labels'])&(np.arange(len(pred))>=s.get('startup_ambiguous_until',0)))
        for tick in errors[:4]:
            target=int(s['labels'][tick]);rows=[]
            for horizon in (32,64,128,256,512,1024,4096,8192):
                start=max(0,int(tick)-horizon);original=np.zeros(sh.n) if start==0 else h[start-1]
                for name,nodes in [('all',list(range(sh.n)))]+[(f'layer{i+1}',g) for i,g in enumerate(sh.groups)]:
                    for replacement,values in [('zero',np.zeros(sh.n)),('idle',idle_state)]:
                        before=original.copy();before[nodes]=values[nodes]
                        rr=run(sh,p,s['x'][start:tick+1],h=before);k=rr[2].argmax(1);ev=pulses(k,int(raw[start-1]) if start else 0)
                        span=min(192,len(k));y=s['labels'][tick-span+1:tick+1]
                        competitors=np.delete(rr[2][-1],target)
                        rows.append(dict(horizon=horizon,start=start,layer=name,replacement=replacement,
                            target=target,raw=int(k[-1]),pulse=int(ev[-1]),margin=float(rr[2][-1,target]-max(competitors)),
                            last_span=span,pulse_errors=int(np.sum(ev[-span:]!=y)),
                            original_pulse_errors=int(np.sum(pred[tick-span+1:tick+1]!=y)),state_change_norm=float(np.linalg.norm(rr[1]-h[tick]))))
            result=dict(case=case['case'],tick=int(tick),target=target,original_pulse=int(pred[tick]),original_raw=int(raw[tick]),
                original_margin=float(logits[tick,target]-max(np.delete(logits[tick],target))),interventions=rows)
            results.append(result)
            fixed=[(r['horizon'],r['layer'],r['replacement'],r['pulse_errors'],r['original_pulse_errors']) for r in rows if r['pulse']==target and r['horizon']>=256]
            print(case['case'],int(tick),'target',target,'actual',int(pred[tick]),'corrected with older-state intervention',fixed[:20],flush=True)
    write_json(out/'interventions.json',dict(source_block=str(a.block),checkpoint_sha256=digest(b['checkpoint']),results=results,
        scope='diagnostic intervention at arbitrary past ticks, never a receiver feature or accepted recovery procedure; correction of one event is not qualification',
        comparison='identical subsequent generic input features; only the selected stored states are replaced'))
