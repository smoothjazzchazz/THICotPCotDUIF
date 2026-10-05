"""Verify preservation, historical settings, and independent baseline streaming."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from work.study.shared.broad import ROOT, save, reserve
from work.study.shared.comparison import emit_events
from work.study.shared.signals import SignalStream
from work.model.reservoir_model import ReservoirReceiver


def main():
    confirmation=ROOT/'results/broad-confirmation/20261005T012024.954575Z'
    f=json.loads((confirmation/'freeze.json').read_text())
    with gzip.open(confirmation/'test_streams.json.gz','rt') as file:streams=[SignalStream(**s) for s in json.load(file)]
    with gzip.open(confirmation/'traces.json.gz','rt') as file:traces=json.load(file)
    oldmix=json.loads((ROOT/'results/mixed-leaks-seed24-test104/config.json').read_text())
    oldchain=json.loads((ROOT/'results/delay-chains-test105/config.json').read_text())
    rows=[]
    for name,entry in f['baselines'].items():
        old=(oldmix['candidates'][name[6:]] if name.startswith('mixed_') else oldchain['candidates'][name])
        for method,settings in entry['methods'].items():
            actual=settings['receiver'];original=old['methods'][method]['receiver']
            a=json.loads(json.dumps(actual));b=json.loads(json.dumps(original))
            differences=[]
            if method!='hamming':
                for k in ('weights','bias'):
                    differences.append(float(np.max(np.abs(np.asarray(a['readout'].pop(k))-np.asarray(b['readout'].pop(k))))))
            if a!=b or max(differences,default=0)>1e-8:raise AssertionError('Material historical setting difference')
            # Use the ORIGINAL saved coefficients, independently of the refit.
            indices=range(len(streams)) if (name,method) in (('mixed_cycle3210','linear_full'),('level_chain','hamming')) else (0,6)
            for index in indices:
                receiver=ReservoirReceiver.from_dict(original);events=[];pred=[]
                for tick,u in enumerate(streams[index].levels):
                    event=receiver.step(u,tick);pred.append(receiver.observation['class_id'])
                    if event:events.append({**event,'emit_tick':tick})
                expected=traces['predictions'][name+'/'+method][index]
                if pred!=expected:raise AssertionError(f'Historical predictions differ: {name}/{method}/{index}')
                if events!=emit_events(expected,original['hold_ticks']):raise AssertionError('Historical events differ')
            rows.append({'baseline':name+'/'+method,'max_coefficient_refit_difference':max(differences,default=0),'original_saved_receiver_streams_verified':len(indices)})
            print(name,method,'verified',len(indices),flush=True)
    prior=json.loads((ROOT/'broad_search/historical_hashes.json').read_text())
    allowed={'work/study/README.md','work/study/shared/README.md'}
    changed=[p for p,h in prior.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h and p not in allowed]
    if changed:raise AssertionError('Historical files changed: '+str(changed))
    for p,h in f['source_sha256'].items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:raise AssertionError('Frozen source changed: '+p)
    out=reserve('delivery-verification','reproducibility',{'confirmation':str(confirmation)})
    save(out/'verification.json',{'historical_files_checked':len(prior),'unexpected_changes':changed,'frozen_sources_unchanged':True,'baseline_checks':rows,
                               'note':'Refitting with one BLAS thread changes tiny floating-point roundoff only; original saved baseline decisions and events independently checked.'})
    print(out,flush=True)

if __name__=='__main__':main()
