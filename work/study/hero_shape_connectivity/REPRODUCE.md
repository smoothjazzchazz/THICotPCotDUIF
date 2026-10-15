# Reproduce and continue the isolated study

For the final readout-routing comparison, see the v14–v19 replay table at the end
and [READOUT_ROUTING_COMPARISON.md](READOUT_ROUTING_COMPARISON.md). The original
24→20→20 comparison and its smaller clocked-only result remain reproducible below.

Run from the repository root. Historical studies and released files are inputs
only. `connectivity01` is the recorded run; choose a new directory to reproduce.

```sh
export OPENBLAS_NUM_THREADS=1
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
$PY -B -m work.study.hero_shape_connectivity.build
$PY -B -m unittest work.study.hero_shape_connectivity.test_study -v
$PY -B -m work.study.hero_shape_connectivity.reproduce \
  --output work/study/hero_shape_connectivity/runs/clocked_reproduction01 \
  --workers 8
```

The reproduction entry point trains both 64-node shapes with six seeds, uses
30 epochs for each clocked profile and 60 for SPI1, freezes them, then generates
the recorded confirmation family and evaluates float, Q3.12 and post-fit
no-recurrence controls separately. Reusing that family is exact reproduction,
not new independent evidence. Pass `--confirmation-seed-family` with an unused
family for a new confirmation after freezing the trained selection.

The original requested ten-architecture screen is independently reproducible:

```sh
OUT=work/study/hero_shape_connectivity/runs/connectivity_reproduction01
$PY -B -m work.study.hero_shape_connectivity.run launch --output "$OUT"
$PY -B -m work.study.hero_shape_connectivity.run train --output "$OUT" \
  --seeds 11,29,47 --epochs 30 --label initial30 --workers 8
```

Every subsequent batch has `<label>_jobs.json`, `<label>_source_hashes.json`,
`batch_sources/<label>/`, a log and a completion/failure ledger. Job tuples give
the output directory, exact topology constructor, profile, seed, target total
epochs and recipe. Source snapshots distinguish changes made during exploration.
Each epoch saves weights, optimizer moments, leak settings, auxiliary optimizer
state, exposure counts and the end-of-stream state. The next epoch begins a
new independent stream, exactly as in the original run; messages and chunks
within an epoch never reset the receiver.

To resume an existing ordinary batch, repeat its original `run train` command
with the same label and fields. Completed jobs return their recorded result;
unfinished jobs resume from the last complete epoch. Use a new label for a
larger target epoch count. Do not send the readout-only diagnostic to the
ordinary trainer; it has its own CLI and checkpoints.

For the main UART lead:

```sh
$PY -B -m work.study.hero_shape_connectivity.run train \
  --candidates work/study/hero_shape_connectivity/wider_port_candidates.json \
  --profiles uart_e --seeds 11,29,47 --epochs 600 \
  --recipe phase_circulation --label wider_port600 --workers 6
$PY -B -m work.study.hero_shape_connectivity.warm_transfer \
  --candidates work/study/hero_shape_connectivity/wider_port_candidates.json
$PY -B -m work.study.hero_shape_connectivity.run train \
  --candidates work/study/hero_shape_connectivity/wider_port_candidates.json \
  --profiles uart_n,uart_e --seeds 11,29,47 --epochs 300 \
  --recipe phase_transfer --label wider_transfer300 --workers 4
```

The second three seeds use labels `wider_port_extra600` and
`wider_transfer_extra300`. Keep seed identities through transfer; never replace
a failed seed with a successful seed's weights. Transfer is off-chip pretraining
on the same graph and records the source checkpoint hash and prior exposure.

The extra-return comparison uses `phase_route_candidates.json`, `route_transfer`
and recipe `phase_route`; source models are the wider/both-return 600-epoch 8E1
checkpoints. New physical edges start at zero and the shared initial prediction
is checked before fitting. Full commands are reconstructible from the
`phase_route300` and `phase_route_extra300` job lists.

