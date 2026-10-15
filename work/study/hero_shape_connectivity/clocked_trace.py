"""Record pulse changes around short-clock I2C failures before more training."""
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load
from .train import evaluate_stream,write_json
from .runtime import pulses

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';rows=[]
    for name in ('mixed_candidates.json','reduced56_candidate.json'):
        for kw in json.loads((ROOT/name).read_text()):
            sh=make_shape(**kw);folder=root/'models'/'matched'/sh.name/'i2c'/'47';b=json.loads((folder/'block_0030.json').read_text());a=np.load(b['checkpoint']);p=a['p'];sh.leaks=a['leaks'].copy()
            s=load(root/'data'/'i2c'/'dev');_,z=evaluate_stream(sh,p,s,np.ones(6));pred=pulses(z.argmax(1));y=s['labels'];windows=[]
            for tick in np.flatnonzero(pred!=y):
                g=next((g for g in s['groups'] if g['start']<=tick<g['end']),None)
                if not g or g['condition']!='duty':continue
                lo=max(0,int(tick)-8);hi=min(len(y),int(tick)+9)
                windows.append(dict(tick=int(tick),target=int(y[tick]),actual=int(pred[tick]),lines=s['lines'][lo:hi].tolist(),truth=y[lo:hi].tolist(),predicted=pred[lo:hi].tolist(),logits=z[lo:hi].tolist(),window_start=lo,group=g))
            rows.append(dict(shape=sh.name,source_checkpoint=b['checkpoint'],source_sha256=digest(b['checkpoint']),windows=windows))
            print(sh.name,[(r['tick'],r['target'],r['actual'],r['lines'][8]) for r in windows[:8]],flush=True)
    write_json(root/'diagnostics'/'reduced_i2c_duty_traces.json',rows)
