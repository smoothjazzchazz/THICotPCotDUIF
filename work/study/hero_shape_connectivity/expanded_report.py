"""A compact current ledger that never mixes old and expanded development."""
import datetime,json
from .run import ROOT,digest
from .shapes import make_shape,SEEDS,cost
from .train import key,write_json


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';records=[];confirmed=set();confirmation_status=[]
    for folder in sorted((root/'confirmations').iterdir()):
        policy=folder/'startup_semantics.json'
        if not policy.exists() or json.loads(policy.read_text()).get('version')!=3:continue
        result=folder/'joint_qualification.json'
        if result.exists():
            scores=json.loads(result.read_text())['per_shape']
            for name,row in scores.items():
                if name.endswith('/float') and row['qualified']:
                    topology=json.loads((folder/'topologies.json').read_text());confirmed.add(topology[name.rsplit('/',1)[0]]['physical_sha256'])
            confirmation_status.append(f"`{folder.name}` completed fresh/regression scoring; see its frozen joint qualification record.")
        else:confirmation_status.append(f"`{folder.name}` is frozen and undergoing independent fresh confirmation plus separate prior-failure regression.")
    lines=['# Current findings','',
        f'**Full multi-protocol physical shapes independently qualified: {len(confirmed)}. '+('The required two are established.' if len(confirmed)>=2 else 'Research continues.')+'**', '',
        'Start with [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md) for the frozen full-profile gates, demonstration weights and remaining seed failures. The readout-routing comparison and its costs are in [READOUT_ROUTING_COMPARISON.md](READOUT_ROUTING_COMPARISON.md).', '',
        'A narrower physical result is independently confirmed: the64-node24→20→20 sparse→ring→ring graph with one aligned inter-layer route per node matches the sparse baseline on I2C and all SPI modes, across six seeds in float andQ3.12, while saving23.62% MACs and22.10% parameters. UART is absent from that confirmation. See [REPORT.md](REPORT.md) for frozen evidence and resource limits.', '',
        'These UART candidates are exploratory checkpoint portfolios. All rows use the same enlarged8,864-group development suite. Different training recipes/exposures mean this is not a matched topology ranking or fresh proof. Pending replication seeds are marked explicitly.', '',
        '| Candidate | Nonlinear units / stored states | MACs / parameters | Profile | Full development passes | Remaining seeds |',
        '| --- | ---: | ---: | --- | ---: | --- |']
    candidates=[('Sparse24 → ring16 → ring24, registered returns',json.loads((ROOT/'wider_both2_candidate.json').read_text())[0]),('Sparse16 → ring16 → ring16 +16 nonlinear readout units',json.loads((ROOT/'readout_dense_candidate.json').read_text())[0])]
    candidates.extend(zip(['Plain48 control, first leak0.5','First-layer-gated64 (48 states +16 gates)'],json.loads((ROOT/'mixed_first_candidates.json').read_text())))
    candidates.append(('Sparse16 + two ring16 branches + reduced16-unit readout',json.loads((ROOT/'readout_pruned32_fast_candidate.json').read_text())[0]))
    for title,kw in candidates:
        sh=make_shape(**kw);c=cost(sh)
        for profile in ('uart_n','uart_e'):
            count=0;failed=[]
            for seed in SEEDS:
                options=[]
                for path in (root/'models').glob(f'*/{sh.name}/{profile}/{seed}/block_*.json'):
                    b=json.loads(path.read_text())
                    if b.get('development_distribution')=='precision_v2_plus_corners_v4_plus_startup_v5' and not b['recipe'].startswith('final_portfolio_'):options.append((path,b))
                if not options:failed.append(str(seed)+' (pending)');continue
                path,b=max(options,key=lambda pair:key(pair[1]['selected']));s=b['selected'];ok=s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
                count+=ok
                if not ok:failed.append(str(seed))
                records.append(dict(shape=sh.name,profile=profile,seed=seed,pass_development=ok,block=str(path),block_sha256=digest(path),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),selected=s,source_training_exposure_ticks=b.get('source_training_exposure_ticks',b['exposure_ticks'])))
            lines.append(f"| {title} | {c['nodes']} / {c['stored_states']} | {c['macs_per_tick']} / {c['parameters']} | {profile} | {count}/6 | {', '.join(failed) or 'none'} |")
    lines+=['', 'The primary graph already failed a properly audited fresh confirmation: only3/6 no-parity and1/6 parity seeds passed. That failure remains frozen. V3 adds independent startup cases and requires the same five seeds to pass both new fresh tests and the old failure corpus.', '',*confirmation_status,'',
        'Structural comparisons show that true rings can replace sparse layers for clocked reception at lower cost; registered routing and access to earlier layers matter at tight setup. UART also needs reliable internal phase and recovery. Frozen-state, extra-idle and layer-state interventions expose cold-state dependence in some seeds; changing output weights alone does not consistently repair it.', '',
        'Matched cold-prefix training fixes one primary no-parity seed through state changes, while its parity counterpart worsens. Small trust-region output fitting closes four full training/development configurations, but other sources fail larger independent-start training pools. Broader linear fitting can repair selected failure states and simultaneously destroy ordinary traffic; all such failed iterates are retained. These are learned-state/recipe diagnostics, not physical-capacity proofs.', '',
        'The completed allocation comparison trades eight slow-ring states for eight conditional first-layer gates:64-state primary versus its56-state subgraph versus56states+8gates. All18 declared native/refinement fits completed; only one plain56 no-parity fit passes whole development. It did not establish the replicated meaningful threshold. GATE_ALLOCATION_COMPARISON.md retains the curves and failures.', '',
        'The later readout comparison keeps the learned48-state backbone fixed and removes256 actual hidden-input edges. Retaining every fast-ring parent works better in the tested projection than retaining every first-layer parent at the same edge count. Paired conditional supervised fitting and balanced startup coverage are recorded separately; this is transfer/pruning evidence, not an equal-iteration or from-scratch efficiency claim.', '',
        'See [STARTUP_REFINEMENT.md](STARTUP_REFINEMENT.md) for causal traces and paired curves, [LABEL_DIAGNOSTIC.md](LABEL_DIAGNOSTIC.md) for the raw-class versus event-pulse finding, [COVERAGE_V10.md](COVERAGE_V10.md) for balanced cold-start training, [REPRODUCE.md](REPRODUCE.md) for commands, and `runs/connectivity01/ACTIVE.md` for resumable work. Costs are modeled operations/storage, not silicon area or timing; clock_hz remains0.']
    write_json(root/'expanded_development_portfolios.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),distribution='precision_v2_plus_corners_v4_plus_startup_v5',selection='exploratory completed-block selection; no confirmation scores',records=records))
    (ROOT/'CURRENT_FINDINGS.md').write_text('\n'.join(lines).rstrip()+'\n')
