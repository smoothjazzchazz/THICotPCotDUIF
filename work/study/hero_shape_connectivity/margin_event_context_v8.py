"""Check whether canonical-label conflicts concern harmless held event classes."""
import json,shutil
import numpy as np
from .run import ROOT,digest
from .data import load
from .train import write_json


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';folder=root/'diagnostics/margin_certificate_v8_n131';certificate=json.loads((folder/'result.json').read_text())
    a=np.load(certificate['source']);dual=np.load(folder/'solution_and_dual.npz');y=a['support_y'];ids=a['support_ids'];lam=dual['row_multipliers']
    others=np.broadcast_to(np.arange(6),(len(y),6))[np.arange(6)[None,:]!=y[:,None]]
    pool=json.loads((root/'closure_v6_uart_n_pool.json').read_text())['paths'];active=np.flatnonzero(lam>1e-10);jobs={}
    for row in active:
        index=int(row//5);identity=int(ids[index]);fi=identity//(1<<32);tick=identity%(1<<32)
        jobs.setdefault(fi,[]).append((int(row),index,tick))
    rows=[]
    for fi,points in sorted(jobs.items()):
        path=pool[fi]['path'];data=load(path[:-5]);truth=data['labels'];events=np.flatnonzero(truth)
        for row,index,tick in points:
            before=events[events<tick];after=events[events>tick]
            previous=int(before[-1]) if len(before) else None;following=int(after[0]) if len(after) else None
            rows.append(dict(file_index=fi,path=path,tick=tick,target=int(y[index]),competitor=int(others[row]),multiplier=float(lam[row]),
                previous_event_tick=previous,previous_event_class=None if previous is None else int(truth[previous]),ticks_after_previous=None if previous is None else tick-previous,
                next_event_tick=following,next_event_class=None if following is None else int(truth[following]),ticks_before_next=None if following is None else following-tick,
                input_levels=data['lines'][tick].tolist()))
    groups={}
    for r in rows:
        if r['target']==0:
            label=f"previous={r['previous_event_class']},distance={r['ticks_after_previous']}";groups[label]=groups.get(label,0)+1
    source_copy=folder/'margin_event_context_v8_at_run.py'
    if source_copy.exists():assert digest(source_copy)==digest(__file__)
    else:shutil.copy2(__file__,source_copy)
    report=dict(source_sha256=digest(source_copy),certificate_sha256=digest(folder/'result.json'),scope='offline audit of strict canonical labels versus original event pulses; no interface or qualification change',none_context_counts=groups,rows=rows)
    write_json(folder/'event_context.json',report);print(json.dumps(groups),flush=True)
