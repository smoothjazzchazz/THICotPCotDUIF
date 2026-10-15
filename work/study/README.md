# Architecture studies

Current runnable example: [shared-stage waveform demo](stage_demo/README.md).
It keeps stimulus generation, offline fitting, scoring and results here while
reusing the common stages and runner in [work/model](../model/README.md).
Typical new experiments should configure, swap or extend those stage modules
rather than duplicate the pipeline. An experiment can still justify a different
decomposition under the scope amendment below.

New experiments follow [experimental scope](../../knowledgebase/experiments.md).
Agents may explore reservoir and total system architectures in a descriptive
folder here, with their own models and a short README stating the question,
assumptions, comparison, and results. Existing model interfaces and the reference
design's mechanisms are available comparisons, not limits on the experiment.

The previous study implementations and raw artifacts were cleared on 6 October
2026. Their Markdown reports remain. [ARCHIVE.md](ARCHIVE.md) records the cleanup
and how to recover exact code and data from Git history.

## Historical study index

The notes below are retained from the previous studies. Their commands and
non-Markdown links refer to the pre-cleanup tree. They describe past work and
do not add requirements for new experiments.

Experiments for G1: find a temporal shape that can be loaded, decoded, and
re-emitted, including class 7 for unknown input. Goals and gates are in
[doctrine.md](../../knowledgebase/doctrine.md) and
[phases.md](../../knowledgebase/phases.md).

Read the [comprehensive experiment report](EXPERIMENT_REPORT.md) for the waveform
families, architectures, measured strengths, failures, reasoning and hardware
limits across all study stages.

## Protocol study suite

[protocol_suite/](protocol_suite/README.md) contains the completed synthetic
multi-family study, including fresh confirmation and cold reproduction. Its
[report](protocol_suite/REPORT.md) describes the strong long-context results of
16-run Boolean memory and the unresolved tradeoff between malformed-input
rejection and noisy clock/data recall. It does not establish named-protocol
compliance or a project gate pass.

## Experiments

Start with the [broader research result](broad_search/REPORT.md): a study-only
20-sample NGRC implementation with 8-bit readout coefficients passed fresh
confirmation (90.0% event F1 versus 80.9% for the strongest rerun legacy
reservoir; 94.0% unknown recall). Its [ledger](broad_search/LEDGER.md) retains
failed alternatives, controls, resource costs and reproduction evidence.

The original experiments below retain their paths and historical evidence.
Each experiment folder contains its runner, experiment
code, tests, and a README with its methods and observed results.

| Folder | Question | Saved report |
| --- | --- | --- |
| [readout_comparison/](readout_comparison/README.md) | How do Hamming, sign-bit linear, and full-state linear readouts compare, with a fixed or selected reservoir? | [Fixed](results/latest/report.html), [selected](results/selected/report.html) |
| [mixed_leaks/](mixed_leaks/README.md) | Can different per-node leak shifts preserve the first pulse and support recognition? | [Mixed leaks](results/mixed-leaks-seed24-test104/report.html) |
| [delay_chains/](delay_chains/README.md) | Can explicit finite memory fix initialization dependence and retain the relevant history? | [Delay chains](results/delay-chains-test105/report.html) |
| [broad_search/](broad_search/README.md) | What survives a broader search, matched controls, quantization and fresh confirmation? | [Research report](broad_search/REPORT.md), [ledger](broad_search/LEDGER.md) |
| [polynomial_memory/](polynomial_memory/README.md) | Can delayed inputs plus nonlinear interactions support reliable rejection? | Confirmed on the pulse-order benchmark; [portable settings](polynomial_memory/compact_20_q8.json) |
| [boolean_ca/](boolean_ca/README.md) | Can local Boolean rules provide useful cheap memory? | Rejected in the measured screen |
| [delay_feedback/](delay_feedback/README.md) | Does nonlinear scalar feedback improve on a plain delay buffer? | Rejected in the measured screen |
| [modular_reservoirs/](modular_reservoirs/README.md) | Do size, structure or multiple reservoirs help at matched storage? | Promising original validation; no selected robust winner |

[shared/](shared/README.md) contains signal generation, readout fitting,
evaluation, and plotting reused by the experiments. The original integer reservoir
itself lives in [work/model/](../model/README.md).

## Run

From the repository root, using the existing environment:

```sh
work/study/.venv/bin/python -B -m work.study.readout_comparison.run_comparison
work/study/.venv/bin/python -B -m work.study.mixed_leaks.run_mixed_leaks
work/study/.venv/bin/python -B -m work.study.delay_chains.run_delay_chains
```

These are separate commands for separate experiments. Read each experiment's
README before running it: mixed leaks protects existing outputs, and delay chains
also refuses a test seed already recorded in local results. Use `--help` to inspect
options without running an experiment.

For a fresh checkout, create the shared environment once:

```sh
python3 -m venv work/study/.venv
work/study/.venv/bin/python -m pip install -r work/study/requirements.txt
```

## Saved results

Generated reports, traces, and frozen settings remain under `results/`, at their
original paths. They and `.venv/` are Git-ignored. Historical artifacts retain
their original commands, source paths, and hashes; new runs record the reorganized
source paths. The experiment READMEs link to the corresponding saved reports.

## Checks

The discovery command below finds the study tests recursively, including the
protocol suite's contract, scoring, causality and checkpoint tests.

```sh
work/study/.venv/bin/python -B -m unittest discover -s work/study -p 'test_*.py' -v
work/study/.venv/bin/python -B -m unittest discover -s work/model -p 'test_*.py' -v
python3 -B work/tools/check_template.py
git diff --check
```
