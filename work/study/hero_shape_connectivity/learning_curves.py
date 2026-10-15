"""Comparable within-stage curves; no double-counting shared pretraining."""
import json
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from .run import ROOT
from .shapes import make_shape,SEEDS


def plot(root):
    candidates=json.loads((ROOT/'phase_route_candidates.json').read_text());shapes=[make_shape(**c) for c in candidates]
    colors=plt.get_cmap('tab10').colors
    for recipe in ('phase_circulation','phase_ring_fixed','phase_portfolio','phase_extended','phase_profile_fresh','phase_recovery','phase_recovery_readout'):
        fig,axes=plt.subplots(2,2,figsize=(12,7),sharex='col');found=False
        for column,profile in enumerate(('uart_n','uart_e')):
            for si,sh in enumerate(shapes):
                for j,seed in enumerate(SEEDS):
                    path=root/'models'/recipe/sh.name/profile/str(seed)/'history.jsonl'
                    if not path.exists():continue
                    rows=[json.loads(line) for line in path.read_text().splitlines()];rows=[r for r in rows if 'dev_loss' in r]
                    if not rows:continue
                    found=True;x=[r['exposure_ticks']/1e6 for r in rows]
                    axes[0,column].plot(x,[100*r['message_accuracy'] for r in rows],color=colors[j],ls='-' if si==0 else '--',lw=1.2,alpha=.8)
                    axes[1,column].plot(x,[max(1e-10,r['dev_loss']) for r in rows],color=colors[j],ls='-' if si==0 else '--',lw=1.2,alpha=.8)
            axes[0,column].set_title(profile);axes[0,column].set_ylim(-1,101)
            axes[1,column].set_yscale('log');axes[1,column].set_xlabel('Training ticks within this stage (millions)')
        axes[0,0].set_ylabel('Exact complete development messages (%)');axes[1,0].set_ylabel('Canonical development loss')
        for ax in axes.flat:ax.grid(alpha=.2)
        handles=[Line2D([0],[0],color=colors[j],label=f'Seed {s}') for j,s in enumerate(SEEDS)]
        handles.extend([Line2D([0],[0],color='black',ls='-',label='One return per ring'),Line2D([0],[0],color='black',ls='--',label='Two returns per ring')])
        fig.legend(handles=handles,ncol=4,loc='lower center',bbox_to_anchor=(.5,-.02),frameon=False)
        corpus='extended development' if recipe in ('phase_extended','phase_profile_fresh','phase_recovery','phase_recovery_readout') else 'original development'
        fig.suptitle(f'{recipe}: {corpus}; all six seeds retained\nRaw evaluation checkpoints, not a confirmation or a smoothed best-case envelope')
        fig.tight_layout(rect=(0,.07,1,.94))
        if found:fig.savefig(root/'figures'/f'{recipe}_curves.png',dpi=160)
        plt.close(fig)
    print('Saved within-stage UART accuracy and loss curves.')

if __name__=='__main__':plot(ROOT/'runs'/'connectivity01')
