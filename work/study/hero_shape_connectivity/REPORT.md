# Physical-shape research and the clocked cost comparison

**2 complete multi-protocol shape(s) independently qualify.** See [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md) for current full-profile evidence. Both required shapes have been confirmed.

A narrower architectural result is independently confirmed: at 64 nodes, replacing the two later sparse layers by true directed rings and reducing their incoming routes to one aligned edge per node preserves clocked reception while reducing modeled computation and learned parameters.

| Shape | Allocation | Recurrent / inter-layer edges | MACs/tick | Learned parameters |
| --- | --- | ---: | ---: | ---: |
| sss_registered_24-20-20 | 24 → 20 → 20 | 256 / 160 | 1016 | 1086 |
| srr_registered_24-20-20_aligned1 | 24 → 20 → 20 | 136 / 40 | 776 | 846 |

The reduction is 23.62% in MACs and 22.10% in learned parameters. Both retain 216 input connections and 384 readout connections. Node state, leak operations, preprocessing, event assembly and scheduling are included separately in `runs/connectivity01/costs.json`. The shared 8,194-byte activation LUT and assembly storage do not shrink; these are not measured chip-area or frequency savings.

## Fresh confirmation 02

Each valid timing condition has at least 1,000 complete messages, including all byte values, constant/alternating patterns, random payloads, and a 1,024-byte message where applicable. Gates include exact boundaries, malformed rejection, cold/midstream startup, long idle and recovery. Frozen weights preceded seed-family 191000000 generation. Float and Q3.12 integer replay are separate.

| Shape | Profile | Float pass / 6 | Integer pass / 6 | Post-fit no recurrence / 1 |
| --- | --- | ---: | ---: | ---: |
| sss_registered_24-20-20 | i2c | 6 | 6 | 0 |
| sss_registered_24-20-20 | spi0 | 6 | 6 | 1 |
| sss_registered_24-20-20 | spi1 | 6 | 6 | 0 |
| sss_registered_24-20-20 | spi2 | 6 | 6 | 1 |
| sss_registered_24-20-20 | spi3 | 6 | 6 | 0 |
| srr_registered_24-20-20_aligned1 | i2c | 6 | 6 | 0 |
| srr_registered_24-20-20_aligned1 | spi0 | 6 | 6 | 1 |
| srr_registered_24-20-20_aligned1 | spi1 | 6 | 6 | 0 |
| srr_registered_24-20-20_aligned1 | spi2 | 6 | 6 | 0 |
| srr_registered_24-20-20_aligned1 | spi3 | 6 | 6 | 0 |

Complete condition counts are in [per_condition.csv](runs/connectivity01/per_condition.csv); every prediction tick and message outcome remains under `confirmations/clocked_cost02/results`. All six seeds are 11,29,47,71,101,131. UART is absent from this scoped confirmation, not counted as passed.

Confirmation 01 is preserved: all complete messages recovered, but cold-start false STOP events caused SPI1 boundary failures (SSS seeds 47/131; SRR-aligned1 seed11). Both shapes then received the same 60-epoch SPI1 exposure, fixed those development-visible errors, and were frozen again before independent confirmation 02. No startup grace or threshold relaxation was introduced.

## What the comparisons teach

- The five requested connectivity patterns and both inter-layer schedules reached exact clocked development message recovery after corrected training coverage. They did not produce a meaningful UART advance. All failures and improving runs are retained.
- Sparse feedback was not required at every layer for clocked reception. Two actual closed rings with lighter inter-layer routing retain the tested behavior at lower operation/parameter cost.
- Tight setup was a training-coverage failure in the previous recipe. Historical SPI1/SPI3 readout ablations implicate stale middle-layer contributions, while retraining the full sparse baseline resolves the condition.
- Last-layer-only registered readout has a demonstrable information-delay limitation for one-tick setup. The tested all-node readout avoids that limitation.
- UART difficulty is not explained simply by absent long memory. Some trained states retain distinctions for 160 ticks but still fail complete messages; simple-frame traces show drifting/missing sampling pulses. Loss rebalance, longer training windows, allocation/input access, generic readout factorization, curriculum and single-port circulation trials are preserved as training/architecture diagnostics, not capacity proofs.

See [FOLLOWUPS.md](FOLLOWUPS.md) for the hypotheses, advance thresholds and decisions recorded before each comparison. Learning curves and optimizer checkpoints remain in every model directory. No candidate is called architecturally impossible.

The current ledger contains 2310 recipe/shape/profile/seed fits. [training_trials.csv](runs/connectivity01/training_trials.csv) and [training_per_condition.csv](runs/connectivity01/training_per_condition.csv) retain failures and exposure counts. Forked rescue histories include their starting exposure, so summing those counts would double-count earlier work.

![UART learning curves](runs/connectivity01/figures/uart_learning_curves.png)

## Fixed topology and demonstrations

![sss_registered_24-20-20 connections](runs/connectivity01/figures/sss_registered_24-20-20.png)

![srr_registered_24-20-20_aligned1 connections](runs/connectivity01/figures/srr_registered_24-20-20_aligned1.png)

The diagrams show actual graph edges, not placement. Exact masks and seed-11 clocked demonstration weights are in `runs/connectivity01/demonstration_configs`; every other seed is retained in the immutable confirmation snapshot. Seed 11 is a consistent example, not a selectively chosen best seed. These are trained recurrent networks; no on-chip training, hardware compliance, STA, electrical or reference-design gate is claimed. `clock_hz` stays 0.

## Reproduce and resume

Use the bundled study Python and one BLAS thread. Initial launch refuses an existing run directory. Repeating a completed batch is idempotent; checkpoints include Adam moments and exposure counts.

```sh
export OPENBLAS_NUM_THREADS=1
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
OUT=work/study/hero_shape_connectivity/runs/reproduction01
$PY -B -m work.study.hero_shape_connectivity.run launch --output "$OUT"
$PY -B -m work.study.hero_shape_connectivity.run train --output "$OUT" --epochs 30 --label initial30 --workers 12
```

Exact batch job lists, source snapshots, environment, corpus seeds and historical hashes are filed in the run. For confirmation replay, use its frozen `source` package, its frozen weights, and saved waveform files. Current source changes must not be substituted silently for a frozen snapshot.

**Full-profile qualification:** see QUALIFIED_SHAPES.md and its immutable fresh/regression records. Current control comparisons and preserved failed trials are recorded separately. USB/Ethernet extensions remain untested.
