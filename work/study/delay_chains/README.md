# Finite delay-chain experiment

From the repository root:

```sh
work/study/.venv/bin/python -B -m work.study.delay_chains.run_delay_chains
```

Open [the report](../results/delay-chains-test105/report.html). The separate runner
requires a new output directory and refuses paths within existing result trees,
including the original and mixed-leak runs and resolved symlink aliases. It also
refuses test seed 105 if local saved JSON evidence already records its use.
After the first run, inspect the saved artifacts; repeating seed 105 would be
reproducibility work, not fresh evidence. `--output` changes only the destination.

## What changes

`EXPERIMENT` in [delay_chains.py](delay_chains.py) is the settings block. Exactly
two predetermined candidates use one existing 16-node, six-bit `IntegerReservoir`
each. Node 0 receives the existing feature taps; each later node copies the
previous tick's predecessor with weight +1. All leaks and other weights are zero.
All three recurrent and two feature slots remain present with valid indices.

| Configuration | Root input | Role |
| --- | --- | --- |
| `age_chain` | signed_level − log_age | New candidate |
| `level_chain` | signed_level | Age ablation |
| `seed24_forward_leak0` | Original generated inputs | Original selected control |
| `cycle3210` | Original generated inputs | Previously rejected mixed-leak control |

The two chains isolate the age contribution. Comparisons with legacy controls
also change topology and input placement. The saved original selection and
mixed-leak control were checked against their generated configurations before
implementation. The model, feature encoding, signed rounding, clipping, updates,
reset behavior and serialization are unchanged. No readout history is added.

## Timing and recognition are separate questions

Features update first, then all reservoir nodes update simultaneously, then the
readout decides. After startup, `state[i]` at tick `t` equals `q(t-i)`: the current
input plus **15 previous ticks**. Subtracting the last first-pulse high tick from
the final falling-edge tick gives:

```text
delay at decision offset d = gap + second_pulse_width + 1 + d
```

The nominal long-ending pair reaches nodes 12, 13, 14, 15 at offsets 0, 1, 2, 3.
At offset 3, the maximum delay becomes 17 with ±1 duration variation and 19 with
±2. Neither the chain nor decision window is adjusted to avoid this limit.

For identical features, node 0 overwrites initial state on update 1, node 1 on
update 2, and node 15 on update 16. The implementation verifies both extreme
initial vectors and exact propagation; tests also use nonuniform initial values.
This finite reservoir-state property does **not** establish convergence of an
arbitrarily initialized `FeatureExtractor`, or successful task recognition.

The original reset/20-low and 50 continuous-prefix probes are reused, with all
five nominal targets and four post-update decision ticks. Saved diagnostics
separate full-state distances, differing signs, matched-prefix differences,
cross-prefix collisions, same-target variation, and actual class counts.

The separate deterministic timing diagnostic has 204 paired cases: both required
comparisons, full gap/second-width grids for ±1 and ±2, and matched first-width
changes of `−range`, `0`, `+range`. This controlled grid is development evidence,
not a complete perturbation sweep or held-out recognition score. Its plots fix
first widths at 3 and 8 to show the horizon clearly.

## Fitting, rejection and freezing

All four configurations use identical seed-23 training/validation streams,
standard counts (12/6 streams, 24 patterns), and unchanged distributions. Hamming,
linear/sign-bit and linear/full-state readouts share exactly the same states.
The existing fitting objective, ridge/decision/M grids and reference selection
are reused. Only training fits coefficients; validation chooses settings.

Original screens remain: at least two fingerprints, at most 50% saturated node
samples and initialization-tail gap at most one. The mixed-leak requirements
also remain: no required nominal full-state collision at any offset, including
across prefixes; all full-state reset decisions correct; at least 90% correctness
for each continuous target/offset; and validation known-event precision, recall,
and unknown recall each at least 80%. Every failure is recorded. These screen
the existing F1-selected settings; they do not search for alternative settings
that satisfy the constraints. Controls cannot win or serve as fallbacks.

The runner saves the plan before fitting and freezes all configurations,
readouts, validation choices and eligibility before generating tests. It reloads
the frozen files, then evaluates every configuration and the run-length reference
on identical seed-105 clean, jitter, glitches and mixed streams (6 per condition).
Earlier test seeds 23, 24 and 104 are development evidence. No settings may change
after looking at seed 105, and different datasets cannot establish improvement.

The report includes detections, misses, false detections, precision, F1, unknown
recall, and matched-event median/p95 latency, with clean results separated from
the aggregate. Per-configuration reports include each perturbation condition.

Artifacts include `plan.json`, `freeze.json`, `config.json`, `selection.json`,
`metrics.json`, `development_streams.json`, `test_streams.json`, `timing.json`,
`memory_traces.json.gz`, and each configuration's full test traces. Source hashes,
dataset hashes, stream seeds, freeze time and reload results are recorded.
Plots are embedded in HTML and also saved as PNG/SVG. Generated results are
Git-ignored. No RTL, firmware, released specification or gate status changes.

## Verification

```sh
work/study/.venv/bin/python -B -m unittest discover -s work/model -p 'test_*.py' -v
work/study/.venv/bin/python -B -m unittest discover -s work/study -p 'test_*.py' -v
work/study/.venv/bin/python -B work/tools/check_template.py
git diff --check
```

Focused tests cover configuration isolation, hand-derived propagation, the
15-tick horizon, initial-state flushing, post-update probe timing, boundary
collisions, selection without control fallbacks, reload/replay, output protection,
unchanged development data, and freezing before held-out generation.

