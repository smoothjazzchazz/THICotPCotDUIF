"""Causal event/logit windows for the corrected development distribution."""
import argparse
import json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .data import load
from .shapes import make_shape
from .train import evaluate_stream,write_json
from .runtime import pulses

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('block',type=Path);ap.add_argument('--label',required=True);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';out=root/'diagnostics'/a.label;out.mkdir(parents=True,exist_ok=False)
    b=json.loads(a.block.read_text());sh=make_shape(**b['construction']);model=np.load(b['checkpoint']);p=model['p'];sh.leaks=model['leaks'].copy();cases=[]
    for case in b['selected']['cases']:
        if case['exact_messages']==case['valid_messages'] and case['boundary_errors']==0:continue
        s=load(root/'data_precision_v2'/b['profile']/'dev'/case['case']);_,z=evaluate_stream(sh,p,s,np.ones(6));pred=pulses(z.argmax(1));y=s['labels']
        bad=np.flatnonzero((y!=pred)&(np.arange(len(y))>=s.get('startup_ambiguous_until',0)));windows=[]
        for tick in bad[:128]:
            true_start=np.flatnonzero(y[:tick+1]==3);start=int(true_start[-1]) if len(true_start) else None
            group=next((g for g in s['groups'] if g['start']<=tick<g['end']),None);lo=max(0,int(tick)-20);hi=min(len(y),int(tick)+21)
            windows.append(dict(tick=int(tick),expected=int(y[tick]),predicted=int(pred[tick]),since_true_start=None if start is None else int(tick)-start,
                group=group,window_start=lo,rx=s['lines'][lo:hi,0].tolist(),truth=y[lo:hi].tolist(),events=pred[lo:hi].tolist(),
                logits=z[lo:hi].tolist(),none_margin=float(z[tick,z[tick].argmax()]-z[tick,0])))
        cases.append(dict(case=case['case'],score=case,windows=windows))
        print(case['case'],[(w['tick'],w['expected'],w['predicted'],w['since_true_start'],round(w['none_margin'],3)) for w in windows[:12]],flush=True)
    write_json(out/'errors.json',dict(source_block=str(a.block),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),cases=cases,
        scope='verified development only; diagnostic does not change weights or qualification gates'))
