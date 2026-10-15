"""Bounded-memory state interventions on frozen failures; never a receiver reset."""
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,features
from .data import load
from .runtime import run,pulses
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';out=root/'confirmations'/'full_shape_v2a';frozen=json.loads((out/'freeze.json').read_text());records=[]
    for profile,seed,condition,tick in [('uart_n',131,'minus_jitter',914662),('uart_e',131,'minus_jitter',863482)]:
        e=next(e for e in frozen['entries'] if e['profile']==profile and e['seed']==seed);sh=make_shape(**e['construction']);a=np.load(out/e['weight_path']);p=a['p'];sh.leaks=a['leaks'].copy()
        s=load(out/'data'/f'{profile}_{condition}');raw=np.load(out/'results'/sh.name/profile/f'float_{seed}'/f'{condition}_trace.npz')['predicted'];original=pulses(raw)
        horizons=[256,512,1024,2048];starts=sorted(tick-h for h in horizons);states={};h=np.zeros(sh.n);begin=0
        for end in starts:
            for t in range(begin,end,8192):h=run(sh,p,s['x'][t:min(t+8192,end)],h=h)[1]
            states[end]=h.copy();begin=end
        idle=run(sh,p,features(np.ones((4096,3),dtype=np.uint8))[0])[1];rows=[];end=min(len(raw),tick+512)
        for horizon in horizons:
            start=tick-horizon
            for group,nodes in [('all',range(sh.n))]+[(f'layer{i+1}',nodes) for i,nodes in enumerate(sh.groups)]:
                for replacement,values in [('zero',np.zeros(sh.n)),('idle',idle)]:
                    before=states[start].copy();before[list(nodes)]=values[list(nodes)]
                    z=run(sh,p,s['x'][start:end],h=before)[2];ev=pulses(z.argmax(1),int(raw[start-1]));lo=max(start,tick-192)
                    truth=s['labels'][lo:end];pred=ev[lo-start:];base=original[lo:end]
                    boundary=lambda v:int(np.sum((v!=truth)&(np.isin(v,[3,4])|np.isin(truth,[3,4]))))
                    rows.append(dict(horizon=horizon,layer=group,replacement=replacement,target=int(s['labels'][tick]),original_event=int(original[tick]),event=int(ev[tick-start]),
                        window_start=lo,window_end=end,pulse_errors=int(np.sum(pred!=truth)),original_pulse_errors=int(np.sum(base!=truth)),
                        boundary_errors=boundary(pred),original_boundary_errors=boundary(base)))
        record=dict(profile=profile,seed=seed,condition=condition,tick=tick,checkpoint_sha256=e['weight_sha256'],interventions=rows);records.append(record)
        print(profile,seed,[(r['horizon'],r['layer'],r['replacement'],r['pulse_errors'],r['original_pulse_errors']) for r in rows if r['pulse_errors']<r['original_pulse_errors']][:20],flush=True)
    write_json(root/'diagnostics'/'fresh_context_interventions_v2a.json',dict(records=records,
        scope='diagnostic only: identical subsequent features, selected past state replaced; no reset or oracle information is added to inference; not a complete-message qualification',
        context='frozen failed confirmation; examples never used to fit weights',source_sha256=digest(__file__)))
