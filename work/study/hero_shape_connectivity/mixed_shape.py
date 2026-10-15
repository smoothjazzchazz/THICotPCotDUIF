"""Ungated fast ring and sixteen conditional slow-memory cells: 64 nonlinear units."""
import numpy as np
from .vendor.shapes import Shape


class MixedShape(Shape):
    mixed=True
    head='flat'

    def __post_init__(self):
        pass

    @property
    def gate_nodes(self):return np.array(self.groups[2],dtype=np.int32)

    @property
    def gate_src(self):
        first=self.groups[0]
        return np.array([s for d in self.groups[2] for s in [first[k*len(first)//4] for k in range(4)]+[self.groups[1][0],d]],dtype=np.int32)

    @property
    def gate_dst(self):return np.repeat(self.gate_nodes,6).astype(np.int32)

    @property
    def parameters(self):return len(self.src)+7*self.n+6+len(self.gate_src)+len(self.gate_nodes)

    def config(self):
        d=super().config();d.update(nodes=self.n+len(self.gate_nodes),stored_states=self.n,
            gate_nodes=self.gate_nodes.tolist(),gate_edges=[dict(src=int(s),dst=int(t),delay=1) for s,t in zip(self.gate_src,self.gate_dst)],
            equation='proposal=tanh(b+W*z); last-layer g=sigmoid(bg+Wg*h[t-1]); other g=fixed leak; h[t]=(1-g)*h[t-1]+g*proposal',
            parameter_layout='proposal edges, proposal biases, gate edges, gate biases, all-state readout, output biases',
            activation=f'{self.n} tanh proposals plus {len(self.gate_nodes)} sigmoid gates; all {self.n+len(self.gate_nodes)} nonlinear units counted',
            gate_routing='four first-layer quarters, first fast-ring state, own slow state; all registered')
        return d


class MixedFirstShape(MixedShape):
    @property
    def gate_nodes(self):return np.array(self.groups[0],dtype=np.int32)

    @property
    def gate_src(self):
        fast=self.groups[1]
        return np.array([s for d in self.gate_nodes for s in [fast[k*len(fast)//4] for k in range(4)]+[self.groups[2][0],d]],dtype=np.int32)

    def config(self):
        d=super().config();d.update(
            equation='proposal=tanh(b+W*z); first-layer g=sigmoid(bg+Wg*h[t-1]); other g=fixed leak; h[t]=(1-g)*h[t-1]+g*proposal',
            gate_routing='four fast-ring quarters, first slow-ring state, own first-layer state; all registered')
        return d


class MixedFirstEightShape(MixedFirstShape):
    @property
    def gate_nodes(self):return np.array(self.groups[0][::3],dtype=np.int32)

    def config(self):
        d=super().config();d['equation']='proposal=tanh(b+W*z); nodes0,3,6,9,12,15,18,21 use g=sigmoid(bg+Wg*h[t-1]); other g=fixed leak; h[t]=(1-g)*h[t-1]+g*proposal'
        return d


def initialize(shape,seed,plain):
    e=len(shape.src);n=shape.n;ge=len(shape.gate_src);gn=len(shape.gate_nodes)
    p=np.zeros(shape.parameters);p[:e+n]=plain[:e+n]
    a=shape.leaks[shape.gate_nodes];p[e+n+ge:e+n+ge+gn]=np.log(a/(1-a))
    p[e+n+ge+gn:]=plain[e+n:]
    return p


def cost(shape):
    from .shapes import cost as plain_cost
    base=Shape(shape.name,shape.n,shape.groups,shape.src,shape.dst,shape.delay,shape.leaks)
    d=plain_cost(base);ge=len(shape.gate_src);gn=len(shape.gate_nodes)
    groups={i:g for g,nodes in enumerate(shape.groups) for i in nodes}
    rec=sum(groups[int(s)]==groups[int(t)] for s,t in zip(shape.gate_src,shape.gate_dst))
    d.update(nodes=shape.n+gn,gate_edges=ge,gate_biases=gn,parameters=shape.parameters,
        recurrent_edges=d['recurrent_edges']+rec,inter_layer_edges=d['inter_layer_edges']+ge-rec,
        macs_per_tick=d['macs_per_tick']+ge,modeled_multiplies_per_tick=d['modeled_multiplies_per_tick']+ge,
        sigmoid_per_tick=gn,q12_parameters_bytes=2*shape.parameters,
        leak_configuration_bytes=2*(shape.n-gn),
        known_numeric_storage_bytes=2*shape.parameters+4*shape.n+2*(shape.n-gn)+8194,
        sigmoid_implementation='(1+tanh(z/2))/2; shared LUT, two fixed divisions and one addition per gate',
        activation_depth=1)
    return d
