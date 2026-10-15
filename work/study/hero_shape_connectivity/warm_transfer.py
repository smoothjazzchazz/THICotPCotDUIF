"""Explicit off-chip same-shape pretraining; source checkpoints remain immutable."""
import argparse
import json
from pathlib import Path
from .run import ROOT,digest
from .shapes import make_shape
from .train import write_json


def prepare(root,candidates,seeds):
    for kwargs in candidates:
        sh=make_shape(**kwargs)
        for seed in seeds:
            source=root/'models'/'phase_circulation'/sh.name/'uart_e'/str(seed)/'block_0600.json'
            b=json.loads(source.read_text());checkpoint=b['checkpoint']
            for profile in ('uart_n','uart_e'):
                dest=root/'models'/'phase_transfer'/sh.name/profile/str(seed);dest.mkdir(parents=True,exist_ok=True)
                target=dest/'warm_start.json'
                record=dict(checkpoint=checkpoint,checkpoint_sha256=digest(checkpoint),source_profile='uart_e',
                    source_recipe='phase_circulation',source_epochs_spent=b['epochs'],source_selected_epoch=b['selected_epoch'],
                    source_exposure_ticks_spent=b['exposure_ticks'],target_profile=profile,
                    purpose='selected-checkpoint lower-rate refinement; UART 8N1 also tests transfer of learned phase from 8E1',
                    state_policy='same physical shape; no additional inference state; new independent stream at each training epoch')
                if target.exists():
                    if json.loads(target.read_text())!=record:raise ValueError('different warm source already recorded')
                else:write_json(target,record)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',default='11,29,47');ap.add_argument('--candidates',type=Path,default=ROOT/'feedback_candidates.json');a=ap.parse_args()
    prepare(ROOT/'runs'/'connectivity01',json.loads(a.candidates.read_text()),list(map(int,a.seeds.split(','))))
