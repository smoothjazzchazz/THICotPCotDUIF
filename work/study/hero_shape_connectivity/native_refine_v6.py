"""Start declared lower-rate continuations only after each native source completes."""
import argparse,json
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape
from .train import write_json


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    root=ROOT/'runs/connectivity01';manifest=root/f'{a.label}_jobs.json'
    if manifest.exists():raise ValueError('use resume_batch with the existing immutable wave, or choose a new label for newly completed sources')
    jobs=[];pending=[]
    for kw in json.loads((ROOT/'gate_eight_candidates.json').read_text()):
        sh=make_shape(**kw)
        for profile in ('uart_n','uart_e'):
            for seed in (11,29,47):
                source=root/'models/phase_native_v6'/sh.name/profile/str(seed)/'block_0120.json'
                folder=root/'models/phase_native_refine_v6'/sh.name/profile/str(seed);warm=folder/'warm_start.json'
                if not source.exists() or warm.exists():
                    pending.append(dict(shape=sh.name,profile=profile,seed=seed,reason='already prepared; inspect its original wave' if warm.exists() else 'native120 incomplete'));continue
                b=json.loads(source.read_text());s=b['selected'];passed=s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
                folder.mkdir(parents=True,exist_ok=True);record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(source),source_block_sha256=digest(source),
                    source_profile=profile,target_profile=profile,reset_optimizer=True,data_epoch_offset=110,source_epochs=120,source_exposure_ticks=b['exposure_ticks'],
                    policy='same-seed/profile completed native-v6 best; matched conditional rule, retain whole enlarged-development passes, otherwise60 epochs at0.0001 without auxiliary loss')
                write_json(warm,record);jobs.append((str(root),kw,profile,seed,0 if passed else 60,'phase_native_refine_v6'))
    if not jobs:raise ValueError('no newly completed native sources; no batch created')
    write_json(root/f'{a.label}_pending.json',pending);batch_jobs(root,jobs,a.workers,a.label)
