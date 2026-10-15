"""Only unresolved configurations receive the new readout-fitting block."""
import argparse
import json
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape,SEEDS
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',default=str(ROOT/'wider_both2_candidate.json'));ap.add_argument('--profiles',default='uart_n,uart_e');ap.add_argument('--label',default='precision_readout_v2_60');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    from pathlib import Path
    root=ROOT/'runs'/'connectivity01';jobs=[]
    for kwargs in json.loads(Path(a.candidates).read_text()):
        sh=make_shape(**kwargs)
        for profile in a.profiles.split(','):
            for seed in SEEDS:
                block=root/'models'/'phase_precision_v2'/sh.name/profile/str(seed)/'block_0060.json';b=json.loads(block.read_text());s=b['selected']
                folder=root/'models'/'phase_precision_readout_v2'/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
                record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(block),
                    source_profile=profile,target_profile=profile,source_provenance=b.get('warm_start'),reset_optimizer=True,data_epoch_offset=60,
                    policy='freeze all recurrent state parameters; train only six affine readouts on corrected banks 61-120 if full development gates remain unresolved')
                path=folder/'warm_start.json'
                if path.exists():
                    if json.loads(path.read_text())!=record:raise ValueError('source differs')
                else:write_json(path,record)
                passed=s['message_accuracy']==1 and s['boundary_errors']==0 and s['invalid_accepted']==0 and s['background_accepted']==0
                jobs.append((str(root),kwargs,profile,seed,0 if passed else 60,'phase_precision_readout_v2'))
    batch_jobs(root,jobs,a.workers,a.label)
