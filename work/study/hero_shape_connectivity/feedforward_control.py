"""Supplement a frozen replay by deleting every learned cycle edge, not leak carry."""
import argparse,importlib,json,sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from .run import ROOT,digest
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
    out=ROOT/'runs'/'connectivity01'/'confirmations'/a.label;frozen=json.loads((out/'freeze.json').read_text())
    sys.path.insert(0,str(out));confirm=importlib.import_module('source.confirm');shapes=importlib.import_module('source.shapes')
    jobs=[];records=[]
    for entry in frozen['entries']:
        if entry['seed']!=11:continue
        sh=shapes.make_shape(**entry['construction']);groups={n:g for g,ns in enumerate(sh.groups) for n in ns}
        model=dict(np.load(out/entry['weight_path']));p=model['p'].copy()
        indices=[k for k,(s,d) in enumerate(zip(sh.src,sh.dst)) if s>=0 and groups[int(s)]>=groups[int(d)]]
        p[indices]=0;folder=out/'controls'/'feedforward_weights'/entry['profile'];folder.mkdir(parents=True,exist_ok=True)
        path=folder/'11.npz'
        if path.exists():
            z=np.load(path);assert np.array_equal(z['p'],p) and np.array_equal(z['leaks'],model['leaks'])
        else:np.savez_compressed(path,p=p,leaks=model['leaks'])
        e={**entry,'weight_path':str(path.relative_to(out)),'weight_sha256':digest(path)}
        jobs.append((str(out),e,'feedforward_control'))
        records.append(dict(profile=entry['profile'],seed=11,source_weight_sha256=entry['weight_sha256'],control_weight_path=e['weight_path'],control_sha256=e['weight_sha256'],zeroed_indices=indices))
    write_json(out/'controls'/'feedforward_manifest.json',dict(entries=records,
        definition='zero every within-layer and backward-layer learned edge; retain forward routes, per-node leak carry, generic capped-age features and pulse register',
        limitation='post-fit intervention, not a retrained cheaper architecture; remaining leak/route/feature memory means this is not a memoryless receiver',
        comparison='original no_recurrence replay removes intra-layer edges only; this also removes return paths',
        inference_source_hashes=frozen['source_hashes']))
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for result in pool.map(confirm.evaluate_job,jobs):print(result['profile'],result['pass_all'],flush=True)
