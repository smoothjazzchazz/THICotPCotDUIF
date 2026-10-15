"""Separate warmed neural state from the unchanged generic feature suffix."""
import json
import numpy as np
from .run import ROOT,digest
from .data import load,metrics
from .shapes import make_shape,features
from .runtime import run
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs/connectivity01';rows=[]
    for profile,seed,case in [('uart_n',47,'idle_007'),('uart_n',47,'idle_066'),('uart_n',71,'idle_179'),('uart_e',47,'idle_207')]:
        b=json.loads(next((root/'models/final_portfolio_v2a').glob(f'*/{profile}/{seed}/block_0000.json')).read_text());sh=make_shape(**b['construction']);a=np.load(b['checkpoint']);p=a['p'];sh.leaks=a['leaks'];s=load(root/'data_startup_modes'/profile/case)
        prefix=np.ones((16,3),dtype=np.uint8);xp=features(np.r_[prefix,s['lines']])[0];assert np.array_equal(xp[16:],s['x'])
        _,warm,z,_,_=run(sh,p,xp[:16]);outcomes=[]
        for mode in ('zero','first','fast','slow','all'):
            initial=np.zeros(sh.n)
            if mode=='all':initial=warm.copy()
            elif mode!='zero':
                nodes=sh.groups[{'first':0,'fast':1,'slow':2}[mode]];initial[nodes]=warm[nodes]
            h=initial;pred=[]
            for start in range(0,len(s['x']),8192):
                _,h,logits,_,_=run(sh,p,s['x'][start:start+8192],h=h);pred.extend(logits.argmax(1).tolist())
            score=metrics(s,np.array(pred,dtype=np.int32));outcomes.append(dict(initial_state_intervention=mode,**{k:score[k] for k in ('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted')}))
        row=dict(profile=profile,seed=seed,case=case,checkpoint_sha256=digest(b['checkpoint']),feature_suffix_bitwise_identical=True,last_warmup_class=int(z[-1].argmax()),outcomes=outcomes);rows.append(row)
        print(json.dumps(row),flush=True)
    write_json(root/'diagnostics/startup_state_attribution_v5.json',dict(scope='counterfactual initial-state probes, never a runtime reset or qualification substitute',rows=rows))
