"""Event timing and off-chip phase-head diagnostics, without changing a gate."""
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from .run import ROOT
from .shapes import make_shape
from .data import load
from .runtime import run,pulses
from .teacher import timing_targets
from .train import write_json


def analyze(root):
    rows=[]
    for recipe in ('phase_aux','phase_circulation','phase_clock'):
        for folder in sorted((root/'models'/recipe).glob('*/*/*')):
            blocks=sorted(folder.glob('block_*.json'))
            if not blocks:continue
            b=json.loads(blocks[-1].read_text());sh=make_shape(**b['construction']);d=load(root/'data'/b['profile']/'dev')
            path=folder/f"epoch_{b['epochs']:04d}.npz";a=np.load(path);p=a['p'];targets=timing_targets(d['lines'],b['profile']);offset=len(p)-6*sh.n-6
            heads=[]
            for i in range(3):
                q=p.copy();q[offset:]=a['aux_weights'][i];pred=run(sh,q,d['x'])[2].argmax(1)
                active=(targets[i]>=1)&(targets[i]<=4)
                heads.append(dict(overall_accuracy=float(np.mean(pred==targets[i])),active_accuracy=float(np.mean(pred[active]==targets[i,active]))))
            rows.append(dict(recipe=recipe,shape=sh.name,profile=b['profile'],seed=b['seed'],epoch=b['epochs'],heads=heads,
                note='off-chip diagnostic heads only; these accuracies are not reception qualification'))
    write_json(root/'diagnostics'/'phase_head_accuracy.json',rows)
    profile='uart_n';sh=make_shape('sss');folder=root/'models'/'matched'/sh.name/profile/'11'
    b=json.loads(sorted(folder.glob('block_*.json'))[-1].read_text());p=np.load(b['checkpoint'])['p'];d=load(root/'data'/profile/'dev')
    pred=pulses(run(sh,p,d['x'])[2].argmax(1));np.savez_compressed(root/'diagnostics'/'current_uart_baseline_trace.npz',predicted=pred,expected=d['labels'])
    g=d['groups'][0];begin=max(0,g['start']-8);end=min(g['end']+8,begin+650);x=np.arange(begin,end)
    fig,axes=plt.subplots(3,1,figsize=(12,5),sharex=True)
    axes[0].step(x,d['lines'][begin:end,0],where='post',color='#315c9b');axes[0].set_ylabel('RX')
    for ax,values,label,color in [(axes[1],d['labels'],'Reference','#008b72'),(axes[2],pred,'Learned','#bb5522')]:
        t=np.flatnonzero(values[begin:end])+begin;ax.scatter(t,values[t],color=color,s=14);ax.vlines(t,0,values[t],color=color,lw=.7)
        ax.set_ylabel(label);ax.set_yticks([1,2,3,4,5],['0','1','START','STOP','INVALID']);ax.grid(alpha=.15)
    axes[-1].set_xlabel('Sample tick; continuous state, no supplied frame reset')
    fig.suptitle('UART failures remain event-count and boundary failures, not just lower loss');fig.tight_layout()
    fig.savefig(root/'figures'/'uart_causal_events.png',dpi=170);plt.close(fig)
    print('phase diagnostics and UART trace retained',len(rows))

if __name__=='__main__':analyze(ROOT/'runs'/'connectivity01')
