"""Read-only causal traces of the frozen reduced-head pause failures."""
import json,os
import numpy as np
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .run import ROOT,digest
from .shapes import make_shape
from .data import load
from .readout_probe import trajectory
from .head_learning_v16 import backbone,logits
from .train import write_json


def report():
    root=ROOT/'runs/connectivity01';folder=root/'confirmations/readout_cost_full_v3a';freeze=json.loads((folder/'freeze.json').read_text());manifest=json.loads((folder/'data/manifest.json').read_text());rows=[]
    for profile,seed in [('spi1',47),('spi1',101),('spi2',47)]:
        entries=[next(e for e in freeze['entries'] if e['profile']==profile and e['seed']==seed and e['shape'].endswith(cell)) for cell in ('readout16_dense','readout16_fanin32_fast')]
        result_paths=[folder/'results'/e['shape']/profile/f'float_{seed}'/'pauses.json' for e in entries]
        result=json.loads(result_paths[1].read_text());tick=result['first_event_errors'][0]['tick'];start=max(0,tick-140);end=tick+35
        case=next(c for c in manifest if c['profile']==profile and c['condition']=='pauses');s=load(folder/'data'/case['name']);models=[];states=[]
        for entry in entries:
            file=folder/entry['weight_path'];assert digest(file)==entry['weight_sha256'];a=np.load(file);sh=make_shape(**entry['construction']);sh.leaks=a['leaks'];base,p,stamp=backbone(sh,a['p']);models.append((sh,a['p']));states.append((base,p,stamp))
        assert states[0][2]==states[1][2] and np.array_equal(states[0][1],states[1][1]),'paired backbone differs'
        h=trajectory(states[0][0],states[0][1],s['x'][:end]);window=h[start:end];del h
        predicted=[];margins=[]
        for (sh,p),entry in zip(models,entries):
            z=logits(sh,p,window);actual=z.argmax(1);saved=np.load(folder/'results'/entry['shape']/profile/f'float_{seed}'/'pauses_trace.npz')['predicted'][start:end]
            assert np.array_equal(actual,saved),'diagnostic disagrees with frozen scalar replay';predicted.append(actual)
            truth=z[np.arange(len(z)),s['labels'][start:end]].copy();z[np.arange(len(z)),s['labels'][start:end]]=-np.inf;margins.append(truth-z.max(1))
        row=dict(profile=profile,seed=seed,tick=tick,window_start=start,window_end=end,backbone_sha256=states[0][2],backbone_identical=True,
                 expected_class=int(s['labels'][tick]),dense_class=int(predicted[0][tick-start]),reduced_class=int(predicted[1][tick-start]),
                 dense_correct_class_margin=float(margins[0][tick-start]),reduced_correct_class_margin=float(margins[1][tick-start]),
                 frozen_results=[str(p) for p in result_paths],interpretation='same continuous backbone state, different trained nonlinear/output mapping; local failure does not demonstrate insufficient recurrent memory')
        rows.append(row);fig,axes=plt.subplots(3,1,figsize=(11,6),sharex=True);t=np.arange(start,end)-tick
        for lane,label in enumerate(('clock','select (low active)','data')):axes[0].step(t,s['lines'][start:end,lane]+lane*1.4,where='post',label=label)
        axes[0].set_yticks([]);axes[0].legend(loc='upper left',ncol=3,fontsize=8)
        axes[1].step(t,s['labels'][start:end],where='post',label='Expected event',color='black',lw=2)
        for i,label in enumerate(('Dense','Reduced')):axes[1].step(t,predicted[i]+(.07 if i else 0),where='post',label=label,alpha=.8);axes[2].plot(t,margins[i],label=label)
        axes[1].set_yticks(range(6),['NONE','BIT0','BIT1','START','STOP','INVALID']);axes[1].legend(loc='upper left',ncol=3,fontsize=8)
        axes[2].axhline(0,color='black',lw=.7);axes[2].set_ylabel('Correct-class margin');axes[2].set_xlabel('Samples relative to first incorrect event');axes[2].legend(fontsize=8)
        for ax in axes:ax.axvline(0,color='red',alpha=.3);ax.grid(alpha=.15)
        fig.suptitle(f'{profile}, seed {seed}: identical backbone; reduced head changes the decision at sample {tick}')
        fig.tight_layout();fig.savefig(root/'figures'/f'pause_failure_v20_{profile}_{seed}.png',dpi=150);plt.close(fig)
    write_json(root/'pause_failure_diagnostic_v20.json',dict(confirmation='readout_cost_full_v3a',purpose='read-only diagnostic, never a training bank',traces=rows));print(json.dumps(rows),flush=True)


if __name__=='__main__':report()
