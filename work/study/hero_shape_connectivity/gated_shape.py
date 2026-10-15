"""Two nonlinear computational nodes per scalar stored state; gates are counted."""
import numpy as np
from .vendor.shapes import Shape


class GatedShape(Shape):
    gated=True
    head='flat'

    @property
    def parameters(self):return 2*len(self.src)+8*self.n+6

    def config(self):
        d=super().config();d.update(nodes=2*self.n,stored_states=self.n,
            physical_groups=[[f'{kind}{i}' for i in group for kind in ('proposal','gate')] for group in self.groups],
            computational_edges=[dict(src=int(s),dst=f'{kind}{int(t)}',delay=int(delay))
                for s,t,delay in zip(self.src,self.dst,self.delay) for kind in ('proposal','gate')],
            activation='tanh proposal and sigmoid update gate, both counted as nodes',
            equation='u=tanh(b_u+W_u*z); g=sigmoid(b_g+W_g*z); h[t]=(1-g)*h[t-1]+g*u',
            leaks='values initialize gate bias only; update rate is learned from inputs and prior state')
        return d


def initialize(shape,seed,plain_parameters):
    e=len(shape.src);n=shape.n;p=np.zeros(shape.parameters)
    p[:e]=plain_parameters[:e]
    rng=np.random.default_rng(seed+917000);p[e:2*e]=rng.normal(0,.025,e)
    p[2*e:2*e+n]=plain_parameters[e:e+n]
    a=np.clip(shape.leaks,.01,.99);p[2*e+n:2*e+2*n]=np.log(a/(1-a))
    p[2*e+2*n:]=plain_parameters[e+n:]
    return p
