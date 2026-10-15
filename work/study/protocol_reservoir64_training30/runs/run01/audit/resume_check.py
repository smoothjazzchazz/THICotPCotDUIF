"""Replay actual epoch 30 from saved epoch-29 optimizer states, without saving weights."""
import json
from pathlib import Path
import numpy as np
from work.study.protocol_reservoir64.data import load_split
from work.study.protocol_reservoir64.training import batch, loss_gradient
from work.study.protocol_reservoir64_training30.training import restore_optimizer, adam_step, CHUNK

root=Path(__file__).resolve().parents[1]
results=[]
for profile in ('uart_n','uart_e','i2c'):
    train=batch(load_split(root,profile,'train'))
    x,y,valid=train
    for variant in ('seed_11','original_loss_11'):
        directory=root/'models'/profile/variant
        fit=json.loads((directory/'fit.json').read_text())
        w,m,v,meta=restore_optimizer(directory/'optimizer_29.npz')
        step=meta['step'];state=np.zeros((12,64))
        for a in range(0,len(x),CHUNK):
            _,state,grad=loss_gradient(w,x[a:a+CHUNK],y[a:a+CHUNK],valid[a:a+CHUNK],state,np.array(fit['class_weights']))
            step+=1;adam_step(w,grad,m,v,step)
        expected,em,ev,last=restore_optimizer(directory/'optimizer_30.npz')
        assert step==last['step']
        for aa,bb in ((w,expected),(m,em),(v,ev)):
            for k in aa: np.testing.assert_array_equal(aa[k],bb[k])
        with np.load(directory/'optimizer_30.npz') as saved:
            np.testing.assert_array_equal(state,saved['ending_state'])
        results.append(dict(profile=profile,variant=variant,epoch29_to_30_exact=True,steps=step))
(root/'audit/resume_check.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))
