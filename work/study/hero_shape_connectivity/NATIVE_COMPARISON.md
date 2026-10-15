# Matched native structural comparison

Original2,304-group development, not qualification or the later8,864-group suite. All configurations use the same native-v3 data schedule,512-tick training windows, original seed set and event interface. The first120 epochs have identical exposure per profile. Matched fixed-ring initialization retains the16-node fast ring; other weights are trained off chip. First-gate/control no-parity now extends to all six seeds; direct native parity uses the initial three, with later N-to-E transfer reported separately. See CURRENT_FINDINGS.md for expanded development.

| Shape | Nonlinear units / states | MACs | Parameters | Profile | Completed / planned | Original-suite passes |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 64 / 64 | 840 | 910 | uart_n | 6/6 | 1/6 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 64 / 64 | 840 | 910 | uart_e | 6/6 | 0/6 |
| srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 64 / 64 | 840 | 910 | uart_n | 6/6 | 0/6 |
| srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 64 / 64 | 840 | 910 | uart_e | 6/6 | 0/6 |
| srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 56 / 56 | 656 | 718 | uart_n | 6/6 | 2/6 |
| srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 56 / 56 | 656 | 718 | uart_e | 6/6 | 0/6 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | 48 / 48 | 600 | 654 | uart_n | 6/6 | 2/6 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | 48 / 48 | 600 | 654 | uart_e | 6/6 | 0/6 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | 64 / 48 | 696 | 766 | uart_n | 6/6 | 0/6 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | 64 / 48 | 696 | 766 | uart_e | 6/6 | 0/6 |
| zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 64 / 64 | 744 | 814 | uart_n | 3/3 | 0/3 |
| zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | 64 / 64 | 744 | 814 | uart_e | 3/3 | 0/3 |
| srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 | 64 / 64 | 696 | 766 | uart_n | 3/3 | 0/3 |
| srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 | 64 / 64 | 696 | 766 | uart_e | 3/3 | 0/3 |
| srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 | 64 / 64 | 696 | 766 | uart_n | 3/3 | 1/3 |
| srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 | 64 / 64 | 696 | 766 | uart_e | 3/3 | 1/3 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense | 64 / 48 | 1464 | 1534 | uart_n | 6/6 | 5/6 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense | 64 / 48 | 1464 | 1534 | uart_e | 6/6 | 2/6 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 | 64 / 48 | 824 | 894 | uart_n | 3/3 | 2/3 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 | 64 / 48 | 824 | 894 | uart_e | 3/3 | 0/3 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 | 48 / 48 | 600 | 654 | uart_n | 6/6 | 2/6 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 | 48 / 48 | 600 | 654 | uart_e | 3/3 | 0/3 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first | 64 / 48 | 696 | 766 | uart_n | 6/6 | 5/6 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first | 64 / 48 | 696 | 766 | uart_e | 3/3 | 1/3 |

High-rate collapse is a training-recipe limitation. Lower-rate continuation is recorded separately under `phase_native_refine_v3`, beginning at each configuration’s own best checkpoint; it does not overwrite these matched first-stage results. The meaningful-result and full qualification thresholds remain in README.md/FOLLOWUPS.md.

Input, state and gate counts differ in the reduced candidates and are explicit above. The mixed slow ring costs 48 tanh proposals plus 16 sigmoid gates; its fixed-leak control has 48 proposals. All connection masks and gate edges are serialized under `runs/connectivity01/shapes/`.

## Declared lower-rate continuation

Each unresolved native120 fit receives60 epochs at0.0001 from its own best checkpoint. Passing fits are retained with zero additional training. This is the same conditional training rule, not identical additional exposure for successful and unsuccessful fits. Later extensions are shown separately.

