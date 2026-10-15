"""Train/dev-only recipe comparison. No final cases or selected final evidence."""
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import initial_weights, MASK, StreamReceiver, features, LEAKS
from work.study.protocol_reservoir64.training import batch, class_weights, loss_gradient
from .training import write_json, adam_step, dev_event_scores, live_dev, MULTIPLIERS
from .metrics import aggregate, selection_key
from .data import load_split
from .audit import credit_trace
from work.study.protocol_reservoir64.profiles import load_config


def initialize(seed, recipe):
    w = initial_weights(seed)
    if recipe != 'previous':
        # Only parameter initialization changes. Self edges already exist in MASK.
        w['wx'] *= .2
        w['wh'] *= .1
        np.fill_diagonal(w['wh'], .95 if recipe == 'memory095' else 1.05)
        w['bo'][0] = .5
    assert not np.any(w['wh']*(1-MASK))
    return w


def investigate(output):
    output=Path(output); directory=output/'investigation'; directory.mkdir(exist_ok=True)
    results=[]
    for profile in ('uart_n','uart_e'):
        streams=load_split(output,profile,'train'); devstreams=load_split(output,profile,'dev')
        # Fixed prefix subset, all twelve streams, two passes. Diagnostic budget is separate.
        x,y,valid=batch(streams); x,y,valid=x[:8192],y[:8192],valid[:8192]
        dev=batch(devstreams); weights=class_weights(y,valid)*MULTIPLIERS
        for recipe in ('previous','memory095','memory105'):
            w=initialize(11,recipe); m,v=({k:np.zeros_like(a) for k,a in w.items()} for _ in range(2))
            credit=credit_trace(w,streams[0]['lines']); step=0; history=[]
            for epoch in range(1,3):
                state=np.zeros((12,64))
                for a in range(0,len(x),512):
                    loss,state,g=loss_gradient(w,x[a:a+512],y[a:a+512],valid[a:a+512],state,weights)
                    step+=1; adam_step(w,g,m,v,step)
                loss,events=dev_event_scores(w,devstreams,dev,weights,profile)
                rows=live_dev(w,profile,load_config(output,profile)); summary=aggregate(rows)
                history.append(dict(epoch=epoch,dev_loss=loss,live=summary,selection_key=list(selection_key(summary,loss))))
                print(json.dumps(dict(pilot=recipe,profile=profile,epoch=epoch,loss=loss,boundary=summary['boundary_f1'])),flush=True)
            from work.model.stream_reservoir import save_weights
            save_weights(directory/f'{profile}_{recipe}.npz',w,seed=11,epoch=2,recipe=recipe)
            results.append(dict(profile=profile,recipe=recipe,history=history,initial_credit=credit,updates=step,nonpadding_presentations=int(valid.sum())*2))
    # One shared initialization recipe for both UART profiles. Rank by pooled protocol metrics.
    ranks={}
    for recipe in ('previous','memory095','memory105'):
        rows=[r['history'][-1] for r in results if r['recipe']==recipe]
        ranks[recipe]=[sum(r['selection_key'][k] for r in rows) for k in range(7)]
    selected=max(ranks,key=lambda k:tuple(ranks[k]))
    write_json(directory/'pilots.json',dict(results=results,ranks=ranks,selection_rule='sum profile protocol selection keys after two prefix epochs'))
    write_json(output/'recipe.json',dict(selected=selected,initialization_candidates=['previous','memory095','memory105'],
        rationale='Test small-input near-identity existing self-edge initialization against vanishing complete-frame credit; no inference equation, state, feature or mask change.',
        selection='Pooled train/dev pilot protocol score, selected before main runs; final unseen.',
        epochs=30,chunk=512,batch=12,lr=.003,loss='previous30 weighted, unchanged',
        control='seed11 previous30 initialization and weighted loss, same corpus/budget',
        pilot_updates=sum(r['updates'] for r in results),pilot_presentations=sum(r['nonpadding_presentations'] for r in results)))
    print('SELECTED '+selected,flush=True)

if __name__=='__main__':
    import sys
    investigate(Path(sys.argv[1]))