Auxiliary training heads, trajectory capture and label generators are not
receiver hardware. `runtime.Receiver` uses only generic sampled features,
the frozen physical graph, profile weights/leaks, and causal event output.
Demonstration configurations must include fitted leaks when present.

Frozen confirmations contain their own source package, weight hashes and data
hashes. Use that package for exact replay; do not silently substitute current
exploration code. `verify preservation` checks historical files and frozen
artifacts; `verify replay` checks exact optimizer continuation. Original failed
confirmation 01 and all unsuccessful training trials remain intact.

The later startup audit is mandatory reading before interpreting UART results:
[CONFIRMATIONS.md](CONFIRMATIONS.md). Historical cold-cut tests could label a
message valid while the reference parser remained out of phase. Those records
are preserved, and new work uses verified observable synchronization:

```sh
$PY -B -m work.study.hero_shape_connectivity.startup_audit
$PY -B -m work.study.hero_shape_connectivity.precision_data_v2 --epochs 120
$PY -B -m work.study.hero_shape_connectivity.precision_refine --recipe phase_precision_v2
$PY -B -m work.study.hero_shape_connectivity.distributed_transfer \
  --recipe phase_precision_v2
$PY -B -m work.study.hero_shape_connectivity.distributed_transfer \
  --recipe phase_precision_v2 --seeds 71,101,131 \
  --label distributed_precision_v2_extra60
```

These continuation commands require the source checkpoints named in their
warm-start manifests. They are resumable commands for `connectivity01`, not
claims that a new empty directory contains those trained sources. For an
independent rerun, replay the ordered batch job/source manifests and off-chip
source selection recorded in `FOLLOWUPS.md`.

After a graph's corrected 60-epoch blocks complete, the readout refinement
applies the same rule to every seed: retain passing configurations, fit only
unresolved configurations with the next verified banks. Use separate batch
labels when dispatching profiles or graphs separately. New confirmation must
use `confirm_v2`, frozen source/weights and an unused seed family. Existing
`confirm` snapshots replay their original, preserved semantics.

The completed hard-margin pilot uses SciPy 1.17.1 installed in
`runs/connectivity01/dependencies`; it is not a receiver dependency. Its
version-1 cold-start data is affected by the audit, and that trial is not an
architecture-capacity result. The ordinary receiver/trainer continues to use
NumPy and the compiled scalar kernels.

## Mixed slow-memory and lower-rate/error-directed follow-ups

Build includes `mixed_kernel.cpp`; its three dedicated contract tests check
constant-gate agreement with the ordinary proposal graph, all parameter-gradient
types, causal chunking and an independent integer arithmetic replay.

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.build
OPENBLAS_NUM_THREADS=1 "$PY" -B -m unittest work.study.hero_shape_connectivity.test_mixed work.study.hero_shape_connectivity.test_study
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.run train --candidates work/study/hero_shape_connectivity/mixed_candidates.json --profiles uart_n,uart_e --seeds 11,29,47 --epochs 120 --recipe phase_native_v3 --workers 4 --label mixed_native_v3_120_reproduction
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.native_refine --candidates work/study/hero_shape_connectivity/wider_both2_candidate.json --profiles uart_n --workers 3 --label native_refine_n60
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.error_mining --workers 3 --rounds 56
```

The original mixed batch interleaves the two candidate jobs per profile/seed;
its exact ordered job list is `mixed_native_v3_120_jobs.json`. Job ordering does
not change data/initialization. Use its frozen source snapshot for original-run
reproduction. Error-mining cases are regenerated from the recorded seed family,
round and case index; selected windows are saved individually. The model's own
state initializes every mined window. All source checkpoints, optimizer states,
exposure and best-development selection remain in each run folder.

## Full-corpus phase diagnostics and transfer

The following are training recipes/diagnostics, not new physical shapes. Their
job lists, original source snapshots, source checkpoint hashes and all proposals
are retained even when selection keeps the source checkpoint.

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.margin_calibrate --workers 2
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.window_rescue --workers 4 --rounds 120
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.precision_data_v2 --epochs 300
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.n_to_e
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.run train --candidates work/study/hero_shape_connectivity/no_local_candidate.json --profiles uart_n,uart_e --seeds 11,29,47 --epochs 120 --recipe phase_native_v3 --workers 3 --label no_local_native_v3_120
```

