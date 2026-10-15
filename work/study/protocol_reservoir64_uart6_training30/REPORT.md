# Six-seed UART: fixed shared receiver

**This training recipe did not produce a successful UART receiver.** All six seeds for each profile failed every complete valid final exchange in both float and quantized inference. UART 8E1 seed 131 produced one sequence-aligned byte out of 4,635 valid-test bytes in float; quantized inference produced none. The reserved phrase failed everywhere. Frozen I2C seed 47 and its prior original-loss control still pass through the identical receiver code.

All twelve main candidates and two matched controls finished 30 full epochs: **420 epoch weight/optimizer pairs, 30,660 updates and 182,525,280 nonpadding tick presentations**. 9/12 main runs (10/14 including controls) remain **training-limited / not converged**. This is not evidence of insufficient 64-node capacity.

## What changed and what was audited

The shared receiver is imported unchanged: 64 nodes, four incoming recurrent taps per node, one fixed 256-edge mask, six generic features, the original leaks/equations/arithmetic, event rules and one update per tick. No UART counter, frame feature, decoder, extra temporal state or boundary input was added. Controllers/transmitters keep their original protocol configurations.

Before main fitting, labels were independently reconstructed from actual cell timing, payloads, parity and malformed stops. Repeated identical bits have separate supervision pulses. Finite differences verify 512-tick gradients; online and batch decisions agree, with state continuous across chunks and transactions. Previous epoch-30 weights and actual first-STOP derivatives were inspected.

A train/dev-only pilot compared the previous initialization with .95/1.05 self-weight initializations, smaller input/nonself weights and a NONE output bias. The preregistered pooled development score selected **memory095**: input weights ×.2, nonself recurrent weights ×.1, existing self weights .95 and NONE bias .5. These are starting values of existing trainable parameters. The pilot used 192 updates and 1,179,648 presentations, separately accounted; all trials and both epochs are retained. Its weak early event signal did not establish frame success.

The main intervention changes only initialization. Training corpora, weighted loss, Adam .003, effective batch 12 and 512-tick TBPTT match the preceding 30-epoch run. The seed-11 previous-recipe controls reproduce every corresponding old epoch weight exactly. Checkpoint selection uses preregistered development protocol performance, never final results. Earlier selected epochs do not shorten training.

## Exposure per candidate

| Profile | Transaction ticks/pass | Nonpadding ticks/pass | Padding/pass | Updates | Nonpadding presentations |
| --- | ---: | ---: | ---: | ---: | ---: |
| uart_n | 412,943 | 444,355 | 12,305 | 2,250 | 13,330,650 |
| uart_e | 398,957 | 424,813 | 7,403 | 2,130 | 12,744,390 |

Repeated transaction presentations are 12,388,290 for 8N1 and 11,968,710 for 8E1; repeated padding is 369,150 and 222,090 respectively. Padding contributes no loss or transaction credit. Independent streams start cold each epoch; truncating gradients never resets state within a stream. Exposure/update budgets exactly match the previous 30-epoch experiment.

## Results by profile and seed

**Every row has 0/11 byte-exact and 0/11 strict valid exchanges in each arithmetic mode.** Each mode attempts 4,635 valid bytes. T means training-limited / not converged; P means plateau under this recipe, not a capacity limit.

| Profile / candidate | Selected epoch | Float / quantized decoded bytes | Adequacy |
| --- | ---: | ---: | --- |
| uart_n / seed_11 | 9 | 0 / 0 | T |
| uart_n / seed_29 | 3 | 0 / 0 | P |
| uart_n / seed_47 | 18 | 0 / 0 | T |
| uart_n / seed_71 | 15 | 0 / 0 | P |
| uart_n / seed_101 | 24 | 0 / 0 | T |
| uart_n / seed_131 | 24 | 0 / 0 | T |
| uart_n / previous_recipe_11 | 21 | 0 / 0 | P |
| uart_e / seed_11 | 12 | 0 / 0 | P |
| uart_e / seed_29 | 9 | 0 / 0 | T |
| uart_e / seed_47 | 6 | 0 / 0 | T |
| uart_e / seed_71 | 27 | 0 / 0 | T |
| uart_e / seed_101 | 6 | 0 / 0 | T |
| uart_e / seed_131 | 27 | 1 / 0 | T |
| uart_e / previous_recipe_11 | 3 | 0 / 0 | T |

The sole valid-test byte is 0x55 in the 512-byte pattern case. A subsequence match is not complete-frame/timing qualification. Seed 131 also emitted one byte in malformed/recovery, without recovering the exchange. All other candidates, both previous-recipe controls and all 24 disabled/no-recurrence control conditions fail byte delivery.

Final cases include the phrase, all byte values, 2,048 random bytes, 1,024-byte messages, long constants/patterns, back-to-back and gapped frames, ratio .97/1.03, jitter, combined UART timing corners, malformed stops/parity, disturbances and recovery. All sources/configs/selections were frozen before final generation. Final transaction seeds are disjoint from recorded previous final and train/dev seeds. UART cell-duration replay confirms the actual ratio/jitter/gap settings.

