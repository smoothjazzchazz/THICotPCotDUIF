"""Same weights/data/budget, different offline progress partition only."""
import json
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];sh=make_shape(**kw);jobs=[]
    if not (root/'data_precision_v2'/'manifest_0300.json').exists():raise ValueError('verified 300-bank corpus required')
    for seed in (71,131):
        source=root/'models'/'phase_margin_calibration_v3'/sh.name/'uart_e'/str(seed)/'block_0001.json';b=json.loads(source.read_text())
        for recipe in ('phase_uniform_aux_v4','phase_stop_aux_v4'):
            folder=root/'models'/recipe/sh.name/'uart_e'/str(seed);folder.mkdir(parents=True,exist_ok=True)
            record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(source),source_profile='uart_e',target_profile='uart_e',
                reset_optimizer=True,data_epoch_offset=240,source_provenance=b.get('warm_start'),
                auxiliary_progress='0/48/96/160' if recipe=='phase_stop_aux_v4' else '0/48/96/144',third_head_reset_seed=seed+876510,
                policy='paired same-source offchip auxiliary partition diagnostic; deployed event labels and hardware unchanged')
            path=folder/'warm_start.json'
            if path.exists():
                if json.loads(path.read_text())!=record:raise ValueError('auxiliary comparison source changed')
            else:write_json(path,record)
            jobs.append((str(root),kw,'uart_e',seed,60,recipe))
    batch_jobs(root,jobs,4,'teacher_compare_v4_60')
