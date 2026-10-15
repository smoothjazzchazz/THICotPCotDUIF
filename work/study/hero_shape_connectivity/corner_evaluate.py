"""Old development gates plus independent corner cases; optional fixed-state cache."""
from pathlib import Path
import json
import numpy as np
from .data import load,metrics
from .train import evaluate_stream,write_json
from .readout_probe import trajectory
from .run import digest


def evaluate(sh,p,root,profile,cw,cache=None,extra_paths=()):
    cases=[];loss_sum=0.;ticks=0
    fields=('exact_messages','valid_messages','byte_exact_messages','boundary_errors','invalid_accepted','background_accepted','false_events','missed_events')
    total={k:0 for k in fields};total['conditions']={}
    paths=[('original_'+f.stem,f) for f in sorted((root/'data_precision_v2'/profile/'dev').glob('*.json'))]
    paths += [('corner_'+f.stem,f) for f in sorted((root/'data_corner_dev_v4'/profile).glob('*.json'))]
    if len([name for name,path in paths if name.startswith('corner_')])!=4:raise ValueError('all four new corner files required')
    paths.extend(extra_paths)
    offset=sh.parameters-6*sh.n-6
    if cache is not None:
        cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
        import hashlib
        stamp=hashlib.sha256(p[:offset].tobytes()+sh.leaks.tobytes()).hexdigest();manifest=cache/'state_identity.json'
        if manifest.exists():assert json.loads(manifest.read_text())['state_sha256']==stamp
        else:write_json(manifest,dict(state_sha256=stamp,shape=sh.name,dtype='float64',data_files={str(f):digest(f) for n,f in paths}))
    for name,path in paths:
        s=load(path.with_suffix(''))
        if cache is None:loss,z=evaluate_stream(sh,p,s,cw)
        else:
            file=cache/(name+'.npy')
            if not file.exists():
                h=trajectory(sh,p,s['x']);np.save(file,h);del h
            h=np.load(file,mmap_mode='r');z=np.empty((len(h),6));value=0.
            for start in range(0,len(h),8192):
                zz=h[start:start+8192]@p[offset:-6].reshape(6,sh.n).T+p[-6:];z[start:start+len(zz)]=zz
                y=s['labels'][start:start+len(zz)];top=zz.max(1)
                value+=float(np.sum(cw[y]*(np.log(np.exp(zz-top[:,None]).sum(1))+top-zz[np.arange(len(y)),y])))
            loss=value/len(z)
        r=metrics(s,z.argmax(1));r['case']=name;cases.append(r);loss_sum+=loss*len(z);ticks+=len(z)
        for field in fields:total[field]+=r[field]
        for condition,row in r['conditions'].items():
            dest=total['conditions'].setdefault(condition,dict(valid_messages=0,exact_messages=0,byte_exact_messages=0))
            for k in dest:dest[k]+=row[k]
    for row in total['conditions'].values():row['message_accuracy']=row['exact_messages']/row['valid_messages']
    total.update(message_accuracy=total['exact_messages']/total['valid_messages'],boundary_f1=min(c['boundary_f1'] for c in cases),cases=cases,ticks=ticks)
    return loss_sum/ticks,total
