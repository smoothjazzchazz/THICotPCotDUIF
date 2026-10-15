"""One-parameter boundary separability diagnostic; no fitting on development."""
import argparse,json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load
from .train import evaluate_stream,write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('block',type=Path);ap.add_argument('--label',required=True);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';out=root/'diagnostics'/a.label;out.mkdir(parents=True,exist_ok=False)
    b=json.loads(a.block.read_text());sh=make_shape(**b['construction']);m=np.load(b['checkpoint']);p=m['p'];sh.leaks=m['leaks'].copy()
    lower=-np.inf;upper=np.inf;forbidden=[];weak_true=None;strong_false=None
    for file in sorted((root/'data_precision_v2'/b['profile']/'dev').glob('*.json')):
        s=load(file.with_suffix(''));_,z=evaluate_stream(sh,p,s,np.ones(6));tau=np.max(np.delete(z,4,axis=1),axis=1)-z[:,4];previous=np.r_[np.inf,tau[:-1]]
        scored=np.arange(len(tau))>=s.get('startup_ambiguous_until',0);true=(s['labels']==4)&scored;false=(s['labels']!=4)&scored&(tau<previous)
        if true.any():
            t=int(np.flatnonzero(true)[np.argmax(tau[true])])
            if tau[t]>lower:lower=float(tau[t]);weak_true=dict(case=file.stem,tick=t,required_offset_at_least=lower)
            upper=min(upper,float(np.min(previous[true])))
        for t in np.flatnonzero(false):forbidden.append((float(tau[t]),float(previous[t]),file.stem,int(t)))
    intervals=sorted((max(lower,lo),min(upper,hi),case,t) for lo,hi,case,t in forbidden if lo<upper and hi>lower)
    available=[];cursor=lower;cover=[]
    for lo,hi,case,t in intervals:
        if lo>cursor:available.append([cursor,lo])
        if hi>cursor:cursor=hi;cover.append(dict(start=lo,end=hi,case=case,tick=t))
    if cursor<upper:available.append([cursor,upper])
    result=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(a.block),
        required_interval=[lower,upper],available_stop_onset_intervals=available,weakest_true_stop=weak_true,covering_false_onsets=cover,
        scope='development-only analytic diagnostic of shifting existing STOP bias; weights unchanged; any candidate offset still needs every event/message gate')
    write_json(out/'intervals.json',result);print(json.dumps(result),flush=True)
