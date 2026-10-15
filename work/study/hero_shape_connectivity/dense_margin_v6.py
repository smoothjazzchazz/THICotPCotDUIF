"""Apply the completed fixed-state recipe to unresolved dense-readout candidates."""
import json,shutil
from concurrent.futures import ProcessPoolExecutor,as_completed
from .run import ROOT,digest
from .shapes import make_shape
from .startup_margin_v5 import fit
from .train import key,write_json


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';label='dense_margin_v6_32';kw=json.loads((ROOT/'readout_dense_candidate.json').read_text())[0];sh=make_shape(**kw);file=root/f'{label}_jobs.json'
    if file.exists():jobs=json.loads(file.read_text())
    else:
        jobs=[]
        for profile,seed in [('uart_n',131),('uart_e',101),('uart_e',131),('uart_n',47),('uart_e',47)]:
            options=[]
            for path in (root/'models').glob(f'*/{sh.name}/{profile}/{seed}/block_*.json'):
                b=json.loads(path.read_text())
                if b.get('development_distribution')=='precision_v2_plus_corners_v4_plus_startup_v5':options.append((path,b))
            source,b=max(options,key=lambda pair:key(pair[1]['selected']));record=dict(recipe='phase_dense_margin_v6',source_block=str(source),source_block_sha256=digest(source),checkpoint_sha256=digest(b['checkpoint']))
            jobs.append((str(root),kw,profile,seed,32,record))
        write_json(file,jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):rows.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs)))
