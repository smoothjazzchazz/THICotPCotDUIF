"""Show that the core numerical code changed only where node dimensions require it."""
import inspect,json
from pathlib import Path
import numpy as np
from work.model import stream_reservoir as old
from work.study.protocol_reservoir32_i2c_training30 import receiver as new
from work.study.protocol_reservoir64.training import loss_gradient as old_gradient
from work.study.protocol_reservoir32_i2c_training30.bptt import loss_gradient as new_gradient
from work.study.protocol_reservoir64_training30.training import adam_step as old_adam
from work.study.protocol_reservoir32_i2c_training30.training import adam_step as new_adam
checks={}
for name in ('step',):
    checks['receiver_'+name+'_source_identical']=inspect.getsource(getattr(old.StreamReceiver,name))==inspect.getsource(getattr(new.StreamReceiver,name))
for name in ('LineFeatures','features','StreamEvent','rounded_shift','connection_mask'):
    checks[name+'_source_identical']=inspect.getsource(getattr(old,name))==inspect.getsource(getattr(new,name))
a=inspect.getsource(old_gradient).replace('size, 64','size, NODES').replace('reshape(-1, 64)','reshape(-1, NODES)')
checks['BPTT_identical_after_dimension_substitution']=a==inspect.getsource(new_gradient)
checks['Adam_source_identical']=inspect.getsource(old_adam)==inspect.getsource(new_adam)
checks['leak_schedule_same_prefix']=bool(np.array_equal(old.LEAKS[:32],new.LEAKS))
assert all(checks.values()),checks
root=Path(__file__).resolve().parents[1]
(root/'audit/implementation_delta.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks))