The scalar calibration found no training-feasible bias interval for either
unresolved E seed and kept both weights unchanged. Its analytic interval test
is `test_calibration`. The two window rescues optimize the same 32,768 ticks and
one Adam step per round, with gradients evaluated coherently at one parameter
snapshot. Each saved window identifies its exact training source and offset.
The N→E transfer uses each seed's own N configuration only when that E seed is
still unresolved; successful E configurations are retained without optimization.

Current matched native trajectories and topology diagrams can be refreshed with
`python -B -m work.study.hero_shape_connectivity.native_report`. Original
120-epoch results remain separate from adaptive continuation and the checkpoint
portfolio. None of these development summaries can establish a qualifier.

## Resume from the exact original implementation

`resume_batch` verifies the batch's frozen source hashes, imports that snapshot,
and resumes the exact recorded jobs. It keeps a supplemental resumed ledger;
original batch ledgers and historical snapshots are not replaced. Completed
jobs return their filed block result. Do not run a second copy while the original
worker is still training the same model folder.

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch mixed_native_v3_120 --workers 4
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch paired_window_v4_120 --entry window_rescue --workers 4
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch n_to_e_v3_60 --workers 2
```

A completed native-v3 job was replayed through this path to verify snapshot
imports and idempotent completion. A model's last journaled epoch and saved Adam
moments determine its continuation; selected best checkpoints remain separate
from the last training checkpoint.

## Sparse input routing and auxiliary-target comparison

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.run train --candidates work/study/hero_shape_connectivity/lane_candidates.json --profiles uart_n,uart_e --seeds 11,29,47 --epochs 120 --recipe phase_native_v3 --workers 3 --label lane_native_v3_120
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.teacher_compare
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.window_calibration
```

The lane variants remove only input edges: both keep the nine-feature interface,
all internal edges and readout weights, 64 nodes and matching initialization on
common parameters. The third auxiliary head's original E parity/STOP alias and
the alternative partition are defined in FOLLOWUPS.md. `timing_targets` defaults
to the original targets, preserving older recipes. Both new teacher arms start
from identical weights, reset their third auxiliary projection identically, and
use the same data/exposure; only the off-chip progress labels differ. Inference
imports neither teacher and has no added counter or state.

The nonlinear-readout architecture uses the already verified generic DAG kernel;
its extra sixteen current-sample nodes have no delayed outgoing edges. Dedicated
contracts verify common-backbone initial function, no added recurrent state,
float/integer chunking, and gradients through hidden and recurrent parameters.

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m unittest work.study.hero_shape_connectivity.test_readout
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.run train --candidates work/study/hero_shape_connectivity/readout_candidates.json --profiles uart_n,uart_e --seeds 11,29,47 --epochs 120 --workers 4 --recipe phase_native_v3 --label readout_native_v3_120
```

The corrected fixed-state fit has its own resumable support/solver checkpoints:

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.hard_margin_v4 --rounds 20
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.ring_release
```

`final_portfolio.py --candidates ... --recipe final_portfolio_LABEL` records a
completed-checkpoint selection with hashes and refuses a full-profile freeze
when fewer than five seeds pass any profile's development gates. It requires the
prior training artifacts; it is a selection step, not fresh evidence.

The first corrected full-profile confirmation is `full_shape_v2a` (family331000000):

