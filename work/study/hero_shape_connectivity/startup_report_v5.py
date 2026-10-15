"""Keep coverage and parameter-learning diagnostics separate from qualification."""
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .run import ROOT
from .shapes import make_shape,SEEDS

if __name__=='__main__':
    root=ROOT/'runs/connectivity01';kw=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];sh=make_shape(**kw)
    lines=['# Startup and training-coverage diagnostics','',
        '**Ongoing research; zero complete multi-protocol shapes qualify.** These results are development/training diagnostics, not fresh confirmation.',
        '', 'The enlarged development suite contains8,864 valid groups/profile: the original2,304,4,000 sustained-corner groups, and2,560 independent known-idle/error-startup groups. No previous condition was removed. Training and development families are distinct.',
        '', '## Completed blocks', '',
        '| Recipe | Profile / seed | Budget / selected round | Exact messages | Boundaries | Failed complete training-startup cases |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for recipe in ('phase_startup_margin_v5','phase_startup_readout_v5','phase_startup_core_v5'):
        for profile in ('uart_n','uart_e'):
            for seed in SEEDS:
                files=sorted((root/'models'/recipe/sh.name/profile/str(seed)).glob('block_*.json'))
                if not files:continue
                b=json.loads(files[-1].read_text());s=b['selected']
                lines.append(f"| {recipe} | {profile} / {seed} | {b['epochs']} / {b['selected_epoch']} | {s['exact_messages']}/{s['valid_messages']} | {s['boundary_errors']} | {b['selected_training_failed_cases']}/320 |")
    lines+=['', 'The margin fit updates all six affine output rows while holding every state parameter fixed. Its unstable iterates and solver diagnostics are retained. The separate cold-prefix pair uses the same512-tick episodes, anchors, class weights and180,224 optimized ticks per round; only permission to change state parameters differs. The16-node fast ring remains protected in both arms.',
        '', '## Causal observations', '',
        '- Frozen N47 cold traces first call a true STOP a data bit at tick168; later alignment errors follow. Sampling before that point is correct.',
        '- Adding16 observable high ticks before each of seven failing N47 training files fixes every tested message/boundary. It also fixes the tested N71 cold failure. E47/E101 failures persist with up to1,024 extra ticks. These changed-input probes never replace a required cold-start test.',
        '- N47 state refinement selects round16 with8,864/8,864 development groups and all320 complete training-startup cases passing. The matched output-only fit leaves nine development groups failing. This is a seed-specific parameter-learning result, not a topology-dependent advance or capacity proof.',
        '- The same cold-prefix state refinement worsens parity E47 in later rounds; its earlier checkpoint is preserved. Do not generalize the N47 fix to all UART failures.',
        '', '## Matched cold-prefix learning curves', '']
    fig,axes=plt.subplots(2,2,figsize=(10,6.5),sharex='col')
    for col,profile in enumerate(('uart_n','uart_e')):
        for mode,color in [('readout','#315c9b'),('core','#008b72')]:
            path=root/'models'/f'phase_startup_{mode}_v5'/sh.name/profile/'47/history.jsonl'
            if not path.exists():continue
            h=[json.loads(x) for x in path.read_text().splitlines()];h=[x for x in h if 'dev_loss'in x];x=[r['exposure_ticks']/1e6 for r in h]
            axes[0,col].plot(x,[r['valid_messages']-r['exact_messages'] for r in h],marker='.',color=color,label='Outputs only' if mode=='readout' else 'State + outputs')
            axes[1,col].plot(x,[r['boundary_errors'] for r in h],marker='.',color=color)
        axes[0,col].set_title(profile+' / seed47');axes[0,col].legend(fontsize=8)
        axes[1,col].set_xlabel('Optimized training ticks (millions)')
    axes[0,0].set_ylabel('Failed complete development groups');axes[1,0].set_ylabel('Development boundary errors')
    for ax in axes.flat:ax.set_yscale('symlog',linthresh=1);ax.grid(alpha=.25)
    fig.suptitle('Identical physical graph and training exposure; failed iterates retained',fontsize=12);fig.tight_layout()
    path=root/'figures/startup_parameter_comparison_v5.png';fig.savefig(path,dpi=160);plt.close(fig)
    lines+=['![Matched parameter-learning curves](runs/connectivity01/figures/startup_parameter_comparison_v5.png)', '',
        'Per-case training audits, immutable source/checkpoint hashes, all iterations and selected weights are stored under the corresponding model folders. Frozen full_shape_v2a remains a failed confirmation. The next confirmation will retain all original gates, add independent startup cases, and separately replay the corrected prior corpus as a regression suite.']
    (ROOT/'STARTUP_REFINEMENT.md').write_text('\n'.join(lines).rstrip()+'\n')