| Shape | Profile | Completed continuations | Whole-suite passes | Exact-message range | Boundary-error range |
| --- | --- | ---: | ---: | ---: | ---: |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6 | 4/6 | 98.090–100.000% | 0–273 |
| srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6 | 0/6 | 5.252–99.783% | 10–60098 |
| srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6 | 1/6 | 6.120–100.000% | 0–103105 |
| srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6 | 0/6 | 88.715–99.870% | 10–1586 |
| srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 6 | 2/6 | 90.972–100.000% | 0–2476 |
| srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 6 | 0/6 | 0.391–99.913% | 0–85966 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_n | 6 | 2/6 | 0.477–100.000% | 0–87330 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_e | 6 | 0/6 | 0.260–99.653% | 4–104155 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_n | 6 | 2/6 | 96.398–100.000% | 0–988 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_e | 6 | 1/6 | 67.665–100.000% | 0–7013 |
| zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_n | 3 | 0/3 | 64.931–96.398% | 216–5616 |
| zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 | uart_e | 3 | 0/3 | 2.908–58.247% | 11365–66160 |
| srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 | uart_n | 3 | 1/3 | 96.224–100.000% | 0–532 |
| srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 | uart_e | 3 | 0/3 | 97.917–99.392% | 73–1277 |
| srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 | uart_n | 3 | 1/3 | 99.219–100.000% | 0–50 |
| srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 | uart_e | 3 | 1/3 | 96.007–100.000% | 0–1756 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense | uart_n | 6 | 5/6 | 99.957–100.000% | 0–60 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense | uart_e | 6 | 5/6 | 99.609–100.000% | 0–95 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 | uart_n | 3 | 2/3 | 99.436–100.000% | 0–147 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 | uart_e | 3 | 0/3 | 98.915–99.523% | 130–245 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 | uart_n | 6 | 3/6 | 96.354–100.000% | 0–942 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 | uart_e | 3 | 0/3 | 94.661–99.392% | 0–1180 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first | uart_n | 6 | 6/6 | 100.000–100.000% | 0–0 |
| srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first | uart_e | 3 | 1/3 | 1.649–100.000% | 0–86034 |

Additional training on still-improving comparisons:

| Shape | Profile / seed | Refinement epochs | Exact messages | Boundary errors |
| --- | --- | ---: | ---: | ---: |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_e / 29 | 240 | 0.347% | 87121 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_e / 29 | 120 | 0.347% | 87121 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_e / 29 | 360 | 0.347% | 87121 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 | uart_e / 29 | 600 | 0.347% | 87121 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_e / 29 | 240 | 93.793% | 929 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_e / 29 | 120 | 82.161% | 3191 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_e / 29 | 360 | 96.094% | 648 |
| srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last | uart_e / 29 | 600 | 97.873% | 208 |

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2_native_v3_curves.png)

![srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 directed graph](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)

![srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2_native_v3_curves.png)

![srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 directed graph](runs/connectivity01/figures/srr_current_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)

![srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2_native_v3_curves.png)

![srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2 directed graph](runs/connectivity01/figures/srr_registered_16-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_native_v3_curves.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2 directed graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last raw learning curves](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last_native_v3_curves.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last directed graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_mixed_last.png)

![zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2_native_v3_curves.png)

![zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2 directed graph](runs/connectivity01/figures/zrr_registered_24-16-24_port_fanin4_leak1.0,1.0,0.125_both2.png)

![srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2_native_v3_curves.png)

![srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2 directed graph](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_injectlanes_roundrobin_leak1.0,1.0,0.125_both2.png)

![srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2_native_v3_curves.png)

![srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2 directed graph](runs/connectivity01/figures/srr_registered_24-16-24_port_fanin4_injectlanes_banks_leak1.0,1.0,0.125_both2.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense raw learning curves](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense_native_v3_curves.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense directed graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 raw learning curves](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8_native_v3_curves.png)

![srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8 directed graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin8.png)

![srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 raw learning curves](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_native_v3_curves.png)

![srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2 directed graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2.png)

![srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first raw learning curves](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first_native_v3_curves.png)

![srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first directed graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first.png)
