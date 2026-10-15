"""Remove conditional gate inputs while preserving learned constant gate biases."""
import json,math,shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,cost
from .runtime import run
from .startup_evaluate import evaluate
from .train import key,write_json


def convert(sh,p,kw):
    plain=make_shape(**{**kw,'cell':'plain'});plain.leaks=sh.leaks.copy()
    for name in ('src','dst','delay'):assert np.array_equal(getattr(sh,name),getattr(plain,name))
    start=len(sh.src)+sh.n;ge=len(sh.gate_src);gn=len(sh.gate_nodes)
    clamped=p.copy();clamped[start:start+ge]=0
    plain.leaks[sh.gate_nodes]=[.5*(1+math.tanh(.5*v)) for v in p[start+ge:start+ge+gn]]
    reduced=np.r_[p[:start],p[start+ge+gn:]]
    rng=np.random.default_rng(81327);x=rng.uniform(-1,1,(513,9));h=rng.uniform(-1,1,sh.n)
    a=run(sh,clamped,x,h=h);b=run(plain,reduced,x,h=h)
    assert np.array_equal(a[1],b[1]) and np.array_equal(a[2],b[2]),'constant-gate conversion mismatch'
    return plain,reduced


def audit(job):
    root,kw,profile,seed,record=job;root=Path(root);sh=make_shape(**kw)
    assert digest(record['source_block'])==record['source_block_sha256']
    b=json.loads(Path(record['source_block']).read_text());assert digest(b['checkpoint'])==record['checkpoint_sha256']
    a=dict(np.load(b['checkpoint']));sh.leaks=a['leaks'].copy();plain,p=convert(sh,a['p'],kw)
    recipe='gate_bias_clamp_v6a';folder=root/'models'/recipe/plain.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
    dl,score=evaluate(plain,p,root,profile,np.array(b['class_weights']));score.update(epoch=0,dev_loss=dl,exposure_ticks=0)
    checkpoint=folder/'epoch_0000.npz';meta=json.loads(str(a['metadata']));meta.update(recipe=recipe,epoch=0,step=0,exposure=0)
    np.savez_compressed(checkpoint,**{**a,'p':p,'leaks':plain.leaks,'m':np.zeros_like(p),'v':np.zeros_like(p),'metadata':json.dumps(meta)})
    result=dict(shape=plain.name,construction={**kw,'cell':'plain'},profile=profile,seed=seed,recipe=recipe,epochs=0,selected_epoch=0,
        selected=score,checkpoint=str(checkpoint),class_weights=b['class_weights'],exposure_ticks=0,source_training_exposure_ticks=b['exposure_ticks'],
        warm_start=record,resources=cost(plain),development_distribution='precision_v2_plus_corners_v4_plus_startup_v5',
        status='gate_input_ablation_no_refit_no_confirmation; retained biases become ordinary per-node leaks')
    write_json(folder/'block_0000.json',result)
    print(json.dumps(dict(profile=profile,seed=seed,exact=score['exact_messages'],messages=score['valid_messages'],boundary=score['boundary_errors'])),flush=True)
    return result


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';label='gate_bias_clamp_v6a';file=root/f'{label}_jobs.json'
    if file.exists():raise ValueError('frozen diagnostic already launched; resume its original snapshot explicitly')
    kw=json.loads((ROOT/'mixed_first_candidates.json').read_text())[1];sh=make_shape(**kw);jobs=[]
    for profile,seed in [('uart_n',11),('uart_n',29),('uart_n',47),('uart_e',29),('uart_e',47)]:
        options=[]
        for path in (root/'models').glob(f'*/{sh.name}/{profile}/{seed}/block_*.json'):
            b=json.loads(path.read_text())
            if b.get('development_distribution')=='precision_v2_plus_corners_v4_plus_startup_v5':options.append((path,b))
        path,b=max(options,key=lambda pair:key(pair[1]['selected']));s=b['selected']
        assert s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
        record=dict(source_block=str(path),source_block_sha256=digest(path),checkpoint_sha256=digest(b['checkpoint']),policy='freeze completed full enlarged-development pass; zero gate-input weights; no refit')
        jobs.append((str(root),kw,profile,seed,record))
    write_json(file,jobs);snapshot=root/'batch_sources'/label;snapshot.mkdir(parents=True)
    for p in ROOT.rglob('*'):
        if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
            q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=1) as pool:
        for f in as_completed([pool.submit(audit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
