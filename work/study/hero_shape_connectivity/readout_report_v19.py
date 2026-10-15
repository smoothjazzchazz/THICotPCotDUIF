"""Report the recorded readout-routing interventions without hiding failed fits."""
import csv,json,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,cost,PROFILES,SEEDS
from .train import write_json
from .report import diagram


def passed(s):
    return s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))


def report():
    root=ROOT/'runs/connectivity01';rows=[];conditions=[]
    stages=[('phase_readout_projection_v14','First-layer-complete projection'),
            ('phase_readout_projection_v15','Fast-ring-complete projection'),
            ('phase_readout_supervised_v16','Supervised UART head fitting'),
            ('phase_readout_projection_clocked_v17','Clocked projection'),
            ('phase_readout_supervised_clocked_v18','Supervised clocked head fitting'),
            ('phase_grid_margin_v19','Balanced startup-grid output fitting'),
            ('phase_clocked_pause_v20','Expanded continuous-pause output fitting')]
    for recipe,title in stages:
        for file in sorted((root/'models'/recipe).glob('*/*/*/block_*.json')):
            b=json.loads(file.read_text());s=b['selected']
            row=dict(stage=title,recipe=recipe,shape=b['shape'],profile=b['profile'],seed=b['seed'],
                     epochs=b['epochs'],selected_epoch=b['selected_epoch'],exposure_ticks=b['exposure_ticks'],
                     exact_messages=s['exact_messages'],valid_messages=s['valid_messages'],
                     boundary_errors=s['boundary_errors'],invalid_accepted=s['invalid_accepted'],
                     background_accepted=s['background_accepted'],pass_all=passed(s),
                     block=str(file),block_sha256=digest(file),checkpoint=b['checkpoint'])
            rows.append(row)
            for condition,metrics in s['conditions'].items():conditions.append(dict(**row,condition=condition,metrics=metrics))
    with (root/'readout_routing_trials.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write_json(root/'readout_routing_conditions.json',conditions)
    candidates=json.loads((ROOT/'readout_cost_pair_v3_candidates.json').read_text());shapes=[make_shape(**kw) for kw in candidates]
    resources={s.name:cost(s) for s in shapes};write_json(root/'readout_routing_resources.json',resources)
    for sh in shapes:diagram(sh,root/'figures'/f'{sh.name}.png')
    # Separate the actual backbone from the head incidence matrix so dense routes
    # do not obscure the two closed rings in the overview.
    base=make_shape(**{**candidates[0],'cell':'plain'});diagram(base,root/'figures/readout_shared_backbone.png',backbone_only=True)
    fig,axes=plt.subplots(1,2,figsize=(12,4),sharey=True)
    for ax,sh,title in zip(axes,shapes,('Dense: 48 parents per unit','Reduced: 32 parents per unit')):
        mask=np.zeros((16,48));take=sh.dst>=48;mask[sh.dst[take]-48,sh.src[take]]=1
        ax.imshow(mask,aspect='auto',interpolation='nearest',cmap='Blues',vmin=0,vmax=1)
        for border in (15.5,31.5):ax.axvline(border,color='#c26300',lw=1.5)
        ax.set_xticks([7.5,23.5,39.5],['Sparse\n0–15','Fast ring\n16–31','Slow ring\n32–47']);ax.set_title(title)
        ax.set_xlabel('Current backbone outputs; blue = one physical directed edge')
        ax.set_yticks([0,7,15],[48,55,63])
    axes[0].set_ylabel('Nonlinear readout unit');fig.suptitle('Same 48-state backbone and 16-unit head; 256 connections removed')
    fig.tight_layout();fig.savefig(root/'figures/readout_parent_masks.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,7))
    for si,sh in enumerate(shapes):
        for pi,profile in enumerate(('uart_n','uart_e')):
            for seed in SEEDS:
                file=root/'models/phase_readout_supervised_v16'/sh.name/profile/str(seed)/'history.jsonl'
                history=[json.loads(line) for line in file.read_text().splitlines()]
                label=f'{"dense" if si==0 else "reduced"}, seed {seed}'
                style='-' if si==0 else '--';color=f'C{SEEDS.index(seed)}'
                axes[0,pi].plot([h['epoch'] for h in history],[100*h['message_accuracy'] for h in history],style,color=color,label=label,lw=1.1)
                axes[1,pi].plot([h['epoch'] for h in history],[h['boundary_errors'] for h in history],style,color=color,lw=1.1)
    for pi,profile in enumerate(('UART 8N1','UART 8E1')):
        axes[0,pi].set_title(profile);axes[0,pi].set_ylim(-1,101);axes[1,pi].set_yscale('symlog',linthresh=1);axes[1,pi].set_xlabel('Supervised head optimization block (up to 80 iterations)')
    axes[0,0].set_ylabel('Exact complete messages (%)');axes[1,0].set_ylabel('Boundary errors (zero required)')
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=4,fontsize=8)
    for ax in axes.flat:ax.grid(alpha=.2)
    fig.suptitle('Readout fitting: every evaluation, including collapses and failed seed 47');fig.tight_layout(rect=(0,.12,1,.95));fig.savefig(root/'figures/readout_head_v16_curves.png',dpi=160);plt.close(fig)
    lines=['# Reducing nonlinear readout connections','',
        'This comparison removes 256 actual physical edges from the dense 64-unit receiver: each of its 16 nonlinear readout units receives 32 backbone states instead of 48. The backbone, node count, state count, current-sample head, six event outputs and generic input features remain fixed. All fast-ring states remain accessible to every hidden readout unit; alternating halves of the first layer and slow ring provide the other 16 inputs.','',
        '| Graph | Recurrent / inter-layer / input / final-output edges | MACs/sample | Parameters | All modeled multiplies/sample | Numeric storage |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for sh in shapes:
        c=cost(sh);lines.append(f"| {sh.name.split('_readout16_')[-1]} | {c['recurrent_edges']} / {c['inter_layer_edges']} / {c['input_edges']} / {c['readout_edges']} | {c['macs_per_tick']} | {c['parameters']} | {c['macs_per_tick']+96} | {c['known_numeric_storage_bytes']} bytes |")
    a,b=map(cost,shapes)
    lines+=['',f"The reduction is {100*(1-b['macs_per_tick']/a['macs_per_tick']):.2f}% in MACs and {100*(1-b['parameters']/a['parameters']):.2f}% in parameters, or {100*(1-(b['macs_per_tick']+96)/(a['macs_per_tick']+96)):.2f}% including the 96 common leak-blend multiplies. Both have 48 stored states, 64 nonlinear units and activation depth 2. Storage decreases only 4.43% because the shared activation table dominates this subtotal. Routing, physical area and frequency are unmeasured; see ARCHITECTURE_COMPARISON.md for common costs and exclusions.",'',
        '![Shared backbone with actual directed ring closures](runs/connectivity01/figures/readout_shared_backbone.png)','',
        'The backbone drawing omits the extra head. Its two ring branches both receive the sparse-layer ports; neither ring feeds the other. The following incidence matrices show every added backbone-to-head connection. Both graphs then connect all 64 outputs to all six event logits.','',
        '![Every backbone-to-head connection](runs/connectivity01/figures/readout_parent_masks.png)','',
        '## Controlled training and interpretation','',
        'Each same-seed pair starts from the same learned dense backbone and sees the same independent training waveforms. The first step fits each hidden preactivation on the full training covariance; the intact control exactly represents its source. This is a transfer/pruning study, not evidence of easier learning from random initialization. Failed seed 47 stays in every six-seed comparison.','',
        'Both graphs then receive the same per-seed supervised bank and conditional optimization rule: retain a whole-development pass with zero bank errors, otherwise allow eight blocks of up to 80 L-BFGS iterations. Only existing head weights/biases and six output rows change. Actual optimization exposure differs under this declared rule and is recorded in the CSV; it is not described as identical iteration counts. Projection scans every training tick, while supervised fitting uses recorded representative states.','',
        'The first 32-parent layout retained all first-layer states and half of each ring. It failed to preserve UART recovery after projection. The equal-edge alternative retaining all fast-ring states lowered training projection residual in all three pilot seeds and recovered several full development fits. Supervised head fitting then repaired the remaining required no-parity seeds and all clocked profiles. This supports the value of routing the complete fast phase representation to the nonlinear head for these weights; it is not a proof that the first layout cannot learn.','',
        'Parity seed 101 still had a cold-start boundary error. Balanced startup-grid coverage repaired the reduced graph without changing any recurrent or hidden-head weights. Its selected checkpoint passes all 57,344 grid cases with zero canonical/pulse/boundary errors, all 190,592 retained bank states, all 8,864 development groups and the 320 older startup training cases. The dense control selection also passes the grid and development, but its earlier development-selected checkpoint retains 13 canonical bank-label errors; later fits and this discrepancy remain recorded. Training-label equality is not substituted for fresh message qualification.','',
        'Seed 47 remains unsuccessful for UART in both graphs. Some supervised iterations collapse and then recover; the source checkpoint is retained when it scores better. These are unresolved training/representation cases, not demonstrated impossibility. No confirmation waveform is used for fitting or checkpoint selection.','',
        '## Completed development stages','',
        '| Stage | Graph | UART-N | UART-E | I2C | SPI0 | SPI1 | SPI2 | SPI3 |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for recipe,title in stages:
        for name in sorted({r['shape'] for r in rows if r['recipe']==recipe}):
            counts=[]
            for profile in PROFILES:
                group=[r for r in rows if (r['recipe'],r['shape'],r['profile'])==(recipe,name,profile)]
                counts.append(f"{sum(r['pass_all'] for r in group)}/{len(group)}" if group else '—')
            lines.append(f"| {title} | {name.split('_readout16_')[-1]} | "+' | '.join(counts)+' |')
    lines+=['','These are whole-development passes, including boundaries and rejection. Stage sample counts differ explicitly; only frozen six-seed confirmation can qualify a graph.','',
        '![All supervised UART evaluations](runs/connectivity01/figures/readout_head_v16_curves.png)','',
        '## Fresh confirmation','',
        'The unchanged practical threshold was declared before evaluation: within 1 percentage point per condition with at least 95% recovery, no worse boundaries/rejection, and at least 15% fewer MACs and parameters, replicated in at least five paired seeds. Full qualification remains stricter: exact complete messages and boundaries, no accepted invalid/background messages, and the same five of six passing seeds in every profile across fresh and prior regression suites.','',
        'Both selected portfolios were frozen before family 531000000 was generated (`readout_cost_full_v3a`). The reduced graph failed mandatory SPI1 seed replication on pause traffic. CLOCKED_PAUSE_V20.md preserves those failures, causal traces and the independent full-pool coverage repair. The second freeze (`readout_cost_full_v3b`, family541000000) changes only six existing output-row configurations; all recurrent/hidden parameters and physical masks remain fixed. It adds A to the mandatory regression suites alongside full_shape_v2a and dense_full_v3a. Float and Q3.12 are separate. See QUALIFIED_SHAPES.md and the frozen joint qualification files for completed results; development counts above are not confirmation.','',
        '[Every completed stage and its exposure](runs/connectivity01/readout_routing_trials.csv); [per-condition development results](runs/connectivity01/readout_routing_conditions.json); [exact resource definitions](runs/connectivity01/readout_routing_resources.json). Checkpoints, raw learning curves, projections, covariance matrices, bank identities and source snapshots remain under their original v14–v19 labels. REPRODUCE.md gives immutable replay/resume commands.']
    (ROOT/'READOUT_ROUTING_COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print('Recorded readout-stage fits',len(rows),flush=True)


if __name__=='__main__':report()
