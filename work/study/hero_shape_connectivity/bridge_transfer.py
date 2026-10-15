"""Add counted routes with a paired identical-function warm start."""
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .train import write_json
from .runtime import run
from .data import load


def prepare(root):
    candidates=json.loads((ROOT/'bridge_candidates.json').read_text());base=make_shape(**candidates[0])
    oldedges=list(zip(base.src,base.dst,base.delay));x=load(root/'data'/'uart_e'/'dev')['x'][:8192]
    for seed in (11,29,47):
        block=root/'models'/'phase_profile_fresh'/base.name/'uart_e'/str(seed)/'block_0060.json'
        b=json.loads(block.read_text());source=dict(np.load(b['checkpoint']));oldmeta=json.loads(str(source['metadata']))
        for kwargs in candidates:
            sh=make_shape(**kwargs);folder=root/'models'/'phase_bridge'/sh.name/'uart_e'/str(seed);folder.mkdir(parents=True,exist_ok=True)
            if (folder/'warm_start.json').exists():continue
            edges=list(zip(sh.src,sh.dst,sh.delay));index={e:i for i,e in enumerate(edges)};new=dict(source)
            for key in ('p','m','v'):
                q=np.zeros(sh.parameters)
                for i,e in enumerate(oldedges):q[index[e]]=source[key][i]
                q[len(edges):]=source[key][len(oldedges):];new[key]=q
            meta=dict(oldmeta);meta['frozen_parameter_indices']=[index[oldedges[i]] if i<len(oldedges) else i+len(edges)-len(oldedges) for i in oldmeta['frozen_parameter_indices']]
            new['metadata']=np.array(json.dumps(meta));sh.leaks=source['leaks'].copy();base.leaks=source['leaks'].copy()
            if not np.array_equal(run(base,source['p'],x)[2],run(sh,new['p'],x)[2]):raise AssertionError('new zero routes changed initial function')
            checkpoint=folder/'warm_init.npz';np.savez_compressed(checkpoint,**new)
            write_json(folder/'warm_start.json',dict(checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),
                source_checkpoint=b['checkpoint'],source_checkpoint_sha256=digest(b['checkpoint']),source_block=str(block),
                source_exposure_ticks=b['exposure_ticks'],source_provenance=b.get('warm_start'),data_epoch_offset=60,
                additional_connections=len(edges)-len(oldedges),initial_forward_equal=True,
                rule='same seed, weights, moments, training mask, data and exposure; four new routes start at zero'))

if __name__=='__main__':prepare(ROOT/'runs'/'connectivity01')
