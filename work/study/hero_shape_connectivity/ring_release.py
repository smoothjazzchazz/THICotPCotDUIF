"""Late low-rate release of a protected ring, paired with its frozen control."""
import json
from .run import ROOT,digest,batch_jobs
from .shapes import make_shape
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];sh=make_shape(**kw);jobs=[]
    for seed in (71,131):
        source=root/'models'/'phase_margin_calibration_v3'/sh.name/'uart_e'/str(seed)/'block_0001.json';b=json.loads(source.read_text())
        for recipe in ('phase_ring_frozen_v4','phase_ring_release_v4'):
            folder=root/'models'/recipe/sh.name/'uart_e'/str(seed);folder.mkdir(parents=True,exist_ok=True)
            record=dict(checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),source_block=str(source),source_profile='uart_e',target_profile='uart_e',
                reset_optimizer=True,data_epoch_offset=240,source_provenance=b.get('warm_start'),
                policy='same low-rate coverage; release sixteen middle-ring weights and fifteen undriven biases only in release arm; no runtime change')
            path=folder/'warm_start.json'
            if path.exists():
                if json.loads(path.read_text())!=record:raise ValueError('ring comparison source changed')
            else:write_json(path,record)
            jobs.append((str(root),kw,'uart_e',seed,60,recipe))
    batch_jobs(root,jobs,4,'ring_release_v4_60')
