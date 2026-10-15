"""Post-fit interventions are diagnostic configurations, never substitute winners."""
import argparse
from pathlib import Path
import numpy as np
from .shapes import historical_shape,make_shape
from .vendor.network import run,pulses
from .data import load,metrics
from .train import write_json


def interventions(shape,p):
    groups={i:g for g,nodes in enumerate(shape.groups) for i in nodes}
    output={'full':p.copy()}
    for layer in (None,0,1,2):
        q=p.copy()
        for k,(s,d) in enumerate(zip(shape.src,shape.dst)):
            if s>=0 and groups[int(s)]==groups[int(d)] and (layer is None or groups[int(d)]==layer):q[k]=0
        output['no_recurrence_'+str(layer)]=q
    for layer in (0,1,2):
        q=p.copy();w=q[len(shape.src)+shape.n:-6].reshape(6,shape.n)
        w[:,shape.groups[layer]]=0;output[f'no_readout_layer{layer}']=q
    return output


def analyze(root):
    folder=root/'diagnostics';folder.mkdir(exist_ok=True)
    old=root.parents[2]/'protocol_hero_search'/'runs'/'run01'
    sh=historical_shape('stack3_registered',64);results=[]
    for profile in ('uart_n','uart_e','spi1','spi3','i2c'):
        data=load(root/'data'/profile/'dev')
        p=np.load(old/'models'/sh.name/profile/'trained_11'/'selected.npz',allow_pickle=False)['p']
        for name,q in interventions(sh,p).items():
            kinds=run(sh,q,data['x'])[2].argmax(1);row=metrics(data,kinds)
            row.update(source='historical selected seed11; diagnostic development replay',profile=profile,intervention=name)
            results.append(row)
            if name in ('full','no_recurrence_None'):
                np.savez_compressed(folder/f'historical_{profile}_{name}.npz',predicted=kinds)
        # Save the first 4096 ticks of state, logits and layer output contributions.
        x=data['x'][:4096];h=np.zeros(sh.n);states=[];logits=[]
        for tick in x:
            _,h,z,_,_=run(sh,p,tick[None,:],h=h);states.append(h.copy());logits.append(z[0])
        states=np.array(states);w=p[len(sh.src)+sh.n:-6].reshape(6,sh.n)
        contributions=np.stack([states[:,g]@w[:,g].T for g in sh.groups],axis=1)
        np.savez_compressed(folder/f'historical_{profile}_causal_states.npz',x=x,labels=data['labels'][:4096],
                            states=states,logits=np.array(logits),layer_contributions=contributions)
    write_json(folder/'historical_interventions.json',results)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path(__file__).parent/'runs'/'connectivity01')
    analyze(ap.parse_args().output)
