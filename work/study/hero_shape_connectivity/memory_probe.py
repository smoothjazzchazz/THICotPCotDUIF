"""Paired causal state sensitivity, without imposing protocol state on inference."""
from pathlib import Path
import numpy as np
from .shapes import make_shape,initialize,features
from .vendor.network import run
from .train import write_json


def probe(root):
    folder=root/'diagnostics';folder.mkdir(exist_ok=True);rows=[]
    for code in ('sss','srr','shh','skk','spp'):
        sh=make_shape(code)
        for seed in (11,29,47):
            path=root/'models'/'matched'/sh.name/'uart_n'/str(seed)/'selected.npz'
            for stage,p in [('initial',initialize(sh,seed))]+([('trained',np.load(path)['p'])] if path.exists() else []):
                # Same subsequent input, distinct one-tick initial level. This tests retention,
                # not whether a different input history is valid under any protocol.
                a=np.ones((513,3),dtype=np.uint8);b=a.copy();b[0,0]=0
                xa=features(a)[0];xb=features(b)[0]
                # Remove the generic age difference after the pulse to isolate recurrent memory.
                xb[1:]=xa[1:]
                ha=np.zeros(sh.n);hb=np.zeros(sh.n);dist=[]
                for t in range(len(a)):
                    _,ha,_,_,_=run(sh,p,xa[t:t+1],h=ha);_,hb,_,_,_=run(sh,p,xb[t:t+1],h=hb)
                    dist.append([float(np.linalg.norm(ha[g]-hb[g])) for g in sh.groups])
                d=np.array(dist);np.savez_compressed(folder/f'memory_{sh.name}_{seed}_{stage}.npz',distance=d)
                rows.append(dict(shape=sh.name,seed=seed,stage=stage,
                    at_horizons={str(t):d[t].tolist() for t in (0,7,16,32,64,160,176,256,512)},
                    interpretation='state sensitivity under clamped common future features, not a capacity bound or protocol performance'))
    write_json(folder/'memory_probe.json',rows)

if __name__=='__main__':probe(Path(__file__).parent/'runs'/'connectivity01')
