"""Choose native-profile or transfer training by one explicit development rule."""
import argparse
import json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .data import load,metrics
from .train import evaluate_stream,write_json,key


def prepare(root,candidates):
    for kwargs in candidates:
        sh=make_shape(**kwargs)
        for profile in ('uart_n','uart_e'):
            dev=load(root/'data_extended'/profile/'dev')
            for seed in SEEDS:
                folder=root/'models'/'phase_profile_fresh'/sh.name/profile/str(seed)
                folder.mkdir(parents=True,exist_ok=True)
                if (folder/'warm_start.json').exists():continue
                options=[]
                for recipe,epochs in [('phase_portfolio',300),('phase_ring_fixed',600)]:
                    block=root/'models'/recipe/sh.name/profile/str(seed)/f'block_{epochs:04d}.json'
                    b=json.loads(block.read_text());model=np.load(b['checkpoint']);sh.leaks=model['leaks'].copy()
                    loss,z=evaluate_stream(sh,model['p'],dev,np.ones(6));score=metrics(dev,z.argmax(1));score['dev_loss']=loss
                    options.append(dict(recipe=recipe,checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
                        selected_epoch=b['selected_epoch'],epochs_spent=epochs,exposure_ticks=b['exposure_ticks'],extended_development=score,
                        prior_warm_start=b.get('warm_start')))
                best=max(options,key=lambda x:key(x['extended_development']))
                write_json(folder/'warm_start.json',dict(checkpoint=best['checkpoint'],checkpoint_sha256=best['checkpoint_sha256'],
                    source_recipe=best['recipe'],source_profile=profile,target_profile=profile,candidates=options,
                    source_epochs_spent='refer to candidates and shared source provenance; do not double-count pretraining',
                    selection='same extended-development key for every seed and both graphs; no confirmation samples used'))
                print(sh.name,profile,seed,best['recipe'],best['extended_development']['message_accuracy'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,default=ROOT/'phase_route_candidates.json');a=ap.parse_args()
    prepare(ROOT/'runs'/'connectivity01',json.loads(a.candidates.read_text()))
