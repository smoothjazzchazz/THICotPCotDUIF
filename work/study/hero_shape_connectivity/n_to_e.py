"""Same-seed timing transfer only for still-unresolved parity configurations."""
import json
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape,SEEDS
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];sh=make_shape(**kw);jobs=[]
    if not (root/'data_precision_v2'/'manifest_0300.json').exists():raise ValueError('complete verified 300-bank corpus is required before transfer')
    for seed in SEEDS:
        e_source=root/'models'/'phase_margin_calibration_v3'/sh.name/'uart_e'/str(seed)/'block_0001.json';e=json.loads(e_source.read_text());s=e['selected']
        passed=s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
        source=e_source if passed else root/'models'/'phase_margin_calibration_v3'/sh.name/'uart_n'/str(seed)/'block_0001.json'
        b=json.loads(source.read_text());folder=root/'models'/'phase_n_to_e_v3'/sh.name/'uart_e'/str(seed);folder.mkdir(parents=True,exist_ok=True)
        record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(source),source_profile=b['profile'],target_profile='uart_e',
            source_seed=seed,target_seed=seed,reset_optimizer=True,data_epoch_offset=240,source_provenance=b.get('warm_start'),
            policy='retain already-passing E unchanged; otherwise initialize E from the same seed successful N and train separate E weights')
        path=folder/'warm_start.json'
        if path.exists():
            if json.loads(path.read_text())!=record:raise ValueError('transfer source changed')
        else:write_json(path,record)
        jobs.append((str(root),kw,'uart_e',seed,0 if passed else 60,'phase_n_to_e_v3'))
    batch_jobs(root,jobs,2,'n_to_e_v3_60')
