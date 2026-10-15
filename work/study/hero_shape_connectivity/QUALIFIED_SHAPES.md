# Independently confirmed physical shapes

**2 distinct physical shape(s) qualify under the unchanged float gates.** Both required shapes are established.

Qualification requires the same five of six training seeds per profile to pass every fresh condition and the prior failure regression. Every complete message and boundary must be exact, with no extra accepted messages on the declared invalid/background suite. Float and Q3.12 are scored separately. Numeric weight/leak variants are not counted as additional shapes.

| Shape | UART 8N1 | UART 8E1 | I2C | SPI0 | SPI1 | SPI2 | SPI3 | MACs/sample | Parameters |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1. Reduced readout (32 inputs/unit) | 5/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 1208 | 1278 |
| 2. Dense readout (48 inputs/unit) | 5/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 1464 | 1534 |

## 1. Reduced readout (32 inputs/unit)

Exact configuration: `srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin32_fast`.

Frozen confirmation: `readout_cost_full_v3b`, fresh family 541000000. Q3.12 qualification: **passes**; counts in profile order UART-N, UART-E, I2C, SPI0–3: 5/6, 5/6, 5/6, 6/6, 6/6, 6/6, 6/6.

Remaining float seed failures: uart_n: 47; uart_e: 47.

Remaining Q3.12 seed failures: uart_n: 47; uart_e: 47; i2c: 131.

[Fixed topology and demonstration weights](runs/connectivity01/qualified_demonstrations_v3/readout_cost_full_v3b/e0d364ce03d0/manifest.json). These are separately learned protocol configurations of one fixed physical graph. Every other seed, including failures, remains in the frozen confirmation.

![Actual directed connections](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin32_fast.png)

```sh
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 evaluate --label readout_cost_full_v3b --workers 6
```

## 2. Dense readout (48 inputs/unit)

Exact configuration: `srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense`.

Frozen confirmation: `readout_cost_full_v3b`, fresh family 541000000. Q3.12 qualification: **does not pass**; counts in profile order UART-N, UART-E, I2C, SPI0–3: 5/6, 4/6, 6/6, 6/6, 6/6, 6/6, 6/6.

Remaining float seed failures: uart_n: 47; uart_e: 47.

Remaining Q3.12 seed failures: uart_n: 47; uart_e: 47,101.

[Fixed topology and demonstration weights](runs/connectivity01/qualified_demonstrations_v3/readout_cost_full_v3b/78f53ab1bdff/manifest.json). These are separately learned protocol configurations of one fixed physical graph. Every other seed, including failures, remains in the frozen confirmation.

![Actual directed connections](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense.png)

```sh
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 evaluate --label readout_cost_full_v3b --workers 6
```

Set `PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python` and run from the repository root. Replay imports each confirmation’s immutable source and verifies its hashes. Replaying an existing family reproduces evidence; it does not create new independent evidence.

[Per-condition results, both arithmetic modes and diagnostic controls](runs/connectivity01/qualified_per_condition_v3.csv); [all qualification failures](runs/connectivity01/qualification_failures_v3.csv); [training trials and failed continuations](runs/connectivity01/training_trials.csv).

[ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md) gives equations, routes, operation counts, modeled storage, scheduling and exclusions. [READOUT_ROUTING_COMPARISON.md](READOUT_ROUTING_COMPARISON.md) explains the paired physical-edge reduction and retained training failures. [PAIRED_READOUT_RESULT.md](PAIRED_READOUT_RESULT.md) applies the preregistered cost/recovery threshold to all six paired seeds. [FOLLOWUPS.md](FOLLOWUPS.md) preserves the hypotheses and practical thresholds; [COVERAGE_V10.md](COVERAGE_V10.md) explains the startup-coverage finding; [REPRODUCE.md](REPRODUCE.md) gives training/resume commands and source manifests.

This establishes the declared receive-model tests at known nominal speed with a shared divider and separate protocol weights. It does not establish RTL, routed area/frequency, electrical compliance, on-chip training or a complete waveform-response system. USB/Ethernet extensions are untested. `clock_hz=0`; no reference-design project gate is changed.
