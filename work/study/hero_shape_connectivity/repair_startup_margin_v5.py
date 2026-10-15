"""Resume the E131 serialization failure without changing its training recipe."""
import json,shutil
from .run import ROOT,digest
from .train import write_json
from .startup_margin_v5 import fit

if __name__=='__main__':
    root=ROOT/'runs/connectivity01';label='startup_margin_v5_32_repair1';original='startup_margin_v5_32'
    jobs=[j for j in json.loads((root/f'{original}_jobs.json').read_text()) if j[2]=='uart_e' and j[3]==131];assert len(jobs)==1
    before=root/'batch_sources'/original/'startup_margin_v5.py'
    repair=dict(original_batch=original,original_source_sha256=digest(before),repaired_source_sha256=digest(ROOT/'startup_margin_v5.py'),
        failure="numpy.savez_compressed got multiple values for keyword argument support_x",scope='merge inherited support arrays and current arrays into one dictionary; no data, model, objective, optimizer, budget or selection change',
        original_log_sha256=digest(root/f'{original}.log'),original_snapshot_preserved=True)
    write_json(root/f'{label}_repair.json',repair);write_json(root/f'{label}_jobs.json',jobs)
    snapshot=root/'batch_sources'/label
    if not snapshot.exists():
        snapshot.mkdir(parents=True)
        for p in ROOT.rglob('*'):
            if p.is_file() and 'runs' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts:
                q=snapshot/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        write_json(root/f'{label}_source_hashes.json',{str(p.relative_to(snapshot)):digest(p) for p in snapshot.rglob('*') if p.is_file()})
    rows=[fit(j) for j in jobs];write_json(root/f'{label}_ledger.json',dict(completed=rows,total=len(jobs),repair=repair))
