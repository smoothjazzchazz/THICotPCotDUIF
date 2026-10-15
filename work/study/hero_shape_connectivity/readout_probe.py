"""Fit only the existing linear readout on fixed, causal recurrent trajectories."""
import argparse
import ctypes
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load,metrics
from .runtime import run
from .train import key,write_json


def compile_kernel():
    path=ROOT/'build'/'state_kernel.so';path.parent.mkdir(exist_ok=True)
    subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(ROOT/'state_kernel.cpp'),'-o',str(path)],check=True)


def trajectory(sh,p,x):
    if getattr(sh,'mixed',False):
        from .mixed_trajectory import trajectory as mixed_trajectory
        return mixed_trajectory(sh,p,x)
    f=ctypes.CDLL(str(ROOT/'build'/'state_kernel.so')).states_sequence
    f.argtypes=[ctypes.c_int]*3+[ctypes.c_void_p]*7;f.restype=None
    states=np.zeros((len(x)+1,sh.n));x=np.ascontiguousarray(x,dtype=np.float64)
    f(len(x),sh.n,len(sh.src),*[a.ctypes.data for a in (sh.src,sh.dst,sh.delay,sh.leaks,p,x,states)])
    if not np.array_equal(states[-1],run(sh,p,x)[1]):raise AssertionError('state trace changed recurrence')
    return states[1:]


def fit(block,output,epochs,root):
    output.mkdir(parents=True,exist_ok=True)
    b=json.loads(block.read_text());sh=make_shape(**b['construction']);a=dict(np.load(b['checkpoint']));p=a['p'].copy()
    if 'leaks' in a:sh.leaks=a['leaks'].copy()
    provenance=dict(source_block=str(block),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
        seed=b['seed'],trainable='existing six linear readouts and their biases only',states='fixed causal trajectories; no teacher enters inference',
        lr=.003,minibatch=4096,source_hashes={name:digest(ROOT/name) for name in ('readout_probe.py','state_kernel.cpp')})
    meta=output/'provenance.json'
    if meta.exists() and json.loads(meta.read_text())!=provenance:raise ValueError('probe source differs')
    write_json(meta,provenance)
    for name in ('readout_probe.py','state_kernel.cpp'):shutil.copy2(ROOT/name,output/name)
    streams=[load(root/'data'/b['profile']/f'mixed_{i:02d}') for i in range(12)]
    h=np.concatenate([trajectory(sh,p,s['x']) for s in streams]);y=np.concatenate([s['labels'] for s in streams])
    dev=load(root/'data'/b['profile']/'dev');dh=trajectory(sh,p,dev['x']);offset=len(sh.src)+sh.n
    w=p[offset:offset+6*sh.n].reshape(6,sh.n).copy();bias=p[-6:].copy();mw=np.zeros_like(w);vw=mw.copy();mb=np.zeros(6);vb=mb.copy()
    counts=np.bincount(y,minlength=6);cw=np.minimum(16,np.sqrt(max(counts)/np.maximum(1,counts)));cw[[3,4,5]]*=1.5
    journal=output/'history.jsonl';history=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    if history:
        last=history[-1]['epoch'];resume=np.load(output/f'epoch_{last:04d}.npz')
        w=resume['w'];bias=resume['bias'];mw=resume['mw'];vw=resume['vw'];mb=resume['mb'];vb=resume['vb'];step=int(resume['step'])
    else:last=step=0
    best=max(history,key=key,default=None)
    for epoch in range(last+1,epochs+1):
        order=np.random.default_rng([b['seed'],epoch,99213]).permutation(len(y));losses=[]
        for first in range(0,len(y),4096):
            idx=order[first:first+4096];x=h[idx];target=y[idx];z=x@w.T+bias;z-=z.max(1,keepdims=True)
            probs=np.exp(z);probs/=probs.sum(1,keepdims=True)
            losses.append(float(np.mean(-np.log(np.maximum(1e-300,probs[np.arange(len(idx)),target]))*cw[target])))
            probs[np.arange(len(idx)),target]-=1;probs*=cw[target,None]/len(idx)
            gw=probs.T@x;gb=probs.sum(0);norm=np.sqrt((gw*gw).sum()+(gb*gb).sum());gw/=max(1,norm);gb/=max(1,norm)
            step+=1;mw=.9*mw+.1*gw;vw=.999*vw+.001*gw*gw;mb=.9*mb+.1*gb;vb=.999*vb+.001*gb*gb
            w-=.003*(mw/(1-.9**step))/(np.sqrt(vw/(1-.999**step))+1e-8);bias-=.003*(mb/(1-.9**step))/(np.sqrt(vb/(1-.999**step))+1e-8)
            np.clip(w,-7.99,7.99,out=w);np.clip(bias,-7.99,7.99,out=bias)
        z=dh@w.T+bias;row=dict(epoch=epoch,train_loss=float(np.mean(losses)),exposure_ticks=epoch*len(y));row.update(metrics(dev,z.argmax(1)));row['dev_loss']=0.
        p[offset:offset+6*sh.n]=w.ravel();p[-6:]=bias
        actual=run(sh,p,dev['x'])[2]
        if not np.array_equal(actual.argmax(1),z.argmax(1)):raise AssertionError('BLAS readout decisions differ from deployed scalar kernel')
        if best is None or key(row)>key(best):best=row.copy();np.savez_compressed(output/'selected.npz',p=p,leaks=sh.leaks)
        np.savez_compressed(output/f'epoch_{epoch:04d}.npz',p=p,leaks=sh.leaks,w=w,bias=bias,mw=mw,vw=vw,mb=mb,vb=vb,step=step)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
    write_json(output/'result.json',dict(source=b,best=best,epochs=epochs,exposure_ticks=epochs*len(y),qualification=False,
        limitation='development readout optimization diagnostic; not a converged infeasibility proof or fresh confirmation'))
    print(json.dumps(dict(shape=sh.name,profile=b['profile'],seed=b['seed'],best=best['message_accuracy'],boundary=best['boundary_errors'])))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--compile',action='store_true');ap.add_argument('--block',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--epochs',type=int,default=60);a=ap.parse_args()
    if a.compile:compile_kernel()
    else:fit(a.block,a.output,a.epochs,ROOT/'runs'/'connectivity01')
