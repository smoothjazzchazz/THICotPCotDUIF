"""Matched no-parity-to-parity transfer for unresolved first-gate/control seeds."""
import argparse,json
from pathlib import Path
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape
from .train import key,write_json


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--label',default='first_gate_n_to_e_v6_60');ap.add_argument('--seeds',default='29,47');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--candidates',type=Path,default=ROOT/'mixed_first_candidates.json');args=ap.parse_args()
    root=ROOT/'runs/connectivity01';label=args.label;jobs=[]
    for kw in json.loads(args.candidates.read_text()):
        sh=make_shape(**kw)
        for seed in map(int,args.seeds.split(',')):
            options=[]
            for recipe in ('phase_native_v3','phase_native_refine_v3'):
                for path in (root/'models'/recipe/sh.name/'uart_n'/str(seed)).glob('block_*.json'):options.append((path,json.loads(path.read_text())))
            source,b=max(options,key=lambda pair:key(pair[1]['selected']));folder=root/'models/phase_n_to_e_v6'/sh.name/'uart_e'/str(seed);folder.mkdir(parents=True,exist_ok=True)
            record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(source),source_block_sha256=digest(source),
                source_profile='uart_n',target_profile='uart_e',source_seed=seed,target_seed=seed,source_exposure_ticks=b['exposure_ticks'],
                reset_optimizer=True,data_epoch_offset=428,policy='paired same-seed native/refine N best checkpoint; separate E weights; both unresolved target seeds get identical60-epoch schedule')
            path=folder/'warm_start.json'
            if path.exists():assert json.loads(path.read_text())==record,'transfer source changed'
            else:write_json(path,record)
            jobs.append((str(root),kw,'uart_e',seed,60,'phase_n_to_e_v6'))
    batch_jobs(root,jobs,args.workers,label)