## Observed result: 2026-10-04 local time

**Neither chain qualified; the frozen selection is `null`. Explicit finite
memory fixed initialization dependence and improved nominal retention, but did
not produce reliable recognition.** No settings changed after seed-105 results.

1. **Initialization dependence: fixed for reservoir state.** Both chains have
   zero initialization-tail gap and flush arbitrary node values within 16 updates
   under identical features. Both have zero saturated training samples and
   changing sign fingerprints (402 for age-carrying; 1,057 for level-only).
2. **Nominal retention: fixed only in the age chain's full state.** Its minimum
   cross-prefix L1 distances are `[9,6,3,1]` for `(3,8)` versus `(8,8)`, and
   `[28,27,22,17]` for `(8,3)` versus `(3,3)`. Corresponding sign-bit distances are
   `[2,2,1,0]` and `[4,4,3,2]`: signs lose the long-ending distinction at the final
   tick. Level-only full-state distances are `[2,0,0,0]` for the long-ending pair,
   so the age contribution is necessary for this nominal comparison.
3. **Usable known/unknown recognition: not fixed.** The age chain's full-state
   readout gets both known nominal targets right at every offset, but predicts
   known class 0 for unknown `(8,8)` at every offset after reset and across all
   50 prefixes. It predicts class 1 for `(5,5)` at offsets 0–2. Its validation
   precision is 51.2%, known recall 88.5%, and unknown recall 29.7%; precision,
   unknown recall and probe-decision requirements fail. Level-only additionally
   fails the collision requirements. All rejection reasons are in the audit.
4. **Perturbation robustness: not fixed.** The first-pulse sample can leave the
   chain within the decision window even under ±1 variation. At gap 4 and second
   width 9, it is already gone at offset 2; at gap 5 and width 10, it is gone at
   offset 0. The deterministic grid verifies exact full-state collisions in
   these cases. The age chain's held-out full-state F1 is 59.4% on jitter, 67.4%
   on glitches, and 42.3% on mixed inputs. Unknown recall remains below 38% in
   every condition. This is both a finite-horizon limit and an observed readout
   failure; retained clean-state differences alone do not solve rejection.

The age chain still has some same-target prefix variation, especially for the
shorter target. Its recent inputs can contain different pre-target idle-age
values from the unchanged `FeatureExtractor`. That is compatible with flushing
initial *reservoir* values; it is not evidence of a feedback loop in the chain.

All rows below use the **same seed-105 test streams**, with 96 clean known events
and 384 aggregate known events. Reservoir rows use the full-state linear readout.
The HTML report includes all three readouts, each condition and full latency data.

| Configuration | Condition | Detections / misses | False | Precision | F1 | Unknown recall | Latency median / p95 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Age chain | Clean | 96 / 0 | 54 | 64.0% | 78.0% | 26.0% | 2 / 2 |
| Age chain | Aggregate | 317 / 67 | 334 | 48.7% | 61.3% | 29.4% | 2 / 3 |
| Level chain | Clean | 96 / 0 | 122 | 44.0% | 61.1% | 54.2% | 2 / 2 |
| Level chain | Aggregate | 290 / 94 | 297 | 49.4% | 59.7% | 67.6% | 2 / 2.55 |
| Original selected | Clean | 96 / 0 | 192 | 33.3% | 50.0% | 0.0% | 2 / 2 |
| Original selected | Aggregate | 354 / 30 | 707 | 33.4% | 49.0% | 0.0% | 2 / 3 |
| cycle3210 | Clean | 96 / 0 | 21 | 82.1% | 90.1% | 50.0% | 2 / 2 |
| cycle3210 | Aggregate | 339 / 45 | 103 | 76.7% | 82.1% | 50.0% | 2 / 3 |
| Run-length reference | Clean | 96 / 0 | 0 | 100% | 100% | 100% | 2 / 2 |
| Run-length reference | Aggregate | 245 / 139 | 13 | 95.0% | 76.3% | 82.9% | 2 / 2 |

Other readouts do not overturn the conclusion. The age chain's sign-bit linear
readout reaches 85.0% clean F1 and 85.4% clean unknown recall, but rejects both
known nominal targets at offset 3. Level-only Hamming has 79.3% aggregate F1,
yet its long-ending snapshots collide after offset 0. These scores do not meet
the frozen requirements. The legacy controls remain diagnostic, not winners.

**One next experiment:** keep the age chain fixed and compare the current
all-zero unknown training target with an explicit fourth linear output for
class 7. Keep features, node count, timing, data distributions and eligibility
requirements fixed; freeze before reserving another fresh test set. This tests
whether the training/rejection formulation can use the retained magnitude
distinction. It cannot restore history beyond 15 ticks. It was not implemented
or tuned in this experiment.

Verification: 11 model and 24 study tests passed, including all mixed-leak tests;
template and whitespace checks passed. Separate `delay-chain-regression-fixed/`
and `delay-chain-regression-selected/` runs reproduced the original configurations,
metrics, selections and decompressed traces. The two legacy controls' fitted
settings exactly match their saved originals. Test inputs and reference outputs
match across all four configurations; every test and nominal probe passed
streaming replay. All frozen hashes remain unchanged. All 17 plots were visually
inspected. Of 236 pre-existing files checked, only the intentional README links
changed; original Python sources and saved artifacts remain byte-identical.
See [verification.json](../results/delay-chains-test105/verification.json).
