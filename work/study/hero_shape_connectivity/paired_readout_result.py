"""Apply the preregistered resource/recovery threshold to frozen paired outcomes."""
import argparse,json
import numpy as np
from .run import ROOT
from .shapes import PROFILES,SEEDS
from .train import write_json


def report(label):
    root=ROOT/'runs/connectivity01';folder=root/'confirmations'/label
    joint=json.loads((folder/'joint_qualification.json').read_text())
    topology=json.loads((folder/'topologies.json').read_text())
    dense=next(n for n in topology if n.endswith('readout16_dense'))
    reduced=next(n for n in topology if n.endswith('readout16_fanin32_fast'))
    costs=[topology[n]['configuration']['resources'] for n in (dense,reduced)]
    mac=1-costs[1]['macs_per_tick']/costs[0]['macs_per_tick'];parameters=1-costs[1]['parameters']/costs[0]['parameters']
    rows=[];replication=[];rng=np.random.default_rng(190731)
    for scope in ('fresh','regression'):
        base=folder if scope=='fresh' else folder/'regression'
        ledger=json.loads((base/'ledger.json').read_text());assert len(ledger['completed'])==ledger['total']
        for arithmetic in ('float','quantized'):
            for profile in PROFILES:
                for seed in SEEDS:
                    a=next(r for r in ledger['completed'] if (r['shape'],r['profile'],r['seed'],r['arithmetic'])==(dense,profile,seed,arithmetic))
                    b=next(r for r in ledger['completed'] if (r['shape'],r['profile'],r['seed'],r['arithmetic'])==(reduced,profile,seed,arithmetic))
                    other={c['condition']:c for c in b['conditions']};subset=[]
                    for c in a['conditions']:
                        d=other.pop(c['condition']);assert c['valid_messages']==d['valid_messages']
                        paths=[base/'results'/n/profile/f'{arithmetic}_{seed}'/(c['condition']+'.json') for n in (dense,reduced)]
                        raw=[json.loads(p.read_text()) for p in paths];outcomes=[np.asarray(r['message_outcomes']) for r in raw]
                        assert len(outcomes[0])==len(outcomes[1])==c['valid_messages']
                        assert int(outcomes[0].sum())==c['exact_messages'] and int(outcomes[1].sum())==d['exact_messages'],'paired outcomes disagree with complete-message scorer'
                        delta=outcomes[1]-outcomes[0];n=len(delta)
                        difference=float(delta.mean()) if n else 0.;ci=[0.,0.]
                        if n:
                            probability=np.bincount(delta+1,minlength=3)/n
                            counts=rng.multinomial(n,probability,size=5000)
                            ci=np.quantile((counts[:,2]-counts[:,0])/n,[.025,.975]).tolist()
                        recovery=(not n) or (min(c['exact_messages'],d['exact_messages'])/n>=.95 and abs(difference)<=.01)
                        boundary=d['boundary_errors']-c['boundary_errors'];invalid=d['invalid_accepted']-c['invalid_accepted'];background=d['background_accepted']-c['background_accepted']
                        row=dict(scope=scope,arithmetic=arithmetic,profile=profile,seed=seed,condition=c['condition'],messages=n,
                                 baseline_exact=c['exact_messages'],reduced_exact=d['exact_messages'],paired_accuracy_difference=difference,
                                 paired_bootstrap95=ci,boundary_difference=boundary,invalid_difference=invalid,background_difference=background,
                                 comparable=recovery and boundary<=0 and invalid<=0 and background<=0)
                        rows.append(row);subset.append(row)
                    assert not other
                    replication.append(dict(scope=scope,arithmetic=arithmetic,profile=profile,seed=seed,conditions=len(subset),
                                            all_comparable=all(r['comparable'] for r in subset)))
    summary={}
    for arithmetic in ('float','quantized'):
        counts={p:sum(all(r['all_comparable'] for r in replication if (r['arithmetic'],r['profile'],r['seed'])==(arithmetic,p,s)) for s in SEEDS) for p in PROFILES}
        qualified={n:joint['per_shape'][n+'/'+arithmetic]['qualified'] for n in (dense,reduced)}
        summary[arithmetic]=dict(paired_seeds_passing_fresh_and_regression=counts,resource_recovery_threshold_met=mac>=.15 and parameters>=.15 and all(n>=5 for n in counts.values()),full_qualification=qualified)
    result=dict(confirmation=label,mac_reduction=mac,parameter_reduction=parameters,summary=summary,per_seed=replication,per_condition=rows,
        uncertainty='5000 paired message-outcome bootstrap draws per condition. Exact-zero empirical intervals when both models recover every message do not imply zero population error. Seeds reuse the same test waveforms; messages/bits are not pooled across model seeds as independent observations.')
    write_json(root/f'{label}_paired_cost_result.json',result);write_json(root/'paired_readout_cost_result.json',result)
    lines=['# Paired full-profile readout cost result','',
           f"Float resource/recovery threshold: **{'met' if summary['float']['resource_recovery_threshold_met'] else 'NOT met'}**. The reduced graph removes 256 physical connections, saving {100*mac:.2f}% of MACs and {100*parameters:.2f}% of learned parameters.",'',
           f"Both architectures and all 84 protocol/seed configurations were frozen before fresh family {json.loads((folder/'freeze.json').read_text())['seed_family']} (`{label}`). Every seed is compared on identical waveforms. Previously observed suites are separately scored regressions. The same paired seeds must meet the comparison in both scopes; no failed seed is replaced.",'',
           '| Arithmetic | UART 8N1 | UART 8E1 | I2C | SPI0 | SPI1 | SPI2 | SPI3 | Threshold |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for arithmetic,s in summary.items():
        lines.append(f'| {arithmetic} | '+' | '.join(f"{s['paired_seeds_passing_fresh_and_regression'][p]}/6" for p in PROFILES)+f" | {'met' if s['resource_recovery_threshold_met'] else 'not met'} |")
    lines+=['','Comparison gates are unchanged: within one percentage point on every condition, at least 95% recovery, no worse boundary/rejection counts, and at least 15% lower MACs and parameters in at least five paired seeds. Full hero qualification is stricter and reported separately in QUALIFIED_SHAPES.md.','',
            'All per-message paired outcomes, per-condition differences and empirical 95% bootstrap intervals are retained in [paired_readout_cost_result.json](runs/connectivity01/paired_readout_cost_result.json). A zero-width empirical interval for all-success outcomes does not establish zero population failure probability. Results cover the declared generated distributions, not all possible waveforms.','',
            'The two shapes share the learned 48-state recurrent backbone within each seed/profile. The reduced head receives the same training waveforms and representative state bank, with the same conditional continuation rule as the intact control. Their recorded optimization exposure differs; this establishes a reproducible pruning/transfer result, not a from-scratch training-efficiency ranking. READOUT_ROUTING_COMPARISON.md retains all intermediate failures and curves.','',
            'Including common leak blends gives 16.41% fewer modeled multiplies; the numeric storage subtotal falls 4.43%. The common feature extraction, event interface, assembler, activation table and scheduling costs are unchanged. No routed silicon area or frequency is measured.']
    (ROOT/'PAIRED_READOUT_RESULT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--label',default='readout_cost_full_v3a');args=ap.parse_args();report(args.label)