```bash
OUT=/home/daniel/stuff/THICotPCotDUIF_exp/work/study/hero_shape_connectivity/runs/connectivity01
OPENBLAS_NUM_THREADS=1 PYTHONPATH="$OUT/confirmations/full_shape_v2a" "$PY" -B -m source.confirm_v2 evaluate --output "$OUT" --label full_shape_v2a --workers 6 --arithmetic float,quantized,no_recurrence
```

This replays the already generated frozen data; it is exact reproduction, not
another independent confirmation. `final_portfolio_v2a_selection.json` gives the
same-seed development choices and complete provenance. Each confirmation weight
file contains its actual per-node leak configuration as well as weights.

Rare-boundary follow-up uses a separate development family and fixed-state fit:

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.corner_development
OPENBLAS_NUM_THREADS=1 "$PY" -B -m unittest work.study.hero_shape_connectivity.test_stop_margin
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.stop_margin --workers 2 --rounds 32
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch stop_margin_v4_32 --entry stop_margin --workers 2
```

Do not run the resume command concurrently with original workers. Cached states
are float64 with core/shape/data identities; final selected decisions are checked
against uncached scalar inference. The enlarged development suite retains all
previous cases and adds four independent1000-message timing conditions. It is
not another confirmation and its scores must not be mixed with precision_v2 alone.

## Expanded startup and physical eight-gate comparison

The current8864-group UART suite retains precision-v2, adds four1000-message
timing-corner streams and320 independent known-idle/error startup files.
Training-only sustained corners are separately generated; families are recorded
in each data manifest. Native-v6 uses all three candidates under the same recipe.

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.startup_dev_v5
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.stationary_train_v6
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.run train --candidates work/study/hero_shape_connectivity/gate_eight_candidates.json --profiles uart_n,uart_e --seeds 11,29,47 --epochs 120 --workers 8 --recipe phase_native_v6 --label gate_eight_native_v6_120
```

Resume an interrupted batch from its original snapshot, never concurrently with
the original workers:

```bash
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch gate_eight_native_v6_120 --workers 8
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch dense_startup_v6_64 --entry startup_core_v5 --workers 4
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch first_gate_n_to_e_v6_60 --workers 4
OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.resume_batch linear_closure_v8_16 --entry linear_closure_v8 --workers 1
```

The interrupted linear-closure-v7 collector exceeded its intended in-memory
support budget before the end-of-scan check. Its original sources, saved first
iterations, jobs and interruption record are preserved. Do not resume that
collector unchanged. Version8 enforces capacity during collection and still
counts every training tick; see FOLLOWUPS for the exact constraint rule.

`final_portfolio_v3.py` now requires all expanded UART development conditions
before finalist selection. `confirm_v3.py` freezes weights before generating a
new family, retains every corrected-v2 gate, adds64 independent known-idle and
64 mid-frame UART cases/profile, and separately replays full_shape_v2a as a
regression suite. Qualification requires the same>=5/6 seeds/profile to pass
both suites. Float andQ3.12 remain separate, and seed11 recurrence ablations are
diagnostics only. **No new v3 confirmation family has yet been chosen/generated.**


## First-layer gates and feedback controls

`mixed_first_native_n_remaining120`, `mixed_first_plain_refine_n_remaining60`
and the same gated refinement extend the original paired native-v3 experiment
to the remaining seeds71/101/131. `first_gate_transfer_v6` uses same-seed
no-parity weights as parity initialization, resets the optimizer and freezes
source hashes. Its `--seeds` and `--label` options record each continuation.

`gate_bias_clamp_v6a` freezes five completed full-development passes, removes
conditional gate-input weights and converts the learned gate biases exactly
to ordinary per-node leaks. No training follows. Its source/checkpoint hashes,
converted weights and full8864-group scores are retained. It tests these weights,
not the trainability of every constant-leak configuration.

