"""Refine recovery dynamics without changing the fixed physical topology."""
import argparse
import json
from pathlib import Path
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape,SEEDS
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default='phase_precision');ap.add_argument('--candidates',type=Path,default=ROOT/'wider_both2_candidate.json');ap.add_argument('--workers',type=int,default=6);ap.add_argument('--label');a=ap.parse_args()
    if a.recipe not in ('phase_precision','phase_precision_v2'):raise ValueError(a.recipe)
    root=ROOT/'runs'/'connectivity01';candidates=json.loads(a.candidates.read_text());jobs=[]
    for kwargs in candidates:
        sh=make_shape(**kwargs)
        for profile in ('uart_n','uart_e'):
            for seed in SEEDS:
                source=root/'models'/'phase_recovery_readout'/sh.name/profile/str(seed)
                block=sorted(source.glob('block_*.json'))[-1];b=json.loads(block.read_text())
                folder=root/'models'/a.recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
                path=folder/'warm_start.json'
                record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(block),
                    source_profile=profile,target_profile=profile,reset_optimizer=True,source_provenance=b.get('warm_start'),
                    mask_policy='freeze learned middle-ring edges and undriven middle biases; train other existing parameters')
                if path.exists():
                    if json.loads(path.read_text())!=record:raise ValueError('source changed')
                else:write_json(path,record)
                jobs.append((str(root),kwargs,profile,seed,60,a.recipe))
    batch_jobs(root,jobs,a.workers,a.label or ('precision60' if a.recipe=='phase_precision' else 'precision_v2_60'))
