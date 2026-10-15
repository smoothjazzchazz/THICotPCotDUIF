"""Training-label alternatives that preserve every original event pulse exactly."""
import json,shutil
import numpy as np
from .run import ROOT,digest
from .runtime import pulses
from .linear_margin_diagnostic import solve
from .train import write_json


def held_bit_labels(labels,extension):
    if extension not in (1,2):raise ValueError('declared one/two-tick generic bit holds only')
    out=labels.copy()
    for t in np.flatnonzero(np.isin(labels,[1,2])):
        for j in range(t+1,min(len(labels),t+1+extension)):
            if labels[j]!=0:break
            out[j]=labels[t]
    if not np.array_equal(pulses(out),labels):raise ValueError('held class changed a required event pulse')
    return out


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';source=next((root/'models/phase_linear_closure_v8').glob('*/uart_n/131/epoch_0003.npz'))
    out=root/'diagnostics/bit_hold_v9_n131';out.mkdir(exist_ok=True);source_copy=out/'bit_hold_diagnostic_v9_at_run.py'
    if source_copy.exists():assert digest(source_copy)==digest(__file__)
    else:shutil.copy2(__file__,source_copy)
    a=np.load(source);x=a['support_x'];y=a['support_y'];ids=a['support_ids'];pool=json.loads((root/'closure_v6_uart_n_pool.json').read_text())['paths']
    variants={extension:y.copy() for extension in (1,2)};counts={1:0,2:0}
    for fi in np.unique(ids//(1<<32)):
        take=np.flatnonzero(ids//(1<<32)==fi);ticks=ids[take]%(1<<32);path=pool[int(fi)]['path']
        with np.load(path[:-5]+'.npz') as data:labels=data['labels']
        assert np.array_equal(labels[ticks],y[take]),'support label provenance mismatch'
        for extension in (1,2):
            held=held_bit_labels(labels,extension);variants[extension][take]=held[ticks];counts[extension]+=int(np.sum(held!=labels))
    records=[]
    for extension,target in variants.items():
        record,w=solve(x,target,a['w'],None)
        record.update(extension=extension,changed_retained_labels=int(np.sum(target!=y)),changed_complete_training_ticks=counts[extension],source=str(source),source_sha256=digest(source),
            scope='fixed training-state margin diagnostic; held bit labels have exactly identical pulses on every source file; no acceptance relaxation')
        if w is not None:np.savez_compressed(out/f'extension_{extension}.npz',weights=w,training_labels=target)
        write_json(out/f'extension_{extension}.json',record);records.append(record);print(json.dumps(record),flush=True)
    write_json(out/'summary.json',dict(source_sha256=digest(source_copy),rows=records))
