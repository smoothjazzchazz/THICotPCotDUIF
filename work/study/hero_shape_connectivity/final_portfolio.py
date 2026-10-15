"""Freeze a same-seed development-only selection before fresh confirmation."""
import argparse,json
from pathlib import Path
from .run import ROOT,digest
from .shapes import make_shape,SEEDS,PROFILES
from .train import key,write_json


def prepare(root,candidates,recipe):
    chosen=[];counts={}
    for kw in candidates:
        sh=make_shape(**kw)
        for profile in PROFILES:
            passed=0
            for seed in SEEDS:
                options=[]
                for path in sorted((root/'models').glob(f'*/{sh.name}/{profile}/{seed}/block_*.json')):
                    b=json.loads(path.read_text())
                    if b['recipe'].startswith('final_portfolio_'):continue
                    if profile.startswith('uart') and b.get('development_distribution')!='precision_v2':continue
                    options.append((path,b))
                if not options:raise ValueError(('missing trained seed',sh.name,profile,seed))
                path,b=max(options,key=lambda item:key(item[1]['selected']));s=b['selected']
                passed+=s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
                record=dict(source_block=str(path),source_block_sha256=digest(path),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
                    source_provenance=b.get('warm_start'),selection='unchanged development key, same physical graph/profile/seed; completed verified-v2 UART blocks only',
                    alternatives=[dict(block=str(p),block_sha256=digest(p),checkpoint=r['checkpoint'],recipe=r['recipe'],epochs=r['epochs'],exposure_ticks=r['exposure_ticks']) for p,r in options])
                chosen.append((kw,sh.name,profile,seed,b,record))
            counts[f'{sh.name}/{profile}']=passed
    if any(v<5 for v in counts.values()):raise ValueError(('not ready for finalist confirmation',counts))
    # Complete preflight before writing the concrete selection.
    for kw,name,profile,seed,b,record in chosen:
        folder=root/'models'/recipe/name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
        result={**b,'recipe':recipe,'epochs':0,'selected_epoch':0,'exposure_ticks':0,'warm_start':record,
            'status':'development_selection_only_not_confirmation','source_training_exposure_ticks':b['exposure_ticks']}
        path=folder/'block_0000.json'
        if path.exists():
            if json.loads(path.read_text())!=result:raise ValueError('selection already frozen; choose a new recipe label')
        else:write_json(path,result)
    write_json(root/f'{recipe}_selection.json',dict(recipe=recipe,development_passes=counts,
        note='development preflight only; original fresh confirmation gates remain mandatory',
        selected=[dict(shape=name,profile=profile,seed=seed,**record) for kw,name,profile,seed,b,record in chosen]))
    print(json.dumps(counts),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,required=True);ap.add_argument('--recipe',required=True);a=ap.parse_args()
    if not a.recipe.startswith('final_portfolio_'):raise ValueError('selection recipe must be separately named final_portfolio_*')
    prepare(ROOT/'runs'/'connectivity01',json.loads(a.candidates.read_text()),a.recipe)
