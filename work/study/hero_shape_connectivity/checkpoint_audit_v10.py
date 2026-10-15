"""Paired bounded saved-checkpoint selection for first-gate and plain controls."""
import json,hashlib,shutil
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from .run import ROOT,digest,source_files
from .shapes import make_shape,SEEDS
from .train import key,write_json
from .startup_margin_v5 import passed
from .checkpoint_audit_v5 import audit


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';label='checkpoint_audit_first_n_v10';manifest=root/f'{label}_jobs.json';sources=[];jobs=[]
    if manifest.exists():raise ValueError('frozen selection already prepared; resume its snapshot')
    for kw in json.loads((ROOT/'mixed_first_candidates.json').read_text()):
        sh=make_shape(**kw)
        for seed in SEEDS:
            options=[]
            for path in (root/'models').glob(f'*/{sh.name}/uart_n/{seed}/block_*.json'):
                b=json.loads(path.read_text())
                if b.get('development_distribution')=='precision_v2_plus_corners_v4_plus_startup_v5':options.append((path,b))
            source,b=max(options,key=lambda pair:key(pair[1]['selected']))
            if passed(b['selected']):continue
            sources.append(dict(shape=sh.name,profile='uart_n',seed=seed,block=str(source),block_sha256=digest(source)))
            def weight_identity(path):
                a=np.load(path);return hashlib.sha256(a['p'].tobytes()+a['leaks'].tobytes()).hexdigest()
            seen={weight_identity(b['checkpoint'])}
            for recipe in ('phase_native_v3','phase_native_refine_v3'):
                folder=root/'models'/recipe/sh.name/'uart_n'/str(seed);blocks=sorted(folder.glob('block_*.json'))
                if not blocks:continue
                path=blocks[-1];block=json.loads(path.read_text());history=folder/'history.jsonl';rows=[json.loads(s) for s in history.read_text().splitlines()];good=[r for r in rows if 'dev_loss' in r and passed(r)]
                if not good:continue
                for row in (good[0],good[-1]):
                    checkpoint=folder/f"epoch_{row['epoch']:04d}.npz";identity=weight_identity(checkpoint)
                    if identity in seen:continue
                    seen.add(identity);record=dict(id=f"{recipe}_{row['epoch']:04d}",checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),source_history=str(history),source_history_sha256=digest(history),source_block=str(path),source_block_sha256=digest(path),class_weights=block['class_weights'],source_epoch=row['epoch'],source_exposure_ticks=row['exposure_ticks'],selection_rule='first/last original-suite-passing checkpoint per completed native/refine history; paired rule; frozen before enlarged scoring; identical parameter arrays deduplicated')
                    jobs.append((str(root),label,kw,'uart_n',seed,record))
    write_json(manifest,jobs);write_json(root/f'{label}_sources.json',sources);snapshot=root/'batch_sources'/label;snapshot.mkdir(parents=True)
    for p in source_files():
        q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(audit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
    for source in sources:
        assert digest(source['block'])==source['block_sha256'];old=json.loads(__import__('pathlib').Path(source['block']).read_text());options=[old]+[r for r in rows if (r['shape'],r['profile'],r['seed'])==(source['shape'],source['profile'],source['seed'])];best=max(options,key=lambda r:key(r['selected']))
        result={**best,'recipe':label,'alternatives':[dict(checkpoint=r['checkpoint'],exact=r['selected']['exact_messages'],boundaries=r['selected']['boundary_errors']) for r in options], 'selection_source':source}
        folder=root/'models'/label/source['shape']/source['profile']/str(source['seed']);folder.mkdir(parents=True,exist_ok=True);write_json(folder/'block_0000.json',result)
