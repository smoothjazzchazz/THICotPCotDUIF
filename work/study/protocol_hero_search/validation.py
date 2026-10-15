"""Checkpoint continuation, source preservation, and complete artifact audits."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import numpy as np
from .shapes import make_shape
from .network import run
from .training import load_data,write_json
from .run import ROOT,digest


def continuation(root):
    chosen=json.loads((root/'screen_selection.json').read_text())['advanced'];rows=[]
    for candidate in chosen:
        for profile in ('uart_n','uart_e','i2c','spi0'):
            regime=candidate['profiles'][profile]['regime'];sh=make_shape(candidate['variant'],candidate['nodes'])
            directory=root/'models'/sh.name/profile/f'{regime}_11'
            with np.load(directory/'epoch_0059.npz',allow_pickle=False) as a:
                p=a['p'].copy();m=a['m'].copy();v=a['v'].copy();meta=json.loads(str(a['metadata']))
            fit=json.loads((directory/'screen_done.json').read_text());cw=np.array(fit['class_weights'])
            d=load_data(root,profile,'mixed');h=np.zeros(sh.n);step=meta['step']
            for t in range(0,len(d['x']),512):
                _,h,_,g,_=run(sh,p,d['x'][t:t+512],d['labels'][t:t+512],cw,h,True,regime=='esn')
                g/=max(1.,float(np.linalg.norm(g)));step+=1
                m=.9*m+.1*g;v=.999*v+.001*g*g
                p-=.003*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8);np.clip(p,-7.99,7.99,out=p)
            with np.load(directory/'epoch_0060.npz',allow_pickle=False) as a:
                exact=all(np.array_equal(a[k],value) for k,value in [('p',p),('m',m),('v',v),('ending_state',h)])
            rows.append(dict(shape=sh.name,profile=profile,exact_epoch_59_to_60=exact))
    write_json(root/'continuation_audit.json',rows)
    if not all(r['exact_epoch_59_to_60'] for r in rows):raise AssertionError('continuation mismatch')


def verify_model_history(path):
    checkpoints=0;missing=[];nonfinite=[]
    history=json.loads(path.read_text())
    for row in history:
        cp=path.parent/f"epoch_{row['epoch']:04d}.npz"
        if not cp.exists():missing.append(str(cp));continue
        with np.load(cp,allow_pickle=False) as a:
            for name in ('p','m','v','ending_state'):
                if not np.all(np.isfinite(a[name])):nonfinite.append(str(cp))
            meta=json.loads(str(a['metadata']))
            if meta['epoch']!=row['epoch']:missing.append(str(cp)+' epoch mismatch')
        checkpoints+=1
    return checkpoints,missing,nonfinite


def verify(root):
    baseline=json.loads((root/'preservation.json').read_text())
    changed=[p for p,h in baseline.items() if not Path(p).is_file() or digest(p)!=h]
    frozen=json.loads((root/'freeze.json').read_text())['hashes']
    freeze_changed=[p for p,h in frozen.items() if not (root/p).exists() or digest(root/p)!=h]
    current_source_changed=[]
    for name,h in frozen.items():
        if not name.startswith('frozen_source/'):continue
        source=ROOT/'build'/'kernel.so' if name.endswith('/kernel.so') else ROOT/Path(name).name
        if not source.exists() or digest(source)!=h:current_source_changed.append(str(source))
    data=json.loads((root/'confirmation_data_hashes.json').read_text())
    data_changed=[p for p,h in data.items() if digest(root/p)!=h]
    # Every history record must have a resumable checkpoint and correct epoch metadata.
    checkpoints=0;missing=[];nonfinite=[]
    with ProcessPoolExecutor(max_workers=16) as pool:
        for n,m,f in pool.map(verify_model_history,(root/'models').rglob('history.json')):
            checkpoints+=n;missing.extend(m);nonfinite.extend(f)
    report=dict(preservation_checked=len(baseline),preservation_changed=changed,
                frozen_changes=freeze_changed,data_changes=data_changed,
                current_source_changes=current_source_changed,
                checkpoints_checked=checkpoints,missing=missing,nonfinite=nonfinite,
                passed=not(changed or freeze_changed or current_source_changed or data_changed or missing or nonfinite))
    write_json(root/'verification.json',report)
    if not report['passed']:raise AssertionError(report)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['continuation','verify']);p.add_argument('--output',type=Path,default=ROOT/'runs'/'run01')
    a=p.parse_args();globals()[a.action](a.output)

if __name__=='__main__':main()
