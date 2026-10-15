"""Replace one failed-training source only after complete independent training closure."""
import json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,PROFILES,SEEDS
from .train import write_json
from .startup_margin_v5 import passed


def prepare():
    root=ROOT/'runs/connectivity01';kw=json.loads((ROOT/'mixed_first_gated_candidate.json').read_text())[0];sh=make_shape(**kw)
    recipe='final_portfolio_v3_first_gate_b';old=root/'models/final_portfolio_v3_first_gate_a';repaired=root/'models/phase_gated_linear_v13'/sh.name/'uart_e/131/block_0016.json'
    repair=json.loads(repaired.read_text())
    assert passed(repair['selected']) and repair['selected']['full_pool_verified']
    assert repair['selected_full_training_canonical_errors']==0 and repair['selected_startup_failed_cases']==0
    assert repair['scalar_replay_verified'];selected=[];counts={}
    for profile in PROFILES:
        counts[profile]=0
        for seed in SEEDS:
            source=repaired if (profile,seed)==('uart_e',131) else old/sh.name/profile/str(seed)/'block_0000.json'
            b=json.loads(source.read_text());assert b['construction']==kw
            assert b.get('development_distribution')=='precision_v2_plus_corners_v4_plus_startup_v5' or not profile.startswith('uart')
            weights=np.load(b['checkpoint']);assert np.isfinite(weights['p']).all()
            provenance=dict(source_block=str(source),source_block_sha256=digest(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
                selection='retain all previous development-selected sources except parity131: require complete1296-file independent training closure plus all8864developmentgroups and scalar replay; no confirmation examples used for fitting or checkpoint selection',
                source_training_exposure_ticks=b['exposure_ticks'],source_selected_epoch=b['selected_epoch'])
            row={**b,'recipe':recipe,'epochs':0,'selected_epoch':0,'exposure_ticks':0,'warm_start':provenance,
                 'status':'training_closure_and_expanded_development_selection_only','source_training_exposure_ticks':b['exposure_ticks']}
            folder=root/'models'/recipe/sh.name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True);target=folder/'block_0000.json'
            if target.exists():assert json.loads(target.read_text())==row
            else:write_json(target,row)
            counts[profile]+=passed(b['selected']);selected.append(dict(profile=profile,seed=seed,**provenance))
    assert min(counts.values())>=5
    write_json(root/f'{recipe}_selection.json',dict(recipe=recipe,development_passes=counts,selected=selected,
        required_regressions=['full_shape_v2a','first_gate_full_v3a'],next_gate='freeze before unused fresh family521000000; same>=5/6seeds perprofile mustpass everyfresh and bothregression suites;float/Q3.12 separate'))
    print(json.dumps(counts),flush=True)

if __name__=='__main__':prepare()
