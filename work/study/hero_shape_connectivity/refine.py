"""Start a separately recorded refinement from each seed's own selected model."""
import argparse
import json
from pathlib import Path
from .run import ROOT,digest
from .shapes import make_shape
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,required=True)
    ap.add_argument('--source',default='phase_transfer');ap.add_argument('--source-epochs',type=int,default=300)
    ap.add_argument('--dest',default='phase_leaks');ap.add_argument('--seeds',default='11,29,47');ap.add_argument('--reset-optimizer',action='store_true');a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01'
    for kwargs in json.loads(a.candidates.read_text()):
        sh=make_shape(**kwargs)
        for profile in ('uart_n','uart_e'):
            for seed in map(int,a.seeds.split(',')):
                src=root/'models'/a.source/sh.name/profile/str(seed)/f'block_{a.source_epochs:04d}.json'
                row=json.loads(src.read_text());dest=root/'models'/a.dest/sh.name/profile/str(seed);dest.mkdir(parents=True,exist_ok=True)
                record=dict(checkpoint=row['checkpoint'],checkpoint_sha256=digest(row['checkpoint']),source_recipe=a.source,
                    source_profile=profile,source_epochs_spent=row['epochs'],source_selected_epoch=row['selected_epoch'],
                    source_exposure_ticks_spent=row['exposure_ticks'],target_profile=profile,source_warm_start=row.get('warm_start'),
                    purpose='same-seed selected-checkpoint refinement; destination recipe and frozen batch source define which parameters are fitted')
                path=dest/'warm_start.json'
                if a.reset_optimizer:record['reset_optimizer']=True
                if path.exists():
                    previous=json.loads(path.read_text())
                    if {k:v for k,v in previous.items() if k!='purpose'}!={k:v for k,v in record.items() if k!='purpose'}:raise ValueError('warm-start source differs')
                else:write_json(path,record)