## Remaining failures and training adequacy

Float STOP recall across main seeds is only 7.2%–14.9% for 8N1 and 16.9%–30.0% for 8E1, with substantial false events. Complete event sequences remain unreliable. Every selected UART candidate also emits false events on the 2,048-tick cold-idle probe; none are suppressed. Recovery is 0/2 per model/mode. Deadline failures remain explicit; there were no buffer overflows.

The improved initialization retains more long-range sensitivity on the measured development frame, even after training, without solving event sequencing. This weakens an explanation based only on vanishing gradients; it does not prove sufficient memory or isolate a unique cause. Float and quantized modes both fail at protocol level; losing the one float byte does not make quantization the primary blocker.

Adequacy uses the original unrounded late-window rule: epochs 18/21/24 versus 24/27/30, tracking protocol scores and loss separately. Decreasing loss can coexist with failed exchanges. The next controlled experiment for improving runs is a separately budgeted continuation of retained checkpoints. For plateaued recipes, test a training-only repeated-bit/STOP curriculum with matched exposure. Any later architectural revision must remain generic and be demonstrated trainable for both UART and I2C. No extra main epochs or architecture changes were used here.

## Frozen I2C compatibility

| Frozen candidate | Float exact / strict | Quantized exact / strict |
| --- | ---: | ---: |
| seed_11 | 12/12 / 0/12 | 12/12 / 0/12 |
| seed_29 | 12/12 / 0/12 | 12/12 / 0/12 |
| seed_47 | 12/12 / 12/12 | 12/12 / 12/12 |
| original_loss_11 | 12/12 / 12/12 | 12/12 / 12/12 |

Seeds 11/29 retain startup false events despite exact payloads. Seed 47 and the prior original-loss control have no valid-case event errors. I2C weights were not retrained. The shared architecture hash is `25631ac2745c1222fd229d43e2cc28f2fd1018b0eb48242b1a1e19476a491bfd`; the exact receiver source hash is recorded separately.

**I2C timing interpretation:** the corrected harness forwards the jitter flag in all named jitter cases. The unchanged peer then draws each data-bit low/high duration uniformly from 8–12 ticks, replacing nominal low/high settings; it does not add jitter around 8/12 or 12/8 corners. Those inherited combined-case names therefore cover uniform jitter with different START/STOP setup durations, not corner-centered jitter. Measured spans include setup and stretching. UART combined-corner timing is independently verified as advertised.

## Costs, checks and reproduction

The unchanged receiver has 1,224 trainable coefficients (2,448 packed int16 bytes), 256 bytes for two int16 state buffers, and 1,152 sparse MACs/tick versus 4,992 in the dense NumPy code. The 8,194-byte packed tanh ROM, preprocessing/event state, controller buffers and scheduler are additional costs. The UART capacity value 32 means frames represented through scheduling, not a separate 32-byte allocation. These are logical estimates, not synthesis, silicon speed, area, power or electrical-compliance evidence.

**Verification:** 23 tests passed; all 420 epoch pairs, initializations and selections verified; four real epoch29→30 continuations reproduced weights, Adam moments and ending state exactly; all 28 UART and eight I2C phrase traces replayed exactly. Six pilot replays matched. All 3,417 protected earlier files and frozen hashes match. Plots were visually checked. No project gate or reference design changed.

- [Recipe and base commands](README.md), [selected recipe](runs/run01/recipe.json), [pilot evidence](runs/run01/investigation/pilots.json), [preflight](runs/run01/audit/preflight.json), [initial/prior frame gradients](runs/run01/audit/complete_frame_credit.json).
- [All 500 condition rows](runs/run01/analysis/all_conditions.csv), [per-event/timing detail](runs/run01/analysis/per_condition.csv), [cold idle](runs/run01/final/cold_idle.json), [convergence](runs/run01/analysis/convergence.json), [trained frame gradients](runs/run01/analysis/trained_complete_frame_credit.json).
- [Learning curves](runs/run01/analysis/learning_curves.png), [waveform traces](runs/run01/final/traces/), [all checkpoints](runs/run01/models/), [freeze](runs/run01/freeze.json), [shared source hash](runs/run01/shared_architecture.json), [full generated report](runs/run01/analysis/generated_report.md).
- [UART timing audit](runs/run01/final/timing_audit.json), [I2C effective spans](runs/run01/final/i2c_compatibility/effective_timing.json), [seed audit](runs/run01/analysis/seed_disjointness.json), [tests](runs/run01/verification_tests.log), [checkpoint checks](runs/run01/analysis/checkpoint_verification.json).

After the README commands, reproduce the read-only post-freeze analysis and this condensed report:

```sh
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
OUT=work/study/protocol_reservoir64_uart6_training30/runs/run01
OPENBLAS_NUM_THREADS=1 PYTHONPATH=. $PY -B "$OUT/analysis/postcheck.py"
PYTHONPATH=. $PY -B "$OUT/analysis/finish_report.py"
```
