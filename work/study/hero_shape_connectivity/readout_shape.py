"""Sixteen current-sample nonlinear readout nodes after a 48-state reservoir."""
import numpy as np
from .vendor.shapes import Shape


class ReadoutShape(Shape):
    nonlinear_readout=True
    head='flat'

    def config(self):
        d=super().config()
        d.update(stored_states=48,nonlinear_readout_nodes=16,
            readout='six affine logits from 48 recurrent states and 16 current-sample tanh readout nodes',
            equation='first 48 nodes follow serialized leaky recurrence; last 16 are tanh of current first-48 values, with no recurrence or feedback',
            activation_depth=2,implementation='runtime carries a 64-value buffer; last16 previous values have exactly zero effect')
        return d


def augment(base,layout):
    if base.n!=48 or layout not in ('dense','fanin8','fanin32','fanin32_fast'):raise ValueError('declared 48+16 readout graphs only')
    edges=[tuple(map(int,e)) for e in zip(base.src,base.dst,base.delay)]
    for j,d in enumerate(range(48,64)):
        if layout=='dense':parents=range(48)
        elif layout=='fanin32':
            parents=base.groups[0]+[base.groups[g][(j+2*k)%16] for g in (1,2) for k in range(8)]
        elif layout=='fanin32_fast':
            parents=base.groups[1]+[base.groups[g][(j+2*k)%16] for g in (0,2) for k in range(8)]
        else:parents=([base.groups[0][(j+k*8)%16] for k in range(2)]+
            [base.groups[1][(j+k*4)%16] for k in range(4)]+[base.groups[2][(j+k*8)%16] for k in range(2)])
        edges.extend((s,d,0) for s in parents)
    edges.sort(key=lambda e:(e[1],e[0],e[2]));a=np.array(edges,dtype=np.int32)
    return ReadoutShape(base.name+'_readout16_'+layout,64,base.groups+[list(range(48,64))],
        a[:,0].copy(),a[:,1].copy(),a[:,2].copy(),np.r_[base.leaks,np.ones(16)])


def initialize(shape,seed):
    from .shapes import initialize as plain_initialize
    mask=shape.dst<48;e=int(mask.sum());E=len(shape.src)
    base=Shape('backbone',48,shape.groups[:3],shape.src[mask],shape.dst[mask],shape.delay[mask],shape.leaks[:48])
    old=plain_initialize(base,seed);p=np.zeros(shape.parameters)
    p[:e]=old[:e];p[E:E+48]=old[e:e+48]
    p[E+64:E+64+384].reshape(6,64)[:,:48]=old[e+48:e+48+288].reshape(6,48)
    p[-6:]=old[-6:]
    for k in range(e,E):
        p[k]=np.random.default_rng(np.random.SeedSequence([seed,int(shape.src[k])+16,int(shape.dst[k]),14013])).normal(0,.15)
    # New output columns start at zero: exactly the paired backbone's function.
    return p
