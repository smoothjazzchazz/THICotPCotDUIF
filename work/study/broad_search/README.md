# Broader reservoir research

**Outcome: confirmed improvement on the synthetic pulse-order benchmark.**
Start with the [results and explanation](REPORT.md), then the
[before-search plan](PLAN.md) and [complete experiment ledger](LEDGER.md).
No hardware specification or project gate was changed.

## Inspect the implementation

* [Polynomial memory](../polynomial_memory/README.md): selected NGRC/NVAR approach.
* [Boolean cellular reservoirs](../boolean_ca/README.md): rejected configurations.
* [Scalar nonlinear delay feedback](../delay_feedback/README.md): rejected configurations.
* [Size/topology/modular controls](../modular_reservoirs/README.md): matched total state budgets and topology seeds.
* [Shared evaluation](../shared/broad.py): readout fitting, rejection, causal receiver and snapshot reload.
* [Resource accounting](../shared/resources.py): storage and operation estimates.

Each adaptive stage has a separate runner. Configurations are experiment
variants; repeated seeds/precision checks are recorded as repeated evaluations,
not counted as new approaches. There are 94 development configuration/readout
records, one confirmation attempt, a full replay, and an explicitly separate
post-selection unknown-pattern limitation probe.

## Use the frozen recognizer

From the repository root:

```sh
work/study/.venv/bin/python -B -m work.study.polynomial_memory.replay \
  --input work/study/results/research-report/20261005T012524.648650Z/waveform.txt
```

Or feed a text file containing only causal 0/1 samples (whitespace/commas allowed).
The command loads `polynomial_memory/compact_20_q8.json` and prints JSON symbol
events. Class 2 is background, class 7 unknown. The portable configuration can
be used without any saved study results.

## Replay the confirmation

This consumes the **saved input streams**, generates no fresh test set, and
requires the recorded source hashes to match:

```sh
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.confirm replay \
  --directory work/study/results/broad-confirmation/20261005T012024.954575Z
```

A new `results/confirmation-replay/<unique-run-id>/` records exact agreement.
Keep the confirmation directory with the source checkout when sharing evidence;
generated result directories remain Git-ignored, matching the existing study.

## Reproduce the development sequence

These commands create unique new output directories and preserve earlier runs:

```sh
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_screen
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_validate
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_robust
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_quantized
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_ablations
```

`run_screen --family polynomial|ca|delay|modular|legacy` narrows the screen.
`run_robust` uses additional training timing examples with matched controls;
`run_quantized` consumes its latest saved output; `run_ablations` consumes the
latest quantization output. All numerical results and exact inputs are saved.
Seed blocks 31–36 million are development only; the original training/validation
seeds remain 2,300,000 and 2,310,000 ranges. Manifests record source hashes and
purpose; saved datasets or the preceding stage record exact individual seeds.

`confirm freeze` refits all historical baselines on their original development
data, reserves an unused seed batch and writes frozen settings. `confirm run
--directory <printed-path>` generates that batch once. These are **research
confirmation actions**, not required for replay; the first attempt already
succeeded. The tool refuses reuse and limits this study to three attempts.
Every attempted batch retains its status, including failures.

For report-only rendering from saved confirmation evidence:

```sh
MPLCONFIGDIR=/tmp/tpm-matplotlib OPENBLAS_NUM_THREADS=1 \
  work/study/.venv/bin/python -B -m work.study.broad_search.report_results \
  --confirmation work/study/results/broad-confirmation/20261005T012024.954575Z
```

## Evidence locations

| Stage / purpose | Saved run |
| --- | --- |
| Broad inexpensive screening | [38 records](../results/broad-screen/20261005T011146.539052Z/screen.json) |
| Architecture/seed validation | [28 records](../results/broader-validation/20261005T011251.428831Z/validation.json) |
| Timing-coverage hypothesis and controls | [9 records](../results/jitter-training/20261005T011420.632152Z/validation.json) |
| Quantization and augmented legacy controls | [14 records](../results/quantized-memory/20261005T011611.751866Z/validation.json) |
| Matched nonlinear/unknown/input/precision ablations | [5 records](../results/memory-ablations/20261005T011727.898570Z/validation.json) |
| Frozen confirmation, attempt 1 | [Metrics](../results/broad-confirmation/20261005T012024.954575Z/metrics.json) |
| Independent replay | [Verification](../results/confirmation-replay/20261005T012553.876841Z/verification.json) |
| Original saved baseline and preservation checks | [Verification](../results/delivery-verification/20261005T012820.001570Z/verification.json) |
| Figures, per-configuration costs and boundary collisions | [Report artifacts](../results/research-report/20261005T012524.648650Z/) |
| Unseen-unknown limitation probe; no retuning | [Probe](../results/unseen-unknown-probe/20261005T012713.374377Z/probe.json) |

## Correctness checks

```sh
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m unittest discover -s work/study -p 'test_*.py' -v
work/study/.venv/bin/python -B -m unittest discover -s work/model -p 'test_*.py' -v
python3 -B work/tools/check_template.py
git diff --check
```

Focused tests cover delay timing, pair products, causal future independence,
initial-state flush, simultaneous Boolean rules, old-tail feedback, explicit
unknown fitting, integer coefficient ranges, score bounds, events, and JSON
midstream restoration. The independent delivery verifier additionally checks
original saved baseline coefficients, decisions/events and historical hashes.
