# UART research progress

**Historical development ledger; these results are not fresh confirmation.** Current qualification is recorded in [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md).

The independently confirmed clocked resource result is in [REPORT.md](REPORT.md). This page preserves the development stages and their failures, separately from later full-profile confirmation.

On the earlier corrected2,304-group development suite, the primary64-node registered graph reaches **uart_n: 6/6, uart_e: 5/6**. The enlarged8,864-group suite exposes additional failures; see [CURRENT_FINDINGS.md](CURRENT_FINDINGS.md). This earlier same-seed checkpoint portfolio is not a matched topology ranking or fresh confirmation. Distributions below remain separate.

## Best available development checkpoints

Selection across recipes is exploratory. It uses worst-condition complete-message recovery first, followed by overall recovery and errors, exactly as the training selector does. Recipes and exposure differ; this table is not a matched architectural comparison. Missing seeds remain missing.

| Shape | Profile | Seeds available | Exact-message range | All messages exact | Entire development suite passes |
| --- | --- | ---: | ---: | ---: | ---: |
| srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 99.15–100.00% | 2/6 | 0/6 |
| srr_registered_24-16-24_one_port_leak1.0,1.0,0.125_both1 | uart_n | 3/6 | 0.00–98.73% | 0/3 | 0/3 |
| srr_registered_24-16-24_one_port_leak1.0,1.0,0.125_both1 | uart_e | 3/6 | 0.00–96.61% | 0/3 | 0/3 |
| srr_registered_24-16-24_one_port_leak1.0,1.0,0.125_top1 | uart_n | 6/6 | 0.00–98.31% | 0/6 | 0/6 |
| srr_registered_24-16-24_one_port_leak1.0,1.0,0.125_top1 | uart_e | 6/6 | 0.00–97.88% | 0/6 | 0/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1 | uart_n | 6/6 | 99.58–100.00% | 5/6 | 4/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1 | uart_e | 6/6 | 95.76–100.00% | 3/6 | 2/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 100.00–100.00% | 6/6 | 6/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 100.00–100.00% | 6/6 | 5/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2_firstfanin2 | uart_n | 6/6 | 97.88–100.00% | 3/6 | 3/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2_firstfanin2 | uart_e | 6/6 | 87.29–100.00% | 2/6 | 1/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_top1 | uart_n | 6/6 | 4.24–98.31% | 0/6 | 0/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_top1 | uart_e | 6/6 | 7.63–97.46% | 0/6 | 0/6 |

## Extended development coverage

This independently generated development distribution adds long continuous payloads and cold mid-frame startup. Scores remain separate from original development and confirmation. Selection across recorded recipes is exploratory; it is not a matched comparison.

| Shape | Profile | Seeds | Exact-message range | Entire suite passes | Failing seeds |
| --- | --- | ---: | ---: | ---: | --- |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1 | uart_e | 6/6 | 91.94–100.00% | 1/6 | 11,29,47,71,131 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1 | uart_n | 6/6 | 97.18–100.00% | 4/6 | 71,131 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1_bridge_first4 | uart_e | 3/6 | 93.15–99.60% | 0/3 | 11,29,47 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1_bridge_middle4 | uart_e | 3/6 | 97.98–100.00% | 0/3 | 11,29,47 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 100.00–100.00% | 6/6 | none |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 100.00–100.00% | 6/6 | none |

Selected recipes, epochs, conditions and source histories are in `best_extended_development_checkpoints.json`; all latest recipe results, including failed controls, are in `all_extended_development_trials.json`.


Every selected checkpoint, recipe, six-seed failure and exposure count is recorded in `runs/connectivity01/best_development_checkpoints.json`. No missing profile or failed seed is silently counted as a pass.

## Causal findings

- A single ring inlet with registered feedback can learn substantial UART reception; the corresponding no-feedback control remained near zero under the paired auxiliary-training recipe.
- Four upstream sources at the same ring inlet improve some initializations, especially with returns from both rings, but six-seed reliability remains unresolved.
- In wider-inlet/both-return seed11 at 600 epochs, 20 extra events occur half a bit period from valid samples even though the auxiliary heads identify the correct phase at those ticks. That motivates the paired extra-return experiment; it is not a proof that the node count is insufficient.
- A generic pulse-rearm diagnostic does not fix those isolated extra events. Its output policy was not adopted.
- Leak learning and independent training banks are separately recorded recipe comparisons. Auxiliary timing heads are training tools only; deployed inference retains the same nine generic features, neural states and six event logits.

- Fixed middle-ring gains improve several seeds that struggled when those gains were trained. The declared portfolio gives every seed both off-chip recipes and retains its own selected weights. This changes the fitting program, not the physical graph.

## Resource limits

All physical graph costs are in `runs/connectivity01/all_shape_costs.json`. Counts include input, recurrent, return, inter-layer and readout connections. Learned weights/biases, leak storage, state banks, activation LUT and arithmetic are separate. The known numeric-storage subtotal excludes unsynthesized assembler/control and preprocessing/divider registers; it is not a measured silicon total. The confirmed 23.62% MAC reduction becomes 20.98% when the unchanged leak multiplications are included, and only 4.47% in the known numeric-storage subtotal because the shared LUT dominates. Wire length, placement, timing closure and area remain unmeasured.

## Corrected broad development suite

