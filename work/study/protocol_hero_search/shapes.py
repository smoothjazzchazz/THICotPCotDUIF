"""Physical masks are deterministic and independent of protocol and weight seed."""
from dataclasses import dataclass
import hashlib
import json
import numpy as np

VARIANTS = ('flat', 'ring', 'stack2_current', 'stack2_registered',
            'stack3_current', 'stack3_registered', 'parallel_current',
            'parallel_registered', 'chain')
SEEDS = (11, 29, 47, 71, 101, 131)
PROFILES = ('uart_n', 'uart_e', 'i2c', 'spi0', 'spi1', 'spi2', 'spi3')


@dataclass
class Shape:
    name: str
    n: int
    groups: list
    src: np.ndarray
    dst: np.ndarray
    delay: np.ndarray
    leaks: np.ndarray

    @property
    def parameters(self):
        return len(self.src) + self.n + 6 * self.n + 6

    def config(self):
        d = dict(name=self.name, nodes=self.n, groups=self.groups,
                 edges=[list(map(int,e)) for e in zip(self.src,self.dst,self.delay)],
                 leaks=self.leaks.tolist(), activation='tanh', features=9,
                 readout='all nodes, six affine logits; one decision each tick',
                 parameter_count=self.parameters, topology_seed=20261012,
                 equation='h_i[t]=(1-a_i)*h_i[t-1]+a_i*tanh(b_i+sum(w_ij*z_j))')
        d['shape_sha256'] = hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
        return d


def make_shape(variant, n):
    rng = np.random.default_rng(20261012 + n)
    if variant.startswith('stack3'):
        sizes = {32:[12,10,10],48:[16,16,16],64:[24,20,20]}.get(n, [n//3,n//3,n-2*(n//3)])
        parents = [[],[0],[1]]
    elif variant.startswith('parallel'):
        sizes = {32:[12,12,8],48:[16,16,16],64:[24,24,16]}.get(n,[n*3//8,n*3//8,n-2*(n*3//8)])
        parents = [[],[],[0,1]]
    elif variant.startswith('stack2') or variant == 'chain':
        sizes = [n//2,n-n//2]; parents = [[],[0]]
    else:
        sizes = [n]; parents = [[]]
    starts = np.r_[0,np.cumsum(sizes)]
    edges, leaks = [], np.empty(n)
    groups = [list(range(int(starts[g]),int(starts[g+1]))) for g in range(len(sizes))]
    for g, nodes in enumerate(groups):
        for local, i in enumerate(nodes):
            if variant == 'chain' and g == 0:
                # A genuinely directed delay chain, no wrap or self feedback.
                recurrent = [] if local == 0 else [i-1]
                leaks[i] = 1.
            elif variant == 'ring':
                recurrent = sorted({i,nodes[(local-1)%len(nodes)],nodes[(local-4)%len(nodes)],nodes[(local-9)%len(nodes)]})
                leaks[i] = (1., .5, .125)[i%3]
            else:
                recurrent = [i] + sorted(rng.choice([j for j in nodes if j != i],min(3,len(nodes)-1),replace=False).tolist())
                leaks[i] = ([1.,.125,.5][g] if variant.startswith('parallel') else
                            [1.,.5,.125][g] if len(groups)>1 else (1.,.5,.125)[i%3])
            edges.extend((j,i,1) for j in recurrent)
            for parent in parents[g]:
                # Fixed sparse inter-layer routes. Current routes form a DAG.
                edges.extend((int(j),i,0 if variant.endswith('current') else 1)
                             for j in rng.choice(groups[parent],min(4,len(groups[parent])),replace=False))
            if not parents[g] and not (variant == 'chain' and local != 0):
                edges.extend((-1-f,i,0) for f in range(9))
    edges.sort(key=lambda e:(e[1],e[0],e[2]))
    a = np.array(edges,dtype=np.int32)
    return Shape(f'{variant}_{n}',n,groups,a[:,0].copy(),a[:,1].copy(),a[:,2].copy(),leaks)


def initialize(shape, seed):
    rng = np.random.default_rng(seed)
    p = np.zeros(shape.parameters,dtype=np.float64)
    e = len(shape.src)
    for k,(s,d,delay) in enumerate(zip(shape.src,shape.dst,shape.delay)):
        p[k] = rng.normal(0,.25 if s<0 else .15)
        if s == d: p[k] = .85 + rng.normal(0,.03)
        if shape.name.startswith('chain') and d in shape.groups[0] and s>=0: p[k] = .95
    p[e:e+shape.n] = rng.normal(0,.02,shape.n)
    p[e+shape.n:e+7*shape.n] = rng.normal(0,.1,6*shape.n)
    p[-6] = 1.
    return p


def features(lines, previous=None, ages=None):
    previous = np.ones(3) if previous is None else np.array(previous,copy=True)
    ages = np.full(3,256.) if ages is None else np.array(ages,copy=True)
    if not len(lines):return np.empty((0,9)),previous,ages
    levels=np.asarray(lines,dtype=np.float64)
    edge=np.diff(np.vstack((previous,levels)),axis=0)
    ticks=np.arange(len(lines))[:,None]
    # Exactly the scalar per-lane capped timer, vectorized for offline throughput.
    last_change=np.maximum.accumulate(np.where(edge!=0,ticks,-ages-1),axis=0)
    age_rows=np.minimum(256,ticks-last_change)
    return np.column_stack((levels*2-1,edge,age_rows/256)),levels[-1].copy(),age_rows[-1].copy()
