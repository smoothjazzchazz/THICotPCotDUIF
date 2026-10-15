"""Apply the same independently declared coverage recipe to unresolved parity101."""
import json,shutil
from .run import ROOT,digest,source_files
from .shapes import make_shape
from .train import write_json
from .gated_linear_v13 import fit

if __name__=='__main__':
    root=ROOT/'runs/connectivity01';label='gated_linear_v13_e101_16';manifest=root/f'{label}_jobs.json'
    if manifest.exists():raise ValueError('resume original batch')
    kw=json.loads((ROOT/'mixed_first_gated_candidate.json').read_text())[0];sh=make_shape(**kw);seed=101
    block=root/'models/final_portfolio_v3_first_gate_a'/sh.name/'uart_e'/str(seed)/'block_0000.json';b=json.loads(block.read_text())
    cache=root/'models/phase_gated_margin_v11'/sh.name/'uart_e'/str(seed);constraints=cache/'epoch_0016.npz'
    source=dict(block=str(block),block_sha256=digest(block),checkpoint_sha256=digest(b['checkpoint']),
        policy='same original development-selected unresolved parity101 source, same v13 independent1296-file pool and minimum-change objective; started before revised B confirmation results, frozen B unchanged',
        state_cache=str(cache/'training_states'),development_cache=str(cache/'development_states'),constraints=str(constraints),constraints_sha256=digest(constraints))
    jobs=[(str(root),kw,'uart_e',seed,16,source)];write_json(manifest,jobs);snapshot=root/'batch_sources'/label;snapshot.mkdir(parents=True)
    for p in source_files():
        target=snapshot/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    row=fit(jobs[0]);write_json(root/f'{label}_ledger.json',dict(completed=[row],total=1))
