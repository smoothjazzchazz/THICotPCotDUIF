"""Frozen-weight causal probe: extra observable idle before an actual cold file."""
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,features
from .data import load,metrics
from .train import evaluate_stream,write_json
from .runtime import pulses,events
from .vendor.data import reference_labels,assemble

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';rows=[]
    for profile,seed,names in [('uart_n',47,['idle_007','idle_027','idle_066','idle_093','idle_113','idle_169','errors_036']),('uart_n',71,['idle_179']),('uart_e',47,['idle_207']),('uart_e',101,['idle_088'])]:
        block=next((root/'models/final_portfolio_v2a').glob(f'*/{profile}/{seed}/block_0000.json'));b=json.loads(block.read_text());sh=make_shape(**b['construction']);a=np.load(b['checkpoint']);p=a['p'];sh.leaks=a['leaks']
        for name in names:
            base=load(root/'data_startup_modes'/profile/name)
            for idle in [0,16,64,256,1024]:
                lines=np.r_[np.ones((idle,3),dtype=np.uint8),base['lines']];labels=reference_labels(lines,profile)
                assert np.array_equal(labels[idle:],base['labels'])
                truth,rejections=assemble(events(labels),profile)
                s={**base,'lines':lines,'labels':labels,'x':features(lines)[0],'truth':truth,'reference_rejections':rejections,
                   'groups':[{**g,'start':g['start']+idle,'end':g['end']+idle} for g in base['groups']]}
                _,z=evaluate_stream(sh,p,s,np.ones(6));score=metrics(s,z.argmax(1));bad=np.flatnonzero(pulses(z.argmax(1))!=labels)
                row=dict(profile=profile,seed=seed,case=name,extra_idle=idle,checkpoint_sha256=digest(b['checkpoint']),
                    **{k:score[k] for k in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted')},first_pulse_error_relative=int(bad[0]-idle) if len(bad) else None)
                rows.append(row)
            print(json.dumps(dict(profile=profile,seed=seed,case=name,outcomes=[(r['extra_idle'],r['exact_messages'],r['boundary_errors']) for r in rows[-5:]])),flush=True)
    write_json(root/'diagnostics/startup_extra_idle_probe_v5.json',dict(scope='frozen-weight causal diagnostic only; no learned or runtime reset and no gate substitution',rows=rows))
