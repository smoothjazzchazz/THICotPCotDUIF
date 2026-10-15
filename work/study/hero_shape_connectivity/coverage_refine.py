"""Developed-checkpoint selection followed by full startup-coverage calibration."""
import argparse
import json
from pathlib import Path
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape,SEEDS
from .train import write_json,key

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,default=ROOT/'wider_both2_candidate.json');ap.add_argument('--profiles',default='uart_n,uart_e');ap.add_argument('--label',default='coverage_v3_60');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';jobs=[]
    for kwargs in json.loads(a.candidates.read_text()):
        sh=make_shape(**kwargs)
        for profile in a.profiles.split(','):
            for seed in SEEDS:
                folder=root/'models'/'phase_coverage_v3'/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);path=folder/'warm_start.json'
                if path.exists():record=json.loads(path.read_text());b=json.loads(Path(record['selected_source_block']).read_text())
                else:
                    options=[]
                    for recipe in ('phase_precision_v2','phase_precision_readout_v2','phase_native_v3'):
                        files=sorted((root/'models'/recipe/sh.name/profile/str(seed)).glob('block_*.json'))
                        if files:
                            row=json.loads(files[-1].read_text());options.append((files[-1],row))
                    if not options:raise ValueError('no completed verified source')
                    source,b=max(options,key=lambda item:key(item[1]['selected']))
                    record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),selected_source_block=str(source),
                        source_profile=profile,target_profile=profile,reset_optimizer=True,data_epoch_offset=120,
                        candidates=[dict(block=str(p),checkpoint=r['checkpoint'],checkpoint_sha256=digest(r['checkpoint']),recipe=r['recipe'],epochs=r['epochs'],exposure_ticks=r['exposure_ticks'],selected=r['selected']) for p,r in options],
                        source_provenance=b.get('warm_start'),policy='same verified-development selection rule for every seed; retain already passing sources, calibrate unresolved ones with both startup modes')
                    write_json(path,record)
                s=b['selected'];passed=s['message_accuracy']==1 and s['boundary_errors']==0 and s['invalid_accepted']==0 and s['background_accepted']==0
                jobs.append((str(root),kwargs,profile,seed,0 if passed else 60,'phase_coverage_v3'))
    batch_jobs(root,jobs,a.workers,a.label)
