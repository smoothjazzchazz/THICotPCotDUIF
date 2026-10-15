"""Freeze-ready development selection after the paired clocked-pause intervention."""
import json
from .run import ROOT,digest
from .shapes import make_shape,PROFILES,SEEDS
from .train import write_json
from .startup_margin_v5 import passed


def prepare():
    root=ROOT/'runs/connectivity01';recipe='final_portfolio_v3_readout_cost_b';counts={};selected=[]
    for kw in json.loads((ROOT/'readout_cost_pair_v3_candidates.json').read_text()):
        name=make_shape(**kw).name
        for profile in PROFILES:
            count=0
            for seed in SEEDS:
                revised=profile in ('spi1','spi2');source=root/'models'/('phase_clocked_pause_v20' if revised else 'final_portfolio_v3_readout_cost_a')/name/profile/str(seed)/('block_0012.json' if revised else 'block_0000.json')
                b=json.loads(source.read_text());good=passed(b['selected'])
                if revised:
                    assert b['development_distribution']=='original_plus_clocked_pause_v20'
                    good=good and b['full_training_closure'] and b['selected_training_scan']['canonical_errors']==0
                count+=good
                provenance=dict(source_block=str(source),source_block_sha256=digest(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),
                    rule='SPI1/2 use same-seed complete independent pause-pool/development intervention; other profiles retain pre-A selected weights exactly; no confirmation selection',
                    training_closure_required=revised,previous_selection='final_portfolio_v3_readout_cost_a')
                selected.append((name,profile,seed,b,provenance))
            counts[f'{name}/{profile}']=count
    assert all(n>=5 for n in counts.values()),('not ready for new confirmation',counts)
    for name,profile,seed,b,provenance in selected:
        folder=root/'models'/recipe/name/profile/str(seed);folder.mkdir(parents=True,exist_ok=True)
        record={**b,'recipe':recipe,'epochs':0,'selected_epoch':0,'exposure_ticks':0,'source_training_exposure_ticks':b['exposure_ticks'],
                'warm_start':provenance,'status':'independent_pause_development_selection_only_not_confirmation'}
        file=folder/'block_0000.json'
        if file.exists():assert json.loads(file.read_text())==record
        else:write_json(file,record)
    write_json(root/f'{recipe}_selection.json',dict(recipe=recipe,development_passes=counts,selected=[dict(shape=n,profile=p,seed=s,**v) for n,p,s,b,v in selected],
        next_gate='new immutable freeze and unused fresh family; regress full_shape_v2a, dense_full_v3a and readout_cost_full_v3a'))
    print(json.dumps(counts),flush=True)


if __name__=='__main__':prepare()
