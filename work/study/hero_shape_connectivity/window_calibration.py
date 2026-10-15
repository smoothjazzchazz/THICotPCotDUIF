"""Apply the preregistered training-only margin rule to final window-rescue states."""
import json,shutil
from concurrent.futures import ProcessPoolExecutor,as_completed
from .run import ROOT,digest
from .shapes import make_shape
from .train import write_json
from .margin_calibrate import fit

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];sh=make_shape(**kw);label='window_calibration_v4';jobs=[];pending=[]
    for seed in (71,131):
        for window in (512,1024):
            folder=root/'models'/f'phase_window{window}_v4'/sh.name/'uart_e'/str(seed)
            if not (folder/'block_0120.json').exists():pending.append(str(folder))
    if pending:raise ValueError(('paired window comparison must finish first',pending))
    sources=root/'diagnostics'/'window_calibration_sources';sources.mkdir(exist_ok=True)
    for seed in (71,131):
        for window in (512,1024):
            folder=root/'models'/f'phase_window{window}_v4'/sh.name/'uart_e'/str(seed);block=folder/'block_0120.json';b=json.loads(block.read_text())
            rows=[json.loads(l) for l in (folder/'history.jsonl').read_text().splitlines()];last=next(r for r in rows if r['epoch']==120)
            proposal={**b,'selected_epoch':120,'selected':last,'checkpoint':str(folder/'epoch_0120.npz'),
                'original_best_block':str(block),'original_best_block_sha256':digest(block),
                'proposal_policy':'final completed 120-round checkpoint, fixed before scalar calibration; not the development-selected best'}
            path=sources/f'window{window}_e{seed}.json'
            if path.exists():
                if json.loads(path.read_text())!=proposal:raise ValueError('declared final proposal changed')
            else:write_json(path,proposal)
            jobs.append((str(root),kw,'uart_e',seed,dict(recipe=f'phase_window{window}_calibration_v4',source_block=str(path))))
    write_json(root/f'{label}_jobs.json',jobs);snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    results=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(fit,j) for j in jobs]):results.append(f.result());write_json(root/f'{label}_ledger.json',dict(completed=results,total=len(jobs)))
