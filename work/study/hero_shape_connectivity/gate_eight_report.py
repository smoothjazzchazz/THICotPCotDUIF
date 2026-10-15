"""Report the declared eight-state/eight-gate allocation comparison, including failures."""
import csv,json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .run import ROOT,digest
from .shapes import make_shape,cost
from .train import write_json


def report():
    root=ROOT/'runs/connectivity01';candidates=json.loads((ROOT/'gate_eight_candidates.json').read_text());rows=[];conditions=[]
    names=['64 states','56 states','56 states + 8 gates'];lines=['# Eight gates versus eight slow states','',
        'This targeted comparison holds the original24-node sparse layer,16-node fast ring, input routing and event interface fixed. It compares a24-node slow ring, a16-node slow ring, and that same reduced backbone with eight conditional first-layer gates. The retained-parent construction preserves all surviving edges and closes the shortened slow ring. Each gate reads the fast-ring quarters, slow inlet and its own prior state. Gate indices are0,3,6,9,12,15,18,21.','',
        'All three use the same independent native-v6 training schedule,120 epochs,512-tick windows and seeds11,29,47 for each UART profile. The declared continuation retains an expanded-development pass or gives an unresolved fit60 lower-rate epochs from its own best checkpoint. This is a three-seed diagnostic; it cannot satisfy the six-seed qualification requirement.','',
        '| Shape | Units / states | MACs/sample | Parameters |','| --- | ---: | ---: | ---: |']
    for name,kw in zip(names,candidates):
        sh=make_shape(**kw);c=cost(sh);lines.append(f"| {name} | {c['nodes']} / {c['stored_states']} | {c['macs_per_tick']} | {c['parameters']} |")
    for recipe,title in [('phase_native_v6','Matched native120'),('phase_native_refine_v6','Declared lower-rate continuation')]:
        fig,axes=plt.subplots(2,2,figsize=(11,7));lines += ['',f'## {title}','',
            '| Shape | Profile / seed | Completed | Selected exact messages | Boundary errors | Full development pass |',
            '| --- | --- | ---: | ---: | ---: | --- |']
        for ni,(name,kw) in enumerate(zip(names,candidates)):
            sh=make_shape(**kw)
            for pi,profile in enumerate(('uart_n','uart_e')):
                for si,seed in enumerate((11,29,47)):
                    folder=root/'models'/recipe/sh.name/profile/str(seed);blocks=sorted(folder.glob('block_*.json'));journal=folder/'history.jsonl'
                    if not journal.exists():continue
                    history=[json.loads(l) for l in journal.read_text().splitlines()];evaluations=[h for h in history if 'dev_loss'in h]
                    label=f'{name}, seed{seed}';style=('-', '--', ':')[si];color=f'C{ni}'
                    axes[0,pi].plot([h['epoch'] for h in evaluations],[100*h['message_accuracy'] for h in evaluations],style,color=color,label=label,lw=1.1)
                    axes[1,pi].plot([h['epoch'] for h in evaluations],[h['boundary_errors'] for h in evaluations],style,color=color,lw=1.1)
                    if not blocks:
                        lines.append(f'| {name} | {profile}/{seed} | pending, epoch{history[-1]["epoch"]} | — | — | pending |');continue
                    block=blocks[-1];b=json.loads(block.read_text());s=b['selected'];passed=s['message_accuracy']==1 and not any(s[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
                    r=dict(label=name,shape=sh.name,profile=profile,seed=seed,recipe=recipe,epochs=b['epochs'],selected_epoch=b['selected_epoch'],exposure_ticks=b['exposure_ticks'],exact_messages=s['exact_messages'],valid_messages=s['valid_messages'],boundary_errors=s['boundary_errors'],invalid_accepted=s['invalid_accepted'],background_accepted=s['background_accepted'],full_development_pass=passed,source_block=str(block),source_sha256=digest(block));rows.append(r)
                    for condition,score in s['conditions'].items():conditions.append(dict(**r,condition=condition,condition_metrics=score))
                    lines.append(f"| {name} | {profile}/{seed} | {b['epochs']} | {s['exact_messages']}/{s['valid_messages']} | {s['boundary_errors']} | {'yes' if passed else 'no'} |")
        for pi,profile in enumerate(('uart_n','uart_e')):
            axes[0,pi].set_title(profile);axes[0,pi].set_ylim(-1,101);axes[1,pi].set_yscale('symlog',linthresh=1);axes[1,pi].set_xlabel('Epoch in this training stage')
        axes[0,0].set_ylabel('Exact complete messages (%)');axes[1,0].set_ylabel('Boundary errors (zero required)')
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=8)
        for ax in axes.flat:ax.grid(alpha=.2)
        fig.suptitle(title+' — raw evaluations, including collapses and failed boundaries');fig.tight_layout(rect=(0,.11,1,.96));name=recipe+'_allocation_curves.png';fig.savefig(root/'figures'/name,dpi=150);plt.close(fig)
        lines += ['',f'![Training curves](runs/connectivity01/figures/{name})']
    complete=[r for r in rows if r['recipe']=='phase_native_refine_v6'];lines += ['',f'Completed final continuations: {len(complete)}/18. Whole expanded-development passes: {sum(r["full_development_pass"] for r in complete)}/{len(complete)}.','',
        'The prespecified meaningful threshold remains a replicated20-percentage-point improvement on unresolved exact messages with no material regression, or comparable>=95% recovery with>=15% lower MACs and parameters. Eight sparse gates have not established that result in the completed comparisons. Extra slow states are not uniformly helpful either: the ungated56-state control has a passing no-parity fit while the64-state controls still make boundary errors. This does not establish a general ranking or prove any shape incapable.','',
        'The successful16-gate candidate uses a different16/16/16 allocation and gate coverage. Its result cannot be attributed solely to replacing eight slow states by eight gates. Native high-rate collapse, later recovery, incomplete convergence and boundary failures remain visible in these curves. Full-profile qualification is reported separately in QUALIFIED_SHAPES.md.','',
        '[All completed fit records](runs/connectivity01/gate_eight_comparison.csv); [per-condition development metrics](runs/connectivity01/gate_eight_conditions.json). Job lists, immutable source snapshots and all checkpoints remain under the original native/refinement wave labels. Numeric costs exclude unmeasured routing/area; common feature, assembly and activation-table costs are detailed in ARCHITECTURE_COMPARISON.md.']
    with (root/'gate_eight_comparison.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write_json(root/'gate_eight_conditions.json',conditions);(ROOT/'GATE_ALLOCATION_COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print('Final continuations completed',len(complete),'of18',flush=True)

if __name__=='__main__':report()
