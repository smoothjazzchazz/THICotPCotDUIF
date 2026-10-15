"""Matched native-coverage results and raw trajectories; incomplete jobs stay visible."""
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .run import ROOT
from .shapes import make_shape,SEEDS,cost
from .train import key,write_json
from .report import diagram

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';names=['wider_both2_candidate.json','current_phase_candidate.json','reduced56_candidate.json','mixed_candidates.json','no_local_candidate.json','lane_candidates.json','readout_candidates.json','mixed_first_candidates.json']
    candidates=[kw for n in names for kw in json.loads((ROOT/n).read_text())];rows=[]
    lines=['# Matched native structural comparison','',
        'Original2,304-group development, not qualification or the later8,864-group suite. All configurations use the same native-v3 data schedule,512-tick training windows, original seed set and event interface. The first120 epochs have identical exposure per profile. Matched fixed-ring initialization retains the16-node fast ring; other weights are trained off chip. First-gate/control no-parity now extends to all six seeds; direct native parity uses the initial three, with later N-to-E transfer reported separately. See CURRENT_FINDINGS.md for expanded development.','',
        '| Shape | Nonlinear units / states | MACs | Parameters | Profile | Completed / planned | Original-suite passes |','| --- | ---: | ---: | ---: | --- | ---: | ---: |']
    for kw in candidates:
        sh=make_shape(**kw);c=cost(sh);seeds=SEEDS[:3] if kw.get('code')=='zrr' or kw.get('injection','').startswith('lanes') or kw.get('cell')=='readout16_fanin8' or kw.get('leaks',[1])[0]==.5 else SEEDS
        figure=root/'figures'/f'{sh.name}_native_v3_curves.png';fig,axes=plt.subplots(2,2,figsize=(11,7),sharex='col')
        for column,profile in enumerate(('uart_n','uart_e')):
            profile_seeds=SEEDS if profile=='uart_n' and kw.get('leaks',[1])[0]==.5 else seeds
            complete=passed=0
            for seed in profile_seeds:
                folder=root/'models'/'phase_native_v3'/sh.name/profile/str(seed);file=folder/'history.jsonl'
                if not file.exists():continue
                records=[json.loads(s) for s in file.read_text().splitlines()];ev=[r for r in records if 'dev_loss' in r];best=max(ev,key=key)
                done=(folder/'block_0120.json').exists();ok=best['message_accuracy']==1 and not any(best[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
                complete+=done;passed+=done and ok
                rows.append(dict(shape=sh.name,profile=profile,seed=seed,completed=done,epoch=records[-1]['epoch'],best=best,resources=c))
                x=[r['exposure_ticks']/1e6 for r in ev]
                axes[0,column].plot(x,[r['message_accuracy']*100 for r in ev],label=str(seed),lw=1)
                axes[1,column].plot(x,[max(1e-10,r['dev_loss']) for r in ev],lw=1)
            axes[0,column].set_title(profile);axes[0,column].set_ylim(-1,101)
            if axes[0,column].lines:axes[0,column].legend(title='Seed',ncol=3,fontsize=8)
            axes[1,column].set_yscale('log');axes[1,column].set_xlabel('Training ticks (millions)')
            lines.append(f"| {sh.name} | {c['nodes']} / {c['stored_states']} | {c['macs_per_tick']} | {c['parameters']} | {profile} | {complete}/{len(profile_seeds)} | {passed}/{complete} |")
        axes[0,0].set_ylabel('Exact complete messages (%)');axes[1,0].set_ylabel('Development event loss')
        for ax in axes.flat:ax.grid(alpha=.2)
        fig.suptitle(sh.name+'\nRaw evaluation points; peaks and subsequent collapse are both retained',fontsize=10);fig.tight_layout();fig.savefig(figure,dpi=150);plt.close(fig)
        diagram(sh,root/'figures'/f'{sh.name}.png')
    lines+=['','High-rate collapse is a training-recipe limitation. Lower-rate continuation is recorded separately under `phase_native_refine_v3`, beginning at each configuration’s own best checkpoint; it does not overwrite these matched first-stage results. The meaningful-result and full qualification thresholds remain in README.md/FOLLOWUPS.md.','',
        'Input, state and gate counts differ in the reduced candidates and are explicit above. The mixed slow ring costs 48 tanh proposals plus 16 sigmoid gates; its fixed-leak control has 48 proposals. All connection masks and gate edges are serialized under `runs/connectivity01/shapes/`.','']
    lines+=['## Declared lower-rate continuation','',
        'Each unresolved native120 fit receives60 epochs at0.0001 from its own best checkpoint. Passing fits are retained with zero additional training. This is the same conditional training rule, not identical additional exposure for successful and unsuccessful fits. Later extensions are shown separately.','',
        '| Shape | Profile | Completed continuations | Whole-suite passes | Exact-message range | Boundary-error range |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    extensions=[]
    for kw in candidates:
        sh=make_shape(**kw)
        for profile in ('uart_n','uart_e'):
            results=[]
            for seed in SEEDS:
                folder=root/'models'/'phase_native_refine_v3'/sh.name/profile/str(seed)
                path=folder/'block_0060.json'
                if not path.exists():path=folder/'block_0000.json'
                if path.exists():results.append(json.loads(path.read_text()))
                for p in folder.glob('block_*.json'):
                    b=json.loads(p.read_text())
                    if b['epochs']>60:extensions.append(b)
            if not results:continue
            values=[r['selected']['message_accuracy'] for r in results];boundaries=[r['selected']['boundary_errors'] for r in results]
            passed=sum(r['selected']['message_accuracy']==1 and not any(r['selected'][k] for k in ('boundary_errors','invalid_accepted','background_accepted')) for r in results)
            lines.append(f"| {sh.name} | {profile} | {len(results)} | {passed}/{len(results)} | {100*min(values):.3f}–{100*max(values):.3f}% | {min(boundaries)}–{max(boundaries)} |")
    if extensions:
        lines+=['','Additional training on still-improving comparisons:','',
            '| Shape | Profile / seed | Refinement epochs | Exact messages | Boundary errors |',
            '| --- | --- | ---: | ---: | ---: |']
        for b in extensions:lines.append(f"| {b['shape']} | {b['profile']} / {b['seed']} | {b['epochs']} | {100*b['selected']['message_accuracy']:.3f}% | {b['selected']['boundary_errors']} |")
    lines+=['']
    for kw in candidates:
        sh=make_shape(**kw);lines += [f'![{sh.name} raw learning curves](runs/connectivity01/figures/{sh.name}_native_v3_curves.png)','',f'![{sh.name} directed graph](runs/connectivity01/figures/{sh.name}.png)','']
    write_json(root/'native_v3_progress.json',rows);(ROOT/'NATIVE_COMPARISON.md').write_text('\n'.join(lines).rstrip()+'\n')
