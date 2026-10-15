"""Development-only finalist selection with every expanded UART condition."""
import argparse,json
from pathlib import Path
from .run import ROOT,digest
from .shapes import make_shape,SEEDS,PROFILES
from .train import key,write_json


def prepare(root,candidates,recipe):
    if not recipe.startswith('final_portfolio_v3_'):raise ValueError('use a new final_portfolio_v3_* label')
    selected=[];counts={}
    for kw in candidates:
        sh=make_shape(**kw)
        for profile in PROFILES:
            passed=0
            for seed in SEEDS:
                options=[]
                for path in sorted((root/'models').glob(f'*/{sh.name}/{profile}/{seed}/block_*.json')):
                    b=json.loads(path.read_text())
                    if b['recipe'].startswith('final_portfolio_'):continue
                    if profile.startswith('uart') and b.get('development_distribution')!='precision_v2_plus_corners_v4_plus_startup_v5':continue
                    options.append((path,b))
                if not options:raise ValueError(('missing common-development seed',sh.name,profile,seed))
                path,b=max(options,key=lambda pair:key(pair[1]['selected']));score=b['selected']
                passed+=score['message_accuracy']==1 and not any(score[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
                record=dict(source_block=str(path),source_block_sha256=digest(path),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
                    source_provenance=b.get('warm_start'),selection='same graph/profile/seed; all8864 UART development groups; unchanged complete-message key; no confirmation selection',
                    alternatives=[dict(block=str(p),block_sha256=digest(p),checkpoint=r['checkpoint'],recipe=r['recipe'],epochs=r['epochs'],exposure_ticks=r['exposure_ticks']) for p,r in options])
                selected.append((sh.name,profile,seed,b,record))
            counts[f'{sh.name}/{profile}']=passed
    if any(v<5 for v in counts.values()):raise ValueError(('not ready for fresh confirmation',counts))
    for name,profile,seed,b,record in selected:
        folder=root/'models'/recipe/name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
        result={**b,'recipe':recipe,'epochs':0,'selected_epoch':0,'exposure_ticks':0,'warm_start':record,
            'status':'expanded_development_selection_only_not_confirmation','source_training_exposure_ticks':b['exposure_ticks']}
        path=folder/'block_0000.json'
        if path.exists():assert json.loads(path.read_text())==result,'frozen selection changed; choose a new label'
        else:write_json(path,result)
    write_json(root/f'{recipe}_selection.json',dict(recipe=recipe,development_passes=counts,
        selected=[dict(shape=n,profile=p,seed=s,**r) for n,p,s,b,r in selected],
        next_gate='freeze topology/weights; generate unused fresh v3 suite; require fresh and previous-v2 regression jointly'))
    print(json.dumps(counts),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,required=True);ap.add_argument('--recipe',required=True);a=ap.parse_args()
    prepare(ROOT/'runs/connectivity01',json.loads(a.candidates.read_text()),a.recipe)
