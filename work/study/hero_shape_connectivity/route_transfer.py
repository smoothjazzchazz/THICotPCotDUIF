"""Paired graph intervention with initially zero new physical connections."""
import argparse
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .train import write_json
from .runtime import run
from .data import load


def prepare(root,seeds):
    candidates=json.loads((ROOT/'phase_route_candidates.json').read_text())
    source_shape=make_shape(**candidates[0]);oldedges=list(zip(source_shape.src,source_shape.dst,source_shape.delay))
    for seed in seeds:
        source=root/'models'/'phase_circulation'/source_shape.name/'uart_e'/str(seed)/'block_0600.json'
        record=json.loads(source.read_text());a=dict(np.load(record['checkpoint']))
        for kwargs in candidates:
            sh=make_shape(**kwargs);folder=root/'models'/'phase_route'/sh.name/'uart_e'/str(seed)
            folder.mkdir(parents=True,exist_ok=True)
            if (folder/'warm_start.json').exists():continue
            newedges=list(zip(sh.src,sh.dst,sh.delay));mapping={edge:i for i,edge in enumerate(newedges)}
            converted=dict(a)
            for key in ('p','m','v'):
                value=np.zeros(sh.parameters)
                for i,edge in enumerate(oldedges):value[mapping[edge]]=a[key][i]
                value[len(newedges):]=a[key][len(oldedges):];converted[key]=value
            x=load(root/'data'/'uart_e'/'dev')['x'][:2048]
            before=run(source_shape,a['p'],x)[2];after=run(sh,converted['p'],x)[2]
            if not np.array_equal(before,after):raise AssertionError('zero new routes changed initial prediction')
            init=folder/'warm_init.npz';np.savez_compressed(init,**converted)
            write_json(folder/'warm_start.json',dict(checkpoint=str(init),checkpoint_sha256=digest(init),
                source_checkpoint=record['checkpoint'],source_checkpoint_sha256=digest(record['checkpoint']),
                source_profile='uart_e',source_recipe='phase_circulation',source_selected_epoch=record['selected_epoch'],
                source_epochs_spent=600,source_exposure_ticks_spent=record['exposure_ticks'],
                target_profile='uart_e',new_edges=len(newedges)-len(oldedges),new_edge_initialization=0,
                initial_forward_bitwise_equal=True,purpose='paired fixed-graph routing comparison with common learned starting function'))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',default='11,29,47');a=ap.parse_args()
    prepare(ROOT/'runs'/'connectivity01',list(map(int,a.seeds.split(','))))
