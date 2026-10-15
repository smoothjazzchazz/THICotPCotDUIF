# Training labels and the causal event interface

**A training diagnostic, not a topology result or a qualification pass.**

The receiver emits an event when a nonzero output class begins. Keeping that class asserted for one more tick does not emit another event. Therefore, requiring the raw class to return to NONE immediately is stricter than the required event stream.

For one frozen primary-shape UART-N seed131, a retained set of6,653 training states exposed this distinction. A linear-program diagnostic found essentially zero achievable margin for the original raw-class labels. Its66 active weighted constraints involved NONE and BIT1;19 of the constrained NONE states followed a valid BIT1 by one tick. The nearest opposite-label state vectors were different, so this was not an exact state collision.

| Training target on the same fixed states | Verified minimum margin | Retained label errors |
| --- | ---: | ---: |
| Original one-tick event classes | -4.06e-10 (numerical zero) | not separable at a positive robust margin |
| Hold bit classes for 1 additional tick(s) | 0.01076776 | 0 |
| Hold bit classes for 2 additional tick(s) | 0.01076776 | 0 |

Every modified complete training stream was checked: extracting pulses from the held classes produces exactly the original event sequence. START, STOP and INVALID labels are unchanged. No waveform, decoder, hidden counter, runtime filter or acceptance threshold was added.

This rules out interpreting the earlier canonical-label obstruction as an event-interface capacity proof. It does not establish complete-message generalization: fitting a small failure set previously damaged ordinary traffic. The separate bounded full-training-pool fit failed: its expanded13,128-state support was infeasible at the requested0.001 margin, and intermediate fits damaged ordinary development traffic. The original checkpoint remains selected. This wider failure is specific to the one-tick-hold labeling and learned states; it does not prove event-interface or topology incapacity. Quantized performance is separate.

![Class hold and identical event pulses](runs/connectivity01/figures/held_bit_labels_v9.png)

Exact state/checkpoint hashes, primal solutions, numerical dual residuals, source snapshots and event-context rows are in `runs/connectivity01/diagnostics/margin_certificate_v8_n131/` and `bit_hold_v9_n131/`. The floating-point dual calculation is a numerical bound for one learned representation, not formal verification or a physical-topology impossibility proof.
