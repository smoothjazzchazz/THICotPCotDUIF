"""Check actual complete training cases before assuming a development pass is trained."""
import argparse,json
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load,metrics
from .train import evaluate_stream,write_json
from .runtime import pulses


def audit(job):
    root,entry=job;out=ROOT/'runs'/'connectivity01'/'confirmations'/'full_shape_v2a';sh=make_shape(**entry['construction']);a=np.load(out/entry['weight_path']);p=a['p'];sh.leaks=a['leaks'].copy()
    rows=[]
    for path in sorted((ROOT/'runs'/'connectivity01'/'data_startup_modes'/entry['profile']).glob('*.json')):
        data=load(path.with_suffix(''));_,z=evaluate_stream(sh,p,data,np.ones(6));pred=z.argmax(1);r=metrics(data,pred)
        fields=('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted','false_events','missed_events')
        bad=np.flatnonzero(pulses(pred)!=data['labels'])
        rows.append(dict(case=path.stem,path=str(path),metadata_sha256=digest(path),arrays_sha256=digest(path.with_suffix('.npz')),
            **{k:r[k] for k in fields},first_pulse_error_ticks=bad[:16].tolist()))
    result=dict(profile=entry['profile'],seed=entry['seed'],source_weight_sha256=entry['weight_sha256'],cases=rows,
        failed_cases=sum(bool(r['exact_messages']!=r['valid_messages'] or r['boundary_errors'] or r['invalid_accepted'] or r['background_accepted']) for r in rows),
        exact_messages=sum(r['exact_messages'] for r in rows),valid_messages=sum(r['valid_messages'] for r in rows),boundary_errors=sum(r['boundary_errors'] for r in rows),
        scope='existing independent training-case audit; no weight updates and no confirmation data fitted')
    folder=ROOT/'runs'/'connectivity01'/'diagnostics'/'training_startup_audit_v4';folder.mkdir(exist_ok=True)
    write_json(folder/f"{entry['profile']}_{entry['seed']}.json",result)
    print(json.dumps({k:result[k] for k in ('profile','seed','failed_cases','exact_messages','valid_messages','boundary_errors')}),flush=True);return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';out=root/'confirmations'/'full_shape_v2a';config=json.loads((out/'freeze.json').read_text());jobs=[]
    for e in config['entries']:
        if not e['profile'].startswith('uart'):continue
        s=json.loads((out/'results'/e['shape']/e['profile']/f"float_{e['seed']}"/'summary.json').read_text())
        if not s['pass_all']:jobs.append((str(root),e))
    rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for f in as_completed([pool.submit(audit,j) for j in jobs]):rows.append(f.result());write_json(root/'training_startup_audit_v4_ledger.json',dict(completed=rows,total=len(jobs)))
