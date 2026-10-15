"""Publish the balanced training-coverage result without claiming qualification."""
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .run import ROOT
from .data import conditions


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';folder=next((root/'models/phase_grid_margin_v10').glob('*/*/*'));block=json.loads((folder/'block_0008.json').read_text());before=json.loads((folder/'source_grid_pulse_audit.json').read_text());after=json.loads((folder/'selected_grid_audit.json').read_text())
    counts=np.zeros((32,7),dtype=int)
    for item in before['failures']:
        idle,ci=map(int,item['block'].split('_'));counts[idle-17,ci]+=bool(item['pulse_errors'])
    fig,ax=plt.subplots(figsize=(9,5));im=ax.imshow(counts.T,origin='lower',aspect='auto',vmin=0,cmap='YlOrRd',extent=[16.5,48.5,-.5,6.5]);fig.colorbar(im,ax=ax,label='Cases with wrong event pulses /256 bytes')
    ax.set_yticks(range(7),conditions('uart_e'));ax.set_xticks([17,20,24,28,32,36,40,44,48]);ax.set_xlabel('Initial idle length (ticks)');ax.set_title('Dense-readout parity seed101: where random startup training missed coverage')
    for idle,ci in zip(*np.nonzero(counts)):ax.text(idle+17,ci,str(counts[idle,ci]),ha='center',va='center',fontsize=8,color='black')
    fig.tight_layout();fig.savefig(root/'figures/startup_grid_v10_failures.png',dpi=160);plt.close(fig)
    score=block['selected'];lines=['# Balanced initial-state coverage','',
        '**Training-coverage result for one learned configuration; not a fresh topology result.**','',
        'The dense-readout64 parity configuration for seed101 passed all320 prior startup training cases, but missed one first-byte STOP in expanded development. A separate, balanced training grid exposed more cases with the same general risk: zero neural state followed by a short initial idle and varied first-byte timing.','',
        'The grid crosses every idle length17–48, every byte0–255 and all seven existing UART timing conditions:57,344 independent one-byte streams. A separate seeded phase/jitter draw is used for each combination. All generated payloads pass the independent waveform parser. No development or confirmation waveform is copied.','',
        '| Measurement | Before grid fitting | Selected after fitting |','| --- | ---: | ---: |',
        f"| Training-grid cases with wrong event pulses | {before['pulse_failed_cases']}/57,344 | {after['pulse_mismatch_cases']}/57,344 |",
        f"| Training-grid boundary errors | {before['boundary_errors']} | {after['boundary_errors']} |",
        f"| Expanded-development exact messages | 8,863/8,864 | {score['exact_messages']:,}/8,864 |",
        f"| Expanded-development boundary errors | 1 | {score['boundary_errors']} |",'',
        'All43 original grid failures were independently reproduced by the scalar inference kernel. The selected checkpoint is also replayed through the scalar kernel on the whole development suite and through all320 startup training files. Grid metrics report event pulses separately from raw training classes.','',
        f"Only the existing six affine output rows changed. The48 recurrent states,16 nonlinear readout units, their parameters, routes and configured leaks stayed fixed. Selection retained round{block['selected_epoch']} of{block['completed_rounds']} completed rounds; every iterate and original source remains filed. This supports a coverage explanation for this configuration. It does not prove that every seed or graph has the same failure mechanism.",'',
        '![Balanced startup coverage failures](runs/connectivity01/figures/startup_grid_v10_failures.png)','',
        'Training families391000000/392000000, full data/state hashes, the source checkpoint, support constraints, optimizer histories and per-case audits are recorded under `runs/connectivity01/models/phase_grid_margin_v10/`. The frozen batch is `grid_margin_v10_e101_8`; use `resume_batch grid_margin_v10_e101_8 --entry grid_margin_v10 --workers 1` only if interrupted. New independent confirmation remains mandatory.']
    (ROOT/'COVERAGE_V10.md').write_text('\n'.join(lines).rstrip()+'\n')