Future v3 confirmations retain the historical `no_recurrence` control, whose
precise meaning is removal of within-layer proposal edges only. They add
`no_feedback`, which also removes backward proposal routes and all conditional
gate inputs. Forward routes, leak carry, input ages and gate biases remain;
neither control is memoryless. Both use frozen seed11 weights without refitting
and cannot pass a shape's qualification on their own. Three focused v3 tests
check exact masks, startup contracts and same-seed fresh/regression intersection.

## Frozen dense-readout v3 confirmation

`final_portfolio_v3_dense_a` was selected exclusively on completed expanded
8864-group development blocks. It has5/6 UART-N and5/6 UART-E passes, with6/6
in all clocked profiles. `dense_full_v3a` freezes all42 profile/seed weight sets,
physical definitions, resources and source before generating family501000000.
Fresh and previous-v2 regression data are distinct; both must pass for the same
five seeds. This confirmation is complete: one physical shape qualifies in float and Q3.12. See QUALIFIED_SHAPES.md for seed-level limits.

```sh
$PY -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 generate --label dense_full_v3a
$PY -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 evaluate --label dense_full_v3a --workers 6
```

The runner verifies hashes and imports the frozen package for generation and
inference. It does not substitute the mutable working implementation. Float,
Q3.12, local-recurrence removal, and complete-feedback removal are recorded
separately. Repeating these commands reproduces the same data; it does not create
new independent evidence. Never run a second evaluator concurrently on the same
result folders.

The successful balanced startup-grid diagnostic is documented in COVERAGE_V10.md.
To resume an interrupted fit, use its original job list and source snapshot:

```sh
$PY -B -m work.study.hero_shape_connectivity.resume_batch grid_margin_v10_e101_8 --entry grid_margin_v10 --workers 1
```


## First-layer gates and revised fitting

The completed `first_gate_full_v3a` has float counts6,4,6,6,6,6,5 and
Q3.12 counts6,5,6,6,6,6,5 in UART-N, UART-E, I2C, SPI0–3 order. Its float
parity result misses the unchanged5/6 requirement. Preserve it as a failed
float confirmation even though the separate quantized evaluation passes.

```sh
$PY -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 evaluate --label first_gate_full_v3a --workers 6
$PY -B -m work.study.hero_shape_connectivity.resume_batch gated_margin_v11_e_16 --entry gated_margin_v11 --workers 2
$PY -B -m work.study.hero_shape_connectivity.resume_batch gated_linear_v12_e131_16 --entry gated_linear_v12 --workers 1
```

Resume only after the corresponding active worker has stopped. Original job
lists, source snapshots, input hashes, all fit iterates and learning curves
remain under `runs/connectivity01`. These commands resume existing evidence;
they do not erase failed trials or create a fresh comparison. A future gated
confirmation must include `--regression-label first_gate_full_v3a` at freeze,
which retains that entire suite alongside the original v2 regression.

## Raw-waveform demonstration

Choose a manifest from `runs/connectivity01/qualified_demonstrations_v3`.
An input NPZ needs only a `lines` array with shape N×3 containing0/1 samples.
The runtime never reads training labels, expected bytes or generator boundaries.

```sh
$PY -B -m work.study.hero_shape_connectivity.infer_demonstration --manifest MANIFEST.json --profile uart_n --input RAW_LINES.npz --output NEW_EVENTS.json --arithmetic float
```

Use `--arithmetic quantized` for the separately measured Q3.12 configuration.
The command verifies frozen source/weight hashes, maintains causal neural and
feature state, and emits the existing event-only assembly. Output files must be
new. `demonstration_interface_verification.json` records float and quantized
checks against independent truth using a raw-lines-only input file.


The v13 recovery-coverage continuation preserves the v12 failure and adds the
balanced independent invalid/recovery corpus before fitting:

```sh
$PY -B -m work.study.hero_shape_connectivity.error_grid_v13
$PY -B -m work.study.hero_shape_connectivity.resume_batch gated_linear_v13_e131_16 --entry gated_linear_v13 --workers 1
```

