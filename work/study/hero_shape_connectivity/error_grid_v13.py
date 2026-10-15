"""Balanced independent invalid-byte/recovery training, preserving continuous state."""
import itertools,json
import numpy as np
from .run import ROOT,digest
from .vendor.data import Builder
from .data import conditions,save
from .shapes import features
from .startup_audit import mismatches
from .train import write_json


def schedule():
    entries=list(itertools.product(range(256),('framing','break','parity'),range(7)))
    order=np.random.default_rng(401000000).permutation(len(entries))
    return [entries[int(i)] for i in order]


def case(index):
    entries=schedule()[8*index:8*(index+1)];assert len(entries)==8
    seed=402000000+index*100;b=Builder('uart_e',seed)
    for j,(value,error,condition) in enumerate(entries):
        b.message([value],invalid=error)
        b.message(b.rng.integers(0,256,4).tolist(),conditions('uart_e')[condition])
        if j==3:b.idle(4096)
    s=b.finish();s['x']=features(s['lines'])[0];s['seed']=seed
    s['coverage_entries']=[dict(invalid_byte=v,error=e,recovery_condition=conditions('uart_e')[c]) for v,e,c in entries]
    assert sum(g['valid'] for g in s['groups'])==8 and not mismatches(s)
    return s


def generate(root):
    folder=root/'data_error_grid_v13/uart_e';folder.mkdir(parents=True,exist_ok=True);paths=[]
    for i in range(672):
        base=folder/f'balanced_{i:04d}'
        if not base.with_suffix('.json').exists():save(base,case(i))
        path=base.with_suffix('.json');paths.append(dict(path=str(path),metadata_sha256=digest(path),arrays_sha256=digest(base.with_suffix('.npz'))))
    assert len(schedule())==len(set(schedule()))==5376
    old=json.loads((root/'closure_v6_uart_e_pool.json').read_text())
    pool=dict(profile='uart_e',families=[401000000,402000000],existing_pool_sha256=digest(root/'closure_v6_uart_e_pool.json'),
        coverage='all256 invalid bytes x framing/break/parity x7 recovery timings;8 invalid/valid pairs per continuous stream; long idle after fourth pair',
        paths=old['paths']+paths)
    target=root/'error_grid_v13_uart_e_pool.json'
    if target.exists():assert json.loads(target.read_text())==pool
    else:write_json(target,pool)
    print('Verified independent recovery training pool',len(pool['paths']),'files',flush=True)

if __name__=='__main__':generate(ROOT/'runs/connectivity01')
