"""Explain a finite training-label obstruction without overstating capacity."""
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/hero-shape-matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .run import ROOT
from .bit_hold_diagnostic_v9 import held_bit_labels
from .runtime import pulses


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';cert=json.loads((root/'diagnostics/margin_certificate_v8_n131/result.json').read_text())
    variants=[json.loads((root/f'diagnostics/bit_hold_v9_n131/extension_{n}.json').read_text()) for n in (1,2)]
    truth=np.zeros(40,dtype=np.int32);truth[[8,24]]=2;held=held_bit_labels(truth,1)
    fig,axes=plt.subplots(3,1,figsize=(9,5.3),sharex=True)
    for ax,values,label,color in zip(axes,[truth,held,pulses(held)],['Original training class','Alternative training class','Required output pulses'],['#315c9b','#008b72','#a66c00']):
        ax.step(np.arange(len(truth)),(values==2).astype(int),where='post',color=color,lw=2)
        ax.set_yticks([0,1],['NONE','BIT 1']);ax.set_ylim(-.15,1.3);ax.set_title(label,loc='left',fontsize=10,pad=5)
        ax.grid(axis='x',alpha=.2)
    axes[-1].set_xlabel('Sample tick (illustrative two-bit example)');axes[-1].set_xticks([0,8,16,24,32,40])
    fig.suptitle('A held class emits one pulse; the next identical bit still needs a new onset',fontsize=11);fig.tight_layout()
    figure=root/'figures/held_bit_labels_v9.png';fig.savefig(figure,dpi=160);plt.close(fig)
    lines=['# Training labels and the causal event interface','',
        '**A training diagnostic, not a topology result or a qualification pass.**', '',
        'The receiver emits an event when a nonzero output class begins. Keeping that class asserted for one more tick does not emit another event. Therefore, requiring the raw class to return to NONE immediately is stricter than the required event stream.', '',
        'For one frozen primary-shape UART-N seed131, a retained set of6,653 training states exposed this distinction. A linear-program diagnostic found essentially zero achievable margin for the original raw-class labels. Its66 active weighted constraints involved NONE and BIT1;19 of the constrained NONE states followed a valid BIT1 by one tick. The nearest opposite-label state vectors were different, so this was not an exact state collision.', '',
        '| Training target on the same fixed states | Verified minimum margin | Retained label errors |',
        '| --- | ---: | ---: |',f"| Original one-tick event classes | {cert['verified_minimum_margin']:.3g} (numerical zero) | not separable at a positive robust margin |"]
    for v in variants:lines.append(f"| Hold bit classes for {v['extension']} additional tick(s) | {v['verified_minimum_margin']:.8f} | {v['support_errors']} |")
    lines+=['', 'Every modified complete training stream was checked: extracting pulses from the held classes produces exactly the original event sequence. START, STOP and INVALID labels are unchanged. No waveform, decoder, hidden counter, runtime filter or acceptance threshold was added.', '',
        'This rules out interpreting the earlier canonical-label obstruction as an event-interface capacity proof. It does not establish complete-message generalization: fitting a small failure set previously damaged ordinary traffic. The separate bounded full-training-pool fit failed: its expanded13,128-state support was infeasible at the requested0.001 margin, and intermediate fits damaged ordinary development traffic. The original checkpoint remains selected. This wider failure is specific to the one-tick-hold labeling and learned states; it does not prove event-interface or topology incapacity. Quantized performance is separate.', '',
        '![Class hold and identical event pulses](runs/connectivity01/figures/held_bit_labels_v9.png)', '',
        'Exact state/checkpoint hashes, primal solutions, numerical dual residuals, source snapshots and event-context rows are in `runs/connectivity01/diagnostics/margin_certificate_v8_n131/` and `bit_hold_v9_n131/`. The floating-point dual calculation is a numerical bound for one learned representation, not formal verification or a physical-topology impossibility proof.']
    (ROOT/'LABEL_DIAGNOSTIC.md').write_text('\n'.join(lines).rstrip()+'\n')