Its generated pool manifest verifies all1296 input files; unchanged fixed-state
caches may be shared, while every fit history and parameter checkpoint is separate.
[GATE_ALLOCATION_COMPARISON.md](GATE_ALLOCATION_COMPARISON.md) records all18
completed eight-gate/native-control continuations, including failed boundaries.

## Final readout-routing comparison: v14–v19

The reduced graph is defined by `readout_pruned32_fast_candidate.json`; both
finalist constructions are in `readout_cost_pair_v3_candidates.json`. Every stage
has an immutable source snapshot and job tuples specifying its source-checkpoint
hashes. Resume/replay these recorded stages using the table below. Completed fits
return their retained results; this does not retrain or create fresh evidence.

```sh
$PY -B -m work.study.hero_shape_connectivity.resume_batch \
  LABEL --entry ENTRY --workers 6
```

| LABEL | ENTRY | Recorded scope |
| --- | --- | --- |
| readout_projection_v14_pilot | pruned_readout_v14 | First-layer-complete 32-parent pilot, N/E seeds 11/29/47 |
| readout_projection_v15_n_pilot | pruned_readout_v15 | Fast-ring-complete projection, N 11/29/47 |
| readout_projection_v15_e_pilot | pruned_readout_v15 | Same graph, E 11/29/47 |
| readout_projection_v15_extra | pruned_readout_v15 | N/E 71/101/131 |
| readout_supervised_v16_pilot | head_learning_v16 | Paired conditional head fitting, N/E 11/29/47 |
| readout_supervised_v16_extra | head_learning_v16 | Paired conditional head fitting, N/E 71/101/131 |
| readout_projection_clocked_v17_all | pruned_clocked_v17 | All five clocked profiles, all six seeds |
| readout_supervised_clocked_v18_all_fixed | head_learning_clocked_v18 | Paired clocked head fitting |
| grid_margin_v19_e101_8 | grid_margin_v19 | Paired parity-101 startup-grid fitting |

The first clocked-head launch, `readout_supervised_clocked_v18_all`, failed before
jobs were created because its source path was wrong. Its log is retained; use the
`_fixed` label above. Shared supervised banks are prepared once before parallel
fits. Grid replay uses bounded retained constraints; the older stopped unbounded
v7 collector is not required.

Selection and confirmation were executed in this order:

```sh
$PY -B -m work.study.hero_shape_connectivity.final_portfolio_v3 \
  --candidates work/study/hero_shape_connectivity/readout_cost_pair_v3_candidates.json \
  --recipe final_portfolio_v3_readout_cost_a
$PY -B -m work.study.hero_shape_connectivity.confirm_v3 freeze \
  --label readout_cost_full_v3a \
  --candidates work/study/hero_shape_connectivity/readout_cost_pair_v3_candidates.json \
  --seed-family 531000000 --recipe final_portfolio_v3_readout_cost_a \
  --regression-label dense_full_v3a
$PY -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 generate \
  --label readout_cost_full_v3a
$PY -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 evaluate \
  --label readout_cost_full_v3a --workers 16
$PY -B -m work.study.hero_shape_connectivity.audit_confirmation_v3 \
  --label readout_cost_full_v3a
```

Freeze is intentionally immutable and will refuse an existing label. Do not
re-run freeze against the recorded label or change saved sources/weights. For
existing evidence, replay only evaluation/audit. A new independent confirmation
needs a new label and unused seed family selected after finalist selection.
`full_shape_v2a` and `dense_full_v3a` are copied byte-for-byte into a separate
regression ledger. All float/Q3.12 configurations are evaluated; feedback ablations
are diagnostic seed-11 controls. The six-seed qualification is not inferred from
those ablations.

The cheaper first-layer-gated alternative was also pursued: confirmation A passed
only the quantized gates; confirmation B failed both arithmetic modes, including
new parity timing errors after the v13 training-grid repair. Both frozen trials
and every failed condition remain in the qualification failure CSV. They are not
counted as float-qualified shapes or silently discarded.

