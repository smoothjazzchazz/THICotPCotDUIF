"""Declared lower-rate continuation for protected dual rings or inlet teaching."""
import argparse,json
from pathlib import Path
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['dual','inlet'],required=True)
    ap.add_argument('--candidates',type=Path,required=True);ap.add_argument('--profiles',default='uart_n,uart_e')
    ap.add_argument('--seeds',default='11,29,47');ap.add_argument('--workers',type=int,default=3);ap.add_argument('--label',required=True);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';jobs=[]
    source_recipe='phase_dual_ring_v4' if a.source=='dual' else 'phase_inlet_v4';recipe=f'phase_{a.source}_refine_v4'
    for kw in json.loads(a.candidates.read_text()):
        sh=make_shape(**kw)
        for profile in a.profiles.split(','):
            for seed in map(int,a.seeds.split(',')):
                path=root/'models'/source_recipe/sh.name/profile/str(seed)/'block_0120.json';b=json.loads(path.read_text())
                folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
                record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(path),source_profile=profile,target_profile=profile,
                    reset_optimizer=True,data_epoch_offset=180,source_epochs=120,source_exposure_ticks=b['exposure_ticks'],
                    policy='same-seed best source; lower-rate0.0001, aux off, original ring masks preserved; same native-refinement data rule')
                warm=folder/'warm_start.json'
                if warm.exists():assert json.loads(warm.read_text())==record,'source changed'
                else:write_json(warm,record)
                s=b['selected'];passed=s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
                jobs.append((str(root),kw,profile,seed,0 if passed else 60,recipe))
    batch_jobs(root,jobs,a.workers,a.label)
