"""Measured evidence tables and literal connection diagrams for the ongoing study."""
import csv
import json
import os
from pathlib import Path
import numpy as np
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .shapes import make_shape,cost,SEEDS
from .train import write_json
from .run import ROOT


def diagram(sh,path,backbone_only=False):
    fig,ax=plt.subplots(figsize=(18 if len(sh.groups)>3 else 14,5));positions={};colors=['#315c9b','#008b72','#a66c00','#8b4aa5']
    for g,nodes in enumerate(sh.groups):
        angles=np.linspace(np.pi/2,np.pi/2+2*np.pi,len(nodes),endpoint=False)
        for i,a in zip(nodes,angles):positions[i]=np.array([g*3.7+np.cos(a),np.sin(a)])
        if getattr(sh,'nonlinear_readout',False) and g==3:
            for j,i in enumerate(nodes):positions[i]=np.array([g*3.7+(j%4-1.5)*.5,(j//4-1.5)*.5])
        label=f'Layer {g+1}: {len(nodes)} nodes'
        if getattr(sh,'mixed',False):label=f'Layer {g+1}: {len(nodes)} states'+(f' + {len(sh.gate_nodes)} gates' if nodes[0] in sh.gate_nodes else '')
        if getattr(sh,'nonlinear_readout',False) and g==3:label='16 nonlinear readout units'
        ax.text(g*3.7,1.43,label,ha='center',fontsize=13,color=colors[g])
    group={i:g for g,nodes in enumerate(sh.groups) for i in nodes}
    for s,d in zip(sh.src,sh.dst):
        if s<0:continue
        a,b=positions[int(s)],positions[int(d)];same=group[int(s)]==group[int(d)]
        if s==d:
            circle=plt.Circle(a+.03,.07,fill=False,color=colors[group[int(d)]],alpha=.35,lw=.6);ax.add_patch(circle)
        else:
            direction=b-a;length=np.linalg.norm(direction);u=direction/length
            returning=group[int(s)]>group[int(d)]
            ax.annotate('',xy=b-u*.065,xytext=a+u*.065,arrowprops=dict(arrowstyle='->',
                color=colors[group[int(d)]] if same else '#b34b56' if returning else '#515968',alpha=.7 if same else .28 if returning else .55,
                connectionstyle='arc3,rad=-0.08' if returning else 'arc3,rad=0',lw=.85 if same else .55,mutation_scale=7))
    for i,point in positions.items():
        ax.scatter(*point,s=33,color=colors[group[i]],zorder=3)
        ax.text(point[0]*0+point[0],point[1],str(i),color='white',ha='center',va='center',fontsize=4.5,zorder=4)
    if getattr(sh,'mixed',False):
        gate_positions={int(i):np.array([group[int(i)]*3.7,0.])+1.23*(positions[int(i)]-np.array([group[int(i)]*3.7,0.])) for i in sh.gate_nodes}
        for s,d in zip(sh.gate_src,sh.gate_dst):
            ax.annotate('',xy=gate_positions[int(d)],xytext=positions[int(s)],arrowprops=dict(arrowstyle='->',color='#8b4aa5',alpha=.2,linestyle='--',lw=.5,mutation_scale=5))
        for i,point in gate_positions.items():
            ax.scatter(*point,s=24,marker='s',color='#8b4aa5',zorder=4)
            ax.plot([point[0],positions[i][0]],[point[1],positions[i][1]],color='#8b4aa5',lw=.7)
    c=cost(sh)
    center=(len(sh.groups)-1)*3.7/2
    counts=f"{c['recurrent_edges']} recurrent + {c['inter_layer_edges']} inter-layer + {c['input_edges']} input"
    if not backbone_only:counts+=f" + {c['readout_edges']} readout"
    ax.text(center,-1.5,counts+' connections',ha='center',fontsize=11)
    caption=f"Nine generic inputs; six logits see all {c['stored_states']} stored states. Input/output edges counted above, omitted from drawing. Red: returns."
    if getattr(sh,'mixed',False):caption+=f' Purple squares/dashes: {len(sh.gate_nodes)} gates and their {len(sh.gate_src)} registered inputs.'
    if getattr(sh,'nonlinear_readout',False):caption+=' Purple grid: current-sample readout; logits also see these16 units.'
    if backbone_only:caption='Shared backbone only. Nine generic inputs enter nodes 0–15 (input edges omitted). All shown state routes are registered. Red: returns. Head and final outputs shown separately.'
    ax.text(center,-1.8,caption,ha='center',fontsize=8)
    title='Shared 48-state backbone: 16 sparse nodes and two actual directed 16-node rings' if backbone_only else sh.name
    ax.set_title(title+'\nArrows show actual directed connections; circles are illustrations, not a chip layout.',fontsize=13,pad=22)
    ax.set_xlim(-1.5,(len(sh.groups)-1)*3.7+1.6);ax.set_ylim(-2.1,1.6);ax.set_aspect('equal');ax.axis('off');fig.tight_layout()
    fig.savefig(path,dpi=180,bbox_inches='tight');plt.close(fig)


def report(root):
    figures=root/'figures';figures.mkdir(exist_ok=True)
    candidates=json.loads((ROOT/'cost_candidates.json').read_text());shapes=[make_shape(**x) for x in candidates]
    for sh in shapes:diagram(sh,figures/f'{sh.name}.png')
    trial_rows=[];trial_conditions=[]
    for directory in sorted((root/'models').glob('*/*/*/*')):
        blocks=sorted(directory.glob('block_*.json'))
        if not blocks:continue
        trial=json.loads(blocks[-1].read_text());m=trial['selected']
        row={k:trial[k] for k in ('shape','profile','seed','recipe','epochs','selected_epoch','status','exposure_ticks')}
        row['development_distribution']=trial.get('development_distribution','original')
        row.update({k:m[k] for k in ('message_accuracy','boundary_errors','false_events','missed_events','invalid_accepted','background_accepted')})
        trial_rows.append(row)
        for c,score in m['conditions'].items():trial_conditions.append(dict(**row,condition=c,condition_messages=score['valid_messages'],condition_exact=score['exact_messages'],condition_accuracy=score['message_accuracy']))
    for name,table in [('training_trials.csv',trial_rows),('training_per_condition.csv',trial_conditions)]:
        if table:
            with (root/name).open('w') as f:
                w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    # Plot comparable canonical metrics; objectives with different losses are not overlaid.
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for code,color in [('sss','#315c9b'),('srr','#008b72'),('srs','#a66c00')]:
        for seed in (11,29,47):
            path=root/'models'/'matched'/f'{code}_registered_24-20-20'/'uart_n'/str(seed)/'history.jsonl'
            if not path.exists():continue
            h=[json.loads(l) for l in path.read_text().splitlines()];h=[r for r in h if 'dev_loss' in r]
            x=[r['epoch'] for r in h]
            axes[0].plot(x,[r['dev_loss'] for r in h],color=color,alpha=.6,label=code.upper() if seed==11 else None)
            axes[1].plot(x,np.maximum.accumulate([r['message_accuracy'] for r in h])*100,color=color,alpha=.6)
    axes[0].set_ylabel('Canonical development loss');axes[1].set_ylabel('Best exact complete messages (%)')
    for ax in axes:ax.set_xlabel('Training epoch');ax.grid(alpha=.2)
    axes[0].legend();fig.suptitle('UART 8N1: falling loss has not established reliable reception');fig.tight_layout()
    fig.savefig(figures/'uart_learning_curves.png',dpi=160);plt.close(fig)
    confirmation=root/'confirmations'/'clocked_cost02'
    rows=[json.loads(p.read_text()) for p in (confirmation/'results').glob('*/*/*/summary.json')]
    conditions=[]
    for row in rows:
        for c in row['conditions']:conditions.append(dict(shape=row['shape'],**c))
    if conditions:
        with (root/'per_condition.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for row in conditions for k in row)));writer.writeheader();writer.writerows(conditions)
    summaries=[]
    for sh in shapes:
        for profile in ('i2c','spi0','spi1','spi2','spi3'):
            counts={a:sum(r['pass_all'] for r in rows if r['shape']==sh.name and r['profile']==profile and r['arithmetic']==a) for a in ('float','quantized','no_recurrence')}
            summaries.append(dict(shape=sh.name,profile=profile,**counts))
    write_json(root/'confirmed_profile_counts.json',summaries)
    baseline,reduced=map(cost,shapes)
    write_json(root/'costs.json',{sh.name:cost(sh) for sh in shapes})
    # Paired outcomes are retained, including a non-inferential bootstrap of observed differences.
    pairs=[]
    for profile in ('i2c','spi0','spi1','spi2','spi3'):
        for seed in SEEDS:
            folder=confirmation/'results'/shapes[0].name/profile/f'float_{seed}'
            for path in folder.glob('*.json'):
                if path.name in ('summary.json','replay_audit.json'):continue
                other=confirmation/'results'/shapes[1].name/profile/f'float_{seed}'/path.name
                if not other.exists():continue
                a=json.loads(path.read_text());b=json.loads(other.read_text())
                delta=np.array(b['message_outcomes'])-np.array(a['message_outcomes'])
                pairs.append(dict(profile=profile,seed=seed,condition=a['condition'],messages=len(delta),
                    exact_difference=float(delta.mean()),boundary_difference=b['boundary_errors']-a['boundary_errors'],
                    invalid_difference=b['invalid_accepted']-a['invalid_accepted'],background_difference=b['background_accepted']-a['background_accepted']))
    write_json(root/'paired_clocked_comparison.json',dict(pairs=pairs,
        note='Zero observed differences do not imply zero population failure probability. Messages, not bits, are independent scoring units.',
        mac_reduction=1-reduced['macs_per_tick']/baseline['macs_per_tick'],parameter_reduction=1-reduced['parameters']/baseline['parameters']))
    qualification=root/'qualified_shapes_v3.json';qualified_count=json.loads(qualification.read_text())['physical_shape_count'] if qualification.exists() else 0
    lines=['# Physical-shape research and the clocked cost comparison','',
        f'**{qualified_count} complete multi-protocol shape(s) independently qualify.** See [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md) for current full-profile evidence. '+('The search for two continues.' if qualified_count<2 else 'Both required shapes have been confirmed.'),'',
        'A narrower architectural result is independently confirmed: at 64 nodes, replacing the two later sparse layers by true directed rings and reducing their incoming routes to one aligned edge per node preserves clocked reception while reducing modeled computation and learned parameters.','',
        '| Shape | Allocation | Recurrent / inter-layer edges | MACs/tick | Learned parameters |',
        '| --- | --- | ---: | ---: | ---: |']
    for sh in shapes:
        c=cost(sh);lines.append(f"| {sh.name} | 24 → 20 → 20 | {c['recurrent_edges']} / {c['inter_layer_edges']} | {c['macs_per_tick']} | {c['parameters']} |")
    lines+=['',f"The reduction is {100*(1-reduced['macs_per_tick']/baseline['macs_per_tick']):.2f}% in MACs and {100*(1-reduced['parameters']/baseline['parameters']):.2f}% in learned parameters. Both retain 216 input connections and 384 readout connections. Node state, leak operations, preprocessing, event assembly and scheduling are included separately in `runs/connectivity01/costs.json`. The shared 8,194-byte activation LUT and assembly storage do not shrink; these are not measured chip-area or frequency savings.",'',
        '## Fresh confirmation 02','',
        'Each valid timing condition has at least 1,000 complete messages, including all byte values, constant/alternating patterns, random payloads, and a 1,024-byte message where applicable. Gates include exact boundaries, malformed rejection, cold/midstream startup, long idle and recovery. Frozen weights preceded seed-family 191000000 generation. Float and Q3.12 integer replay are separate.','',
        '| Shape | Profile | Float pass / 6 | Integer pass / 6 | Post-fit no recurrence / 1 |','| --- | --- | ---: | ---: | ---: |']
    for r in summaries:lines.append(f"| {r['shape']} | {r['profile']} | {r['float']} | {r['quantized']} | {r['no_recurrence']} |")
    lines+=['','Complete condition counts are in [per_condition.csv](runs/connectivity01/per_condition.csv); every prediction tick and message outcome remains under `confirmations/clocked_cost02/results`. All six seeds are 11,29,47,71,101,131. UART is absent from this scoped confirmation, not counted as passed.','',
        'Confirmation 01 is preserved: all complete messages recovered, but cold-start false STOP events caused SPI1 boundary failures (SSS seeds 47/131; SRR-aligned1 seed11). Both shapes then received the same 60-epoch SPI1 exposure, fixed those development-visible errors, and were frozen again before independent confirmation 02. No startup grace or threshold relaxation was introduced.','',
        '## What the comparisons teach','',
        '- The five requested connectivity patterns and both inter-layer schedules reached exact clocked development message recovery after corrected training coverage. They did not produce a meaningful UART advance. All failures and improving runs are retained.',
        '- Sparse feedback was not required at every layer for clocked reception. Two actual closed rings with lighter inter-layer routing retain the tested behavior at lower operation/parameter cost.',
        '- Tight setup was a training-coverage failure in the previous recipe. Historical SPI1/SPI3 readout ablations implicate stale middle-layer contributions, while retraining the full sparse baseline resolves the condition.',
        '- Last-layer-only registered readout has a demonstrable information-delay limitation for one-tick setup. The tested all-node readout avoids that limitation.',
        '- UART difficulty is not explained simply by absent long memory. Some trained states retain distinctions for 160 ticks but still fail complete messages; simple-frame traces show drifting/missing sampling pulses. Loss rebalance, longer training windows, allocation/input access, generic readout factorization, curriculum and single-port circulation trials are preserved as training/architecture diagnostics, not capacity proofs.','',
        'See [FOLLOWUPS.md](FOLLOWUPS.md) for the hypotheses, advance thresholds and decisions recorded before each comparison. Learning curves and optimizer checkpoints remain in every model directory. No candidate is called architecturally impossible.','',
        f"The current ledger contains {len(trial_rows)} recipe/shape/profile/seed fits. [training_trials.csv](runs/connectivity01/training_trials.csv) and [training_per_condition.csv](runs/connectivity01/training_per_condition.csv) retain failures and exposure counts. Forked rescue histories include their starting exposure, so summing those counts would double-count earlier work.",'',
        '![UART learning curves](runs/connectivity01/figures/uart_learning_curves.png)','',
        '## Fixed topology and demonstrations','']
    demo=root/'demonstration_configs';demo.mkdir(exist_ok=True)
    freeze=json.loads((confirmation/'freeze.json').read_text())
    for sh in shapes:
        lines.append(f'![{sh.name} connections](runs/connectivity01/figures/{sh.name}.png)');lines.append('')
        topology=json.loads((root/'shapes'/f'{sh.name}.json').read_text());write_json(demo/f'{sh.name}.json',topology)
        for e in freeze['entries']:
            if e['shape']==sh.name and e['seed']==11:
                p=np.load(confirmation/e['weight_path'])['p'];np.savez_compressed(demo/f"{sh.name}_{e['profile']}_seed11.npz",p=p)
    lines+=['The diagrams show actual graph edges, not placement. Exact masks and seed-11 clocked demonstration weights are in `runs/connectivity01/demonstration_configs`; every other seed is retained in the immutable confirmation snapshot. Seed 11 is a consistent example, not a selectively chosen best seed. These are trained recurrent networks; no on-chip training, hardware compliance, STA, electrical or reference-design gate is claimed. `clock_hz` stays 0.','',
        '## Reproduce and resume','',
        'Use the bundled study Python and one BLAS thread. Initial launch refuses an existing run directory. Repeating a completed batch is idempotent; checkpoints include Adam moments and exposure counts.','',
        '```sh','export OPENBLAS_NUM_THREADS=1','PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python',
        'OUT=work/study/hero_shape_connectivity/runs/reproduction01',
        '$PY -B -m work.study.hero_shape_connectivity.run launch --output "$OUT"',
        '$PY -B -m work.study.hero_shape_connectivity.run train --output "$OUT" --epochs 30 --label initial30 --workers 12',
        '```','',
        'Exact batch job lists, source snapshots, environment, corpus seeds and historical hashes are filed in the run. For confirmation replay, use its frozen `source` package, its frozen weights, and saved waveform files. Current source changes must not be substituted silently for a frozen snapshot.','',
        ('**Outstanding:** confirm the remaining full-profile finalist under the unchanged six-seed gates; active trials are recorded in runs/connectivity01/ACTIVE.md.' if qualified_count<2 else '**Full-profile qualification:** see QUALIFIED_SHAPES.md and its immutable fresh/regression records. Current control comparisons and preserved failed trials are recorded separately.')+' USB/Ethernet extensions remain untested.']
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print('report refreshed',ROOT/'REPORT.md')

if __name__=='__main__':report(ROOT/'runs'/'connectivity01')
