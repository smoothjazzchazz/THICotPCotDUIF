"""Paired counted routing comparison from identical trained behavior."""
import argparse
import json
import numpy as np
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape
from .train import write_json
from .runtime import run
from .data import load


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default='phase_precision');ap.add_argument('--seeds',default='11,29,47');ap.add_argument('--label');a=ap.parse_args()
    if a.recipe not in ('phase_precision','phase_precision_v2'):raise ValueError(a.recipe)
    root=ROOT/'runs'/'connectivity01';candidates=json.loads((ROOT/'distributed_candidates.json').read_text())
    base=make_shape(**json.loads((ROOT/'wider_both2_candidate.json').read_text())[0]);oldedges=list(zip(base.src,base.dst,base.delay));jobs=[]
    for profile in ('uart_n','uart_e'):
        x=load(root/'data'/profile/'dev')['x'][:8192]
        for seed in map(int,a.seeds.split(',')):
            folder=root/'models'/'phase_recovery_readout'/base.name/profile/str(seed);block=sorted(folder.glob('block_*.json'))[-1]
            b=json.loads(block.read_text());source=dict(np.load(b['checkpoint']));oldmeta=json.loads(str(source['metadata']))
            for kwargs in candidates:
                sh=make_shape(**kwargs);folder=root/'models'/a.recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
                if not (folder/'warm_start.json').exists():
                    edges=list(zip(sh.src,sh.dst,sh.delay));index={e:i for i,e in enumerate(edges)};new=dict(source)
                    for key in ('p','m','v'):
                        q=np.zeros(sh.parameters)
                        for i,e in enumerate(oldedges):q[index[e]]=source[key][i]
                        q[len(edges):]=source[key][len(oldedges):];new[key]=q
                    meta=dict(oldmeta);meta['frozen_parameter_indices']=[index[oldedges[i]] if i<len(oldedges) else i+len(edges)-len(oldedges) for i in oldmeta['frozen_parameter_indices']]
                    new['metadata']=np.array(json.dumps(meta));sh.leaks=source['leaks'].copy();base.leaks=source['leaks'].copy()
                    if not np.array_equal(run(base,source['p'],x)[2],run(sh,new['p'],x)[2]):raise AssertionError('zero-added routes changed initial function')
                    checkpoint=folder/'warm_init.npz';np.savez_compressed(checkpoint,**new)
                    write_json(folder/'warm_start.json',dict(checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),
                        source_checkpoint=b['checkpoint'],source_checkpoint_sha256=digest(b['checkpoint']),source_block=str(block),
                        source_provenance=b.get('warm_start'),additional_connections=len(edges)-len(oldedges),initial_forward_equal=True,reset_optimizer=True,
                        rule='same source seed and state, same precision data/exposure/mask; twelve added routes start at zero'))
                jobs.append((str(root),kwargs,profile,seed,60,a.recipe))
    batch_jobs(root,jobs,4,a.label or ('distributed_precision60' if a.recipe=='phase_precision' else 'distributed_precision_v2_60'))
