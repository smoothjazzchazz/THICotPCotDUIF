"""Scalar causal gate trace; diagnostic implementation verified against inference."""
import json,math,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .runtime import run,pulses
from .data import load
from .train import write_json


def trace(sh,p,x):
    e=len(sh.src);n=sh.n;ge=len(sh.gate_src);gn=len(sh.gate_nodes);go=e+n;gb=go+ge;out=gb+gn
    state=np.zeros(n);states=[];gates=[];logits=[];edge=[np.flatnonzero(sh.dst==i) for i in range(n)];gate_edges=[np.flatnonzero(sh.gate_dst==i) for i in range(n)];gi={int(i):j for j,i in enumerate(sh.gate_nodes)}
    for row in x:
        old=state.copy();now=np.empty(n);rates=sh.leaks.copy()
        for i in range(n):
            z=float(p[e+i])
            for k in edge[i]:
                s=int(sh.src[k]);v=row[-1-s] if s<0 else old[s] if sh.delay[k] else now[s];z+=p[k]*v
            if i in gi:
                g=float(p[gb+gi[i]])
                for k in gate_edges[i]:g+=p[go+k]*old[sh.gate_src[k]]
                rates[i]=.5*(1+math.tanh(.5*g))
            now[i]=(1-rates[i])*old[i]+rates[i]*math.tanh(z)
        z=[]
        for k in range(6):
            value=float(p[out+6*n+k])
            for i in range(n):value+=p[out+k*n+i]*now[i]
            z.append(value)
        states.append(now.copy());gates.append(rates[sh.gate_nodes]);logits.append(z);state=now
    states=np.array(states);gates=np.array(gates);logits=np.array(logits);actual=run(sh,p,x)
    assert np.array_equal(states[-1],actual[1]) and np.array_equal(logits,actual[2]),'diagnostic arithmetic differs from deployed receiver'
    return states,gates,logits


if __name__=='__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=ROOT/'runs/connectivity01';out=root/'diagnostics/gate_trace_v6a';out.mkdir(parents=True,exist_ok=False)
    jobs=json.loads((root/'gate_bias_clamp_v6a_jobs.json').read_text());rows=[]
    for job in (jobs[0],jobs[3]):
        _,kw,profile,seed,source=job;b=json.loads(Path(source['source_block']).read_text())
        assert digest(b['checkpoint'])==source['checkpoint_sha256'];sh=make_shape(**kw);a=np.load(b['checkpoint']);sh.leaks=a['leaks'];s=load(root/'data_precision_v2'/profile/'dev/nominal');x=s['x'][:512]
        h,g,z=trace(sh,a['p'],x);pred=pulses(z.argmax(1));np.savez_compressed(out/f'{profile}_{seed}.npz',state=h,gates=g,logits=z,features=x,labels=s['labels'][:512],predicted=pred)
        rows.append(dict(profile=profile,seed=seed,source=source,scalar_bitwise_verified=True,gate_min=g.min(0).tolist(),gate_max=g.max(0).tolist(),scope='first512ticks of original nominal development; descriptive learned-weight trace only'))
        fig=plt.figure(figsize=(12,6),layout='constrained');grid=fig.add_gridspec(3,2,width_ratios=[40,1],height_ratios=[1,2,1]);axes=[]
        for i in range(3):axes.append(fig.add_subplot(grid[i,0],sharex=axes[0] if axes else None))
        axes[0].step(np.arange(512),s['lines'][:512,0],where='post',color='#315c9b');axes[0].set_ylabel('RX');axes[0].set_yticks([0,1])
        im=axes[1].imshow(g.T,origin='lower',aspect='auto',interpolation='none',vmin=0,vmax=1,cmap='viridis',extent=[0,512,-.5,15.5]);axes[1].set_ylabel('First-layer gate');axes[1].set_yticks([0,4,8,12,15]);fig.colorbar(im,cax=fig.add_subplot(grid[1,1]),label='Update fraction')
        for values,label,color,dy in ((s['labels'][:512],'Required','#008b72',.12),(pred,'Learned','#a66c00',-.12)):
            ticks=np.flatnonzero(values);axes[2].scatter(ticks,values[ticks]+dy,s=12,label=label,color=color)
        axes[2].set_yticks([1,2,3,4,5],['0','1','START','STOP','INVALID']);axes[2].legend(loc='upper right',ncol=2,fontsize=8);axes[2].set_xlabel('Sample tick; no reset between messages');axes[2].set_ylabel('Event')
        fig.suptitle(f'{profile} seed{seed}: learned conditional first-layer updates (0 = hold, 1 = replace)');fig.savefig(root/'figures'/f'gate_trace_{profile}_{seed}_v6.png',dpi=160);plt.close(fig)
    write_json(out/'result.json',rows)
