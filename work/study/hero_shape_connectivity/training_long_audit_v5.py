"""Audit unused-to-selection training streams, never confirmation waveforms."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load
from .runtime import pulses
from .train import evaluate_stream,write_json


def audit(job):
    profile,seed=job;root=ROOT/'runs'/'connectivity01';source=next((root/'models/final_portfolio_v2a').glob(f'*/{profile}/{seed}/block_0000.json'));b=json.loads(source.read_text());sh=make_shape(**b['construction']);a=np.load(b['checkpoint']);p=a['p'];sh.leaks=a['leaks'];rows=[]
    for bank in range(365,397):
        path=root/'data_precision_v2'/profile/'train'/f'long_{bank:04d}';s=load(path);_,z=evaluate_stream(sh,p,s,np.ones(6));pred=pulses(z.argmax(1));bad=np.flatnonzero((pred!=s['labels'])&(np.arange(len(pred))>=s.get('startup_ambiguous_until',0)))
        first=[];last=-1024
        for t in bad:
            if t-last<512:continue
            order=np.argsort(z[t])[::-1];first.append(dict(tick=int(t),truth=int(s['labels'][t]),predicted_pulse=int(pred[t]),top_classes=order[:2].tolist(),logits=z[t].tolist()));last=int(t)
        rows.append(dict(bank=bank,path=str(path),metadata_sha256=digest(path.with_suffix('.json')),arrays_sha256=digest(path.with_suffix('.npz')),
            scored_pulse_errors=len(bad),boundary_pulse_errors=int(np.sum((np.isin(pred[bad],[3,4])|np.isin(s['labels'][bad],[3,4])))),separated_failure_origins=first))
    result=dict(profile=profile,seed=seed,checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),cases=rows,
        total_pulse_errors=sum(r['scored_pulse_errors'] for r in rows),boundary_pulse_errors=sum(r['boundary_pulse_errors'] for r in rows),failed_streams=sum(r['scored_pulse_errors']>0 for r in rows),
        scope='training-only audit; pulse counts are not complete-message qualification; no weight changes')
    folder=root/'diagnostics/training_long_audit_v5';folder.mkdir(exist_ok=True);write_json(folder/f'{profile}_{seed}.json',result)
    print(json.dumps({k:result[k] for k in ('profile','seed','total_pulse_errors','boundary_pulse_errors','failed_streams')}),flush=True);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);a=ap.parse_args();root=ROOT/'runs'/'connectivity01';rows=[]
    jobs=[('uart_n',s) for s in (71,101,131)]+[('uart_e',s) for s in (11,101,131)]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(audit,j) for j in jobs]):rows.append(f.result());write_json(root/'training_long_audit_v5_ledger.json',dict(completed=rows,total=len(jobs)))
