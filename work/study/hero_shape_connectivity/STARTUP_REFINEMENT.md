# Startup and training-coverage diagnostics

**Ongoing research; zero complete multi-protocol shapes qualify.** These results are development/training diagnostics, not fresh confirmation.

The enlarged development suite contains8,864 valid groups/profile: the original2,304,4,000 sustained-corner groups, and2,560 independent known-idle/error-startup groups. No previous condition was removed. Training and development families are distinct.

## Completed blocks

| Recipe | Profile / seed | Budget / selected round | Exact messages | Boundaries | Failed complete training-startup cases |
| --- | --- | ---: | ---: | ---: | ---: |
| phase_startup_margin_v5 | uart_n / 11 | 0 / 0 | 8864/8864 | 0 | 0/320 |
| phase_startup_margin_v5 | uart_n / 29 | 0 / 0 | 8864/8864 | 0 | 0/320 |
| phase_startup_margin_v5 | uart_n / 47 | 32 / 4 | 8855/8864 | 71 | 7/320 |
| phase_startup_margin_v5 | uart_n / 71 | 32 / 24 | 8858/8864 | 9 | 2/320 |
| phase_startup_margin_v5 | uart_n / 101 | 32 / 0 | 8863/8864 | 2 | 0/320 |
| phase_startup_margin_v5 | uart_n / 131 | 32 / 12 | 8860/8864 | 9 | 0/320 |
| phase_startup_margin_v5 | uart_e / 11 | 32 / 0 | 8864/8864 | 2 | 0/320 |
| phase_startup_margin_v5 | uart_e / 29 | 0 / 0 | 8864/8864 | 0 | 0/320 |
| phase_startup_margin_v5 | uart_e / 47 | 32 / 0 | 8863/8864 | 2 | 1/320 |
| phase_startup_margin_v5 | uart_e / 71 | 32 / 0 | 8861/8864 | 107 | 50/320 |
| phase_startup_margin_v5 | uart_e / 101 | 32 / 16 | 8864/8864 | 0 | 0/320 |
| phase_startup_margin_v5 | uart_e / 131 | 32 / 0 | 8861/8864 | 5 | 0/320 |
| phase_startup_readout_v5 | uart_n / 47 | 64 / 0 | 8855/8864 | 71 | 7/320 |
| phase_startup_readout_v5 | uart_e / 47 | 64 / 32 | 8863/8864 | 2 | 1/320 |
| phase_startup_core_v5 | uart_n / 47 | 64 / 16 | 8864/8864 | 0 | 0/320 |
| phase_startup_core_v5 | uart_e / 47 | 64 / 0 | 8863/8864 | 2 | 1/320 |

The margin fit updates all six affine output rows while holding every state parameter fixed. Its unstable iterates and solver diagnostics are retained. The separate cold-prefix pair uses the same512-tick episodes, anchors, class weights and180,224 optimized ticks per round; only permission to change state parameters differs. The16-node fast ring remains protected in both arms.

## Causal observations

- Frozen N47 cold traces first call a true STOP a data bit at tick168; later alignment errors follow. Sampling before that point is correct.
- Adding16 observable high ticks before each of seven failing N47 training files fixes every tested message/boundary. It also fixes the tested N71 cold failure. E47/E101 failures persist with up to1,024 extra ticks. These changed-input probes never replace a required cold-start test.
- N47 state refinement selects round16 with8,864/8,864 development groups and all320 complete training-startup cases passing. The matched output-only fit leaves nine development groups failing. This is a seed-specific parameter-learning result, not a topology-dependent advance or capacity proof.
- The same cold-prefix state refinement worsens parity E47 in later rounds; its earlier checkpoint is preserved. Do not generalize the N47 fix to all UART failures.

## Matched cold-prefix learning curves

![Matched parameter-learning curves](runs/connectivity01/figures/startup_parameter_comparison_v5.png)

Per-case training audits, immutable source/checkpoint hashes, all iterations and selected weights are stored under the corresponding model folders. Frozen full_shape_v2a remains a failed confirmation. The next confirmation will retain all original gates, add independent startup cases, and separately replay the corrected prior corpus as a regression suite.
