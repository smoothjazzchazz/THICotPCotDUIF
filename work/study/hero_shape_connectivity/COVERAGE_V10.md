# Balanced initial-state coverage

**Training-coverage result for one learned configuration; not a fresh topology result.**

The dense-readout64 parity configuration for seed101 passed all320 prior startup training cases, but missed one first-byte STOP in expanded development. A separate, balanced training grid exposed more cases with the same general risk: zero neural state followed by a short initial idle and varied first-byte timing.

The grid crosses every idle length17–48, every byte0–255 and all seven existing UART timing conditions:57,344 independent one-byte streams. A separate seeded phase/jitter draw is used for each combination. All generated payloads pass the independent waveform parser. No development or confirmation waveform is copied.

| Measurement | Before grid fitting | Selected after fitting |
| --- | ---: | ---: |
| Training-grid cases with wrong event pulses | 43/57,344 | 0/57,344 |
| Training-grid boundary errors | 30 | 0 |
| Expanded-development exact messages | 8,863/8,864 | 8,864/8,864 |
| Expanded-development boundary errors | 1 | 0 |

All43 original grid failures were independently reproduced by the scalar inference kernel. The selected checkpoint is also replayed through the scalar kernel on the whole development suite and through all320 startup training files. Grid metrics report event pulses separately from raw training classes.

Only the existing six affine output rows changed. The48 recurrent states,16 nonlinear readout units, their parameters, routes and configured leaks stayed fixed. Selection retained round1 of2 completed rounds; every iterate and original source remains filed. This supports a coverage explanation for this configuration. It does not prove that every seed or graph has the same failure mechanism.

![Balanced startup coverage failures](runs/connectivity01/figures/startup_grid_v10_failures.png)

Training families391000000/392000000, full data/state hashes, the source checkpoint, support constraints, optimizer histories and per-case audits are recorded under `runs/connectivity01/models/phase_grid_margin_v10/`. The frozen batch is `grid_margin_v10_e101_8`; use `resume_batch grid_margin_v10_e101_8 --entry grid_margin_v10 --workers 1` only if interrupted. New independent confirmation remains mandatory.
