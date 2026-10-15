"""Audit frozen sources on independently generated sustained TRAINING corners."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .data import load,metrics
from .train import evaluate_stream,write_json
from .runtime import pulses


def audit(job):
    profile,seed=job;root=ROOT/'runs'/'connectivity01';source=next((root/'models/final_portfolio_v2a').glob(f'*/{profile}/{seed}/block_0000.json'));b=json.loads(source.read_text());sh=make_shape(**b['construction']);a=np.load(b['checkpoint']);p=a['p'];sh.leaks=a['leaks'];rows=[]
    for path in sorted((root/'data_stationary_train_v6'/profile).glob('*.json')):
        s=load(path.with_suffix(''));_,z=evaluate_stream(sh,p,s,np.ones(6));pred=z.argmax(1);r=metrics(s,pred);bad=np.flatnonzero(pulses(pred)!=s['labels'])
        origins=[];last=-512
        for t in bad:
            if t-last>=512:origins.append(dict(tick=int(t),truth=int(s['labels'][t]),predicted=int(pulses(pred)[t])));last=int(t)
        rows.append(dict(case=path.stem,path=str(path.with_suffix('')),metadata_sha256=digest(path),arrays_sha256=digest(path.with_suffix('.npz')),
            **{k:r[k] for k in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted')},pulse_errors=len(bad),separated_error_origins=origins))
    fields=('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted','pulse_errors')
    result=dict(profile=profile,seed=seed,checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),cases=rows,
        **{k:sum(row[k] for row in rows) for k in fields},scope='training-only frozen-source audit; not fresh confirmation')
    folder=root/'diagnostics/training_stationary_audit_v6';folder.mkdir(exist_ok=True);write_json(folder/f'{profile}_{seed}.json',result)
    print(json.dumps({k:result[k] for k in ('profile','seed','exact_messages','valid_messages','boundary_errors','pulse_errors')}),flush=True);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);a=ap.parse_args();root=ROOT/'runs'/'connectivity01';assert (root/'data_stationary_train_v6/manifest.json').exists()
    jobs=[(p,s) for p in ('uart_n','uart_e') for s in SEEDS];rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(audit,j) for j in jobs]):rows.append(f.result());write_json(root/'training_stationary_audit_v6_ledger.json',dict(completed=rows,total=len(jobs)))
