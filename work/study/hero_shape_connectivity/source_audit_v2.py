"""Evaluate each seed's already-trained alternatives on corrected development."""
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .precision_data import evaluate
from .train import write_json


def inspect(job):
    profile,seed,recipe,epochs=job;root=ROOT/'runs'/'connectivity01';kwargs=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];sh=make_shape(**kwargs)
    folder=root/'source_audit_v2'/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);out=folder/f'{recipe}_{epochs}.json'
    if out.exists():return json.loads(out.read_text())
    block=root/'models'/recipe/sh.name/profile/str(seed)/f'block_{epochs:04d}.json';b=json.loads(block.read_text());a=np.load(b['checkpoint']);sh.leaks=a['leaks'].copy()
    loss,r=evaluate(sh,a['p'],root,profile,np.ones(6),'data_precision_v2');r['dev_loss']=loss
    row=dict(profile=profile,seed=seed,source_recipe=recipe,source_block=str(block),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),development=r,qualification=False)
    write_json(out,row);print(profile,seed,recipe,r['message_accuracy'],r['boundary_errors'],flush=True);return row


if __name__=='__main__':
    jobs=[(p,s,r,e) for p in ('uart_n','uart_e') for s in SEEDS for r,e in [('phase_ring_fixed',600),('phase_portfolio',300)]]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(inspect,j) for j in jobs]):f.result()
