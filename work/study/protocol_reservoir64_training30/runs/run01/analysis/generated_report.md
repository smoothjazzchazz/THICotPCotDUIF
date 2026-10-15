# Stronger training with the same 64 nodes

All twelve candidates completed 30 epochs, including three original-loss controls. The receiver architecture and original experiment are unchanged. This is a simulation of the original assumed profiles.

## Exposure

| Profile | Original ticks / updates | New transaction / nonpadding ticks | New updates | Transaction exposure / update ratio |
| --- | ---: | ---: | ---: | ---: |
| uart_n | 64,937 / 552 | 412,943 / 444,355 | 2,250 | 6.36x / 4.08x |
| uart_e | 71,488 / 600 | 398,957 / 424,813 | 2,130 | 5.58x / 3.55x |
| i2c | 75,903 / 600 | 459,385 / 467,802 | 2,820 | 6.05x / 4.70x |

Every candidate uses batch 12 and a 512-tick gradient window; state carries across chunks. The ratio compares new transaction ticks against **all** old nonpadding ticks, so idle cannot satisfy it. These are generated sample positions, not a claim every waveform substring differs. Repeated presentations equal the corresponding unique ticks multiplied by 30; padding is reported separately in exposure.json.

## Fresh final results

| Profile / seed or control | Selected epoch | Float exact / strict cases | Quantized exact / strict cases | Phrase float / quantized |
| --- | ---: | ---: | ---: | --- |
| uart_n / seed_11 | 27 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| uart_n / seed_29 | 27 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| uart_n / seed_47 | 3 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| uart_n / original_loss_11 | 15 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| uart_e / seed_11 | 3 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| uart_e / seed_29 | 3 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| uart_e / seed_47 | 3 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| uart_e / original_loss_11 | 27 | 0/10 / 0/10 | 0/10 / 0/10 | False / False |
| i2c / seed_11 | 30 | 12/12 / 0/12 | 12/12 / 0/12 | True / True |
| i2c / seed_29 | 30 | 12/12 / 0/12 | 12/12 / 0/12 | True / True |
| i2c / seed_47 | 30 | 12/12 / 12/12 | 12/12 / 12/12 | True / True |
| i2c / original_loss_11 | 30 | 12/12 / 12/12 | 12/12 / 12/12 | True / True |

Qualification: {"uart_n": false, "uart_e": false, "i2c": false}. Exact payload delivery alone does not satisfy the zero-event-error gate.

The original UART candidates returned zero bytes and had zero correctly timed STOP events. Original I2C seeds 11/47 had 10/12 byte-exact cases, seed 29 had 2/12, and all failed the strict gate. Original final data were already observed; new binary payloads, transaction phases and peer-jitter seeds are fresh, so this is a condition-matched comparison rather than identical trials.

## Training adequacy

- uart_n / seed_11: **plateau under this recipe; capacity not established**; late dev-loss change +1.1% improvement, boundary F1 +0.005, aligned-byte fraction +0.000.
- uart_n / seed_29: **training-limited / not converged**; late dev-loss change +1.5% improvement, boundary F1 +0.052, aligned-byte fraction +0.000.
- uart_n / seed_47: **training-limited / not converged**; late dev-loss change +3.7% improvement, boundary F1 -0.022, aligned-byte fraction +0.000.
- uart_n / original_loss_11: **training-limited / not converged**; late dev-loss change +3.2% improvement, boundary F1 -0.040, aligned-byte fraction +0.000.
- uart_e / seed_11: **training-limited / not converged**; late dev-loss change +1.2% improvement, boundary F1 +0.034, aligned-byte fraction +0.000.
- uart_e / seed_29: **training-limited / not converged**; late dev-loss change +1.3% improvement, boundary F1 +0.034, aligned-byte fraction +0.000.
- uart_e / seed_47: **training-limited / not converged**; late dev-loss change +4.8% improvement, boundary F1 +0.045, aligned-byte fraction +0.000.
- uart_e / original_loss_11: **plateau under this recipe; capacity not established**; late dev-loss change +1.8% improvement, boundary F1 +0.000, aligned-byte fraction +0.000.
- i2c / seed_11: **training-limited / not converged**; late dev-loss change +38.6% improvement, boundary F1 +0.036, aligned-byte fraction +0.000.
- i2c / seed_29: **training-limited / not converged**; late dev-loss change +40.1% improvement, boundary F1 +0.000, aligned-byte fraction +0.000.
- i2c / seed_47: **training-limited / not converged**; late dev-loss change +39.5% improvement, boundary F1 +0.000, aligned-byte fraction +0.000.
- i2c / original_loss_11: **training-limited / not converged**; late dev-loss change +38.9% improvement, boundary F1 +0.000, aligned-byte fraction +0.000.

These labels follow the preregistered late-window rule. Thirty epochs do not establish capacity limits. Selection uses protocol behavior; an earlier selected epoch can coexist with an improving loss at epoch 30. Epoch 12 and epoch 30, all intermediate weights, and complete Adam checkpoints are retained.

## Interpretation and limits

The intervention combines more transactions, longer credit assignment, more updates, and improved live-bus training coverage. The original-loss controls isolate loss weighting within this expanded budget; this design does not separately identify the effects of extra data versus longer windows versus matched bus timing. No failing result proves that 64 nodes cannot support the task.

Read per-class precision/recall and false events alongside byte delivery: aggregate I2C loss can hide START/STOP faults; UART cell-center predictions can remain too weak or mistimed to deliver a complete frame. Diagnostics compare teacher-tick versus nearby event logits, state saturation, and long-range STOP sensitivity at epochs 12/30. These diagnose a recipe, not a universal representational impossibility. Float/quantized final rows isolate arithmetic degradation.

A layered 64-node comparison becomes justified after retaining these baselines and either (a) continued training reaches a stable protocol-performance plateau across seeds/objectives or (b) targeted state/gradient probes expose a reproducible timing or representation weakness that layering addresses. Use the same event/timing/rejection budgets, separate new selection data, and account for every added temporal state. If this run is still improving, resume it before claiming architecture failure.

The loaded receiver has the original 1,224 learned coefficients, 64 recurrent nodes and 256 taps. No temporal memory was added at inference. Cost, finite queues, deadline failures, rejection/recovery, and disabled/no-recurrence controls remain explicit. USB receives zero fitting steps unless UART/I2C qualify and protocol sources are supplied; no hardware gate is passed.

## Evidence

- [Recipe and commands](README.md); [exposure](runs/run01/exposure.json); [preflight audit](runs/run01/audit/preflight.json).
- [Learning curves](runs/run01/analysis/learning_curves.png); [per-condition CSV](runs/run01/analysis/per_condition.csv); [convergence](runs/run01/analysis/convergence.json); [diagnostics](runs/run01/analysis/diagnostics.json).
- [Frozen hashes](runs/run01/freeze.json); [all weights and optimizer states](runs/run01/models/); [waveform traces](runs/run01/final/traces/); [phrase replay checks](runs/run01/analysis/phrase_replays.json).
- [Resource accounting](runs/run01/final/cost.json); [final manifest](runs/run01/final/manifest.json); [USB status](runs/run01/final/usb_status.json).