```sh
$PY -B -m work.study.hero_shape_connectivity.readout_report_v19
$PY -B -m work.study.hero_shape_connectivity.qualified_report_v3
```

Reports reconstruct from saved blocks and frozen ledgers. Demonstration manifests
point to their exact frozen receiver source; the raw-line inference CLI documented
above verifies weight/source hashes and accepts only sampled three-line waveforms.

## SPI pause coverage and the second readout freeze — v20

Confirmation A failed mandatory SPI1 seed replication. Preserve it. New pause
training/development comes from families411000000/413000000 with recorded
profile/stream offsets, never from confirmation A. All24 paired fits use the
same continuous-waveform pool and conditional output-only fitting rule.

```sh
$PY -B -m work.study.hero_shape_connectivity.resume_batch \
  clocked_pause_v20_all12 --entry clocked_pause_v20 --workers 4
$PY -B -m work.study.hero_shape_connectivity.pause_diagnostic_v20
$PY -B -m work.study.hero_shape_connectivity.pause_report_v20
```

The diagnostic is read-only and checks saved failure traces against the two
identical recurrent backbones. CLOCKED_PAUSE_V20.md records its interpretation,
new full-training-pool scans and expanded development. The next finalist helper
(`prepare_pause_v20_finalist`) requires at least5/6 development-plus-training-
closure passes per changed profile. It takes SPI1/SPI2 from that intervention
and retains all other A-selected configurations byte-for-byte. A new freeze
must add `--regression-label readout_cost_full_v3a` alongside
`--regression-label dense_full_v3a`; the original v2 suite is automatic.

The revised paired freeze was executed after all24 pause fits passed their
expanded development and full training scans. Only six of84 configurations
changed, exclusively in the existing output rows; see
`runs/connectivity01/readout_cost_b_revision_contract.json`.

```sh
$PY -B -m work.study.hero_shape_connectivity.prepare_pause_v20_finalist
$PY -B -m work.study.hero_shape_connectivity.confirm_v3 freeze \
  --label readout_cost_full_v3b \
  --candidates work/study/hero_shape_connectivity/readout_cost_pair_v3_candidates.json \
  --seed-family 541000000 --recipe final_portfolio_v3_readout_cost_b \
  --regression-label dense_full_v3a --regression-label readout_cost_full_v3a
$PY -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 generate \
  --label readout_cost_full_v3b
$PY -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 evaluate \
  --label readout_cost_full_v3b --workers 16
$PY -B -m work.study.hero_shape_connectivity.audit_confirmation_v3 \
  --label readout_cost_full_v3b
$PY -B -m work.study.hero_shape_connectivity.paired_readout_result \
  --label readout_cost_full_v3b
```

As above, the recorded freeze/generation already exists and is immutable; use
only evaluation/audit for replay. Do not overwrite a recorded label.

To actually repeat a fitted pause intervention rather than return its saved
block, choose a nonexistent output directory:

```sh
$PY -B -m work.study.hero_shape_connectivity.reproduce_pause_job \
  --job-index 14 --output /tmp/hero_pause_reproduction_new
```

Job14 is reduced-readout SPI1 seed47. The helper verifies the immutable source,
reads the same retained source checkpoint and independent training waveforms,
and recomputes states, fits the output rows, evaluates development, and checks
weights/leaks/selection against the original result. All generated model files
and caches go in the new directory. This is training reproducibility, not fresh
confirmation.

All14 seed11 shape/profile demonstration configurations were additionally tested
from raw sampled lines in float and Q3.12 (28 combinations). These small independent
family421000000 interface checks are separate from full qualification:

```sh
$PY -B -m work.study.hero_shape_connectivity.demo_smoke_v20
```

Inputs contain only `lines`; oracle truth remains outside the receiver input.
The result is `runs/connectivity01/raw_demonstration_verification_v20/verification.json`.
The selected protocol weights, raw inputs and decoded outputs are preserved there.
