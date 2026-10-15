"""Continue each matched native-v3 best checkpoint at a lower rate, without transfer."""
import argparse,json
from pathlib import Path
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape,SEEDS
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,required=True);ap.add_argument('--profiles',default='uart_n,uart_e');ap.add_argument('--seeds',default=','.join(map(str,SEEDS)));ap.add_argument('--workers',type=int,default=4);ap.add_argument('--label',required=True);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';jobs=[]
    for kw in json.loads(a.candidates.read_text()):
        sh=make_shape(**kw)
        for profile in a.profiles.split(','):
            for seed in map(int,a.seeds.split(',')):
                source=root/'models'/'phase_native_v3'/sh.name/profile/str(seed)/'block_0120.json';b=json.loads(source.read_text())
                folder=root/'models'/'phase_native_refine_v3'/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
                record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(source),source_profile=profile,target_profile=profile,
                    reset_optimizer=True,data_epoch_offset=180,source_epochs=120,source_exposure_ticks=b['exposure_ticks'],
                    policy='same-seed, same-profile native-v3 best development checkpoint; retain passing configurations; no cross-profile or cross-seed transfer')
                path=folder/'warm_start.json'
                if path.exists():
                    if json.loads(path.read_text())!=record:raise ValueError('existing refinement source differs')
                else:write_json(path,record)
                s=b['selected'];passed=s['message_accuracy']==1 and s['boundary_errors']==0 and s['invalid_accepted']==0 and s['background_accepted']==0
                jobs.append((str(root),kw,profile,seed,0 if passed else 60,'phase_native_refine_v3'))
    batch_jobs(root,jobs,a.workers,a.label)
