"""Same-seed, same-graph selection from a declared two-recipe training budget."""
import argparse
import json
from pathlib import Path
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .train import write_json,key


def prepare(root,candidates,seeds):
    for kwargs in candidates:
        sh=make_shape(**kwargs)
        for seed in seeds:
            options=[]
            for recipe in ('phase_circulation','phase_ring_fixed'):
                path=root/'models'/recipe/sh.name/'uart_e'/str(seed)/'block_0600.json'
                options.append(json.loads(path.read_text()))
            best=max(options,key=lambda r:key(r['selected']))
            for profile in ('uart_n','uart_e'):
                folder=root/'models'/'phase_portfolio'/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
                record=dict(checkpoint=best['checkpoint'],checkpoint_sha256=digest(best['checkpoint']),source_recipe=best['recipe'],
                    source_profile='uart_e',source_selected_epoch=best['selected_epoch'],source_epochs_spent=1200,
                    source_exposure_ticks_spent=sum(r['exposure_ticks'] for r in options),target_profile=profile,
                    selection='same key as ordinary training; both recipes run for every seed before selection',
                    retain_frozen_ring=best['recipe']=='phase_ring_fixed',
                    candidates=[dict(recipe=r['recipe'],checkpoint=r['checkpoint'],checkpoint_sha256=digest(r['checkpoint']),selected=r['selected']) for r in options])
                path=folder/'warm_start.json'
                if path.exists():
                    if json.loads(path.read_text())!=record:raise ValueError('portfolio source differs')
                else:write_json(path,record)
                print(sh.name,profile,seed,best['recipe'],best['selected']['message_accuracy'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,default=ROOT/'wider_both_candidate.json');ap.add_argument('--seeds',default=','.join(map(str,SEEDS)));a=ap.parse_args()
    prepare(ROOT/'runs'/'connectivity01',json.loads(a.candidates.read_text()),list(map(int,a.seeds.split(','))))