Version 2 verifies every valid payload after an explicit observable cold-start synchronization interval. These are development results, not fresh confirmation. Interrupted version-1 precision and margin trials remain preserved and cannot establish an architecture limit. See [CONFIRMATIONS.md](CONFIRMATIONS.md) for the startup oracle audit.

| Shape | Profile | Completed seeds | All development gates pass | Remaining seed failures |
| --- | --- | ---: | ---: | --- |
| srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 0/6 | 11,29,47,71,101,131 |
| srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 1/6 | 11,29,47,101,131 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 | uart_e | 3/6 | 0/3 | 11,29,47 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 | uart_n | 6/6 | 3/6 | 11,47,71 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first | uart_e | 3/6 | 1/3 | 29,47 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first | uart_n | 6/6 | 6/6 | none |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 0/6 | 11,29,47,71,101,131 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 2/6 | 11,29,47,71 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_e | 6/6 | 1/6 | 29,47,71,101,131 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_n | 6/6 | 2/6 | 11,29,47,101 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense | uart_e | 6/6 | 5/6 | 47 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense | uart_n | 6/6 | 5/6 | 47 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 | uart_e | 3/6 | 0/3 | 11,29,47 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 | uart_n | 3/6 | 2/3 | 47 |
| srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 0/6 | 11,29,47,71,101,131 |
| srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 2/6 | 11,29,71,101 |
| srr_registered_24-16-24_port_distfast4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 3/6 | 29,71,131 |
| srr_registered_24-16-24_port_distfast4_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 4/6 | 71,131 |
| srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 | uart_e | 3/6 | 1/3 | 29,47 |
| srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 | uart_n | 3/6 | 1/3 | 11,47 |
| srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 | uart_e | 3/6 | 0/3 | 11,29,47 |
| srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 | uart_n | 3/6 | 1/3 | 29,47 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1 | uart_e | 6/6 | 1/6 | 11,47,71,101,131 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1 | uart_n | 6/6 | 1/6 | 11,29,47,71,131 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 5/6 | 71 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 6/6 | none |
| srr_registered_24-16-24_port_fastfanin16_leak1.0,1.0,0.125_both2 | uart_e | 6/6 | 3/6 | 29,71,131 |
| srr_registered_24-16-24_port_fastfanin16_leak1.0,1.0,0.125_both2 | uart_n | 6/6 | 4/6 | 71,131 |
| srr_registered_24-16-24_port_firstlast4_leak1.0,1.0,1.0_both2 | uart_e | 3/6 | 0/3 | 11,29,47 |
| srr_registered_24-16-24_port_firstlast4_leak1.0,1.0,1.0_both2 | uart_n | 3/6 | 0/3 | 11,29,47 |
| srr_registered_25-16-23_port_firstlast4_leak1.0,1.0,1.0_both2 | uart_e | 3/6 | 0/3 | 11,29,47 |
| srr_registered_25-16-23_port_firstlast4_leak1.0,1.0,1.0_both2 | uart_n | 3/6 | 0/3 | 11,29,47 |
| zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 3/6 | 0/3 | 11,29,47 |
| zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 3/6 | 0/3 | 11,29,47 |

Exact conditions, selected recipes, checkpoints and exposure histories are in `best_verified_development_checkpoints.json`. Pending seeds are not counted as successful.

## First fresh UART confirmation: failed

The 600-epoch fixed-ring configurations were frozen before generating family 211000000. This first snapshot has float replay only; later float/integer replays are listed in CONFIRMATIONS.md. Its UART midstream payload contract was subsequently found invalid, so the whole suite cannot establish qualification. The numeric valid-timing counts below remain preserved, and no seed passed even the original replay. These samples are never reused for training.

| Seed | Valid timing messages exact | Worst valid condition | Boundary errors, all cases | Entire suite passes |
| ---: | ---: | ---: | ---: | --- |
| 101 | 6995/7000 | 99.80% | 71 | False |
| 11 | 6996/7000 | 99.60% | 46 | False |
| 131 | 6343/7000 | 74.50% | 2327 | False |
| 29 | 3008/7000 | 11.10% | 30348 | False |
| 47 | 6907/7000 | 95.00% | 145 | False |
| 71 | 6955/7000 | 97.10% | 210 | False |

Rare long-message and corner errors, exact-boundary failures, and startup/recovery failures all remain visible. New training/development families 223000000/224000000 address those coverage gaps; future confirmation must use a different fresh family.

## Return-path topology diagrams

![srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2](runs/connectivity01/figures/srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)

![srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2](runs/connectivity01/figures/srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)

![srr_registered_24-16-16_port_fanin4_leak0.95,1.0,0.125_both2_parent64_gated8](runs/connectivity01/figures/srr_registered_24-16-16_port_fanin4_leak0.95,1.0,0.125_both2_parent64_gated8.png)

![srr_registered_24-16-16_port_fanin4_leak0.95,1.0,0.125_both2_parent64_plain56](runs/connectivity01/figures/srr_registered_24-16-16_port_fanin4_leak0.95,1.0,0.125_both2_parent64_plain56.png)

![srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2.png)

![srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2.png)

![srr_registered_24-16-24_port_fanin4_leak0.95,1.0,0.125_both2](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak0.95,1.0,0.125_both2.png)

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1.png)

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1_bridge_first4](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1_bridge_first4.png)

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1_bridge_middle4](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both1_bridge_middle4.png)

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2_firstfanin2](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2_firstfanin2.png)

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_top1](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_top1.png)

![zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2](runs/connectivity01/figures/zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)
