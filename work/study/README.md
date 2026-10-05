# Reservoir studies

Experiments for G1: find a temporal shape that can be loaded, decoded, and
re-emitted, including class 7 for unknown input. Goals and gates are in
[doctrine.md](../../knowledgebase/doctrine.md) and
[phases.md](../../knowledgebase/phases.md).

## Experiments

Read these in order. Each experiment folder contains its runner, experiment
code, tests, and a README with its methods and observed results.

| Folder | Question | Saved report |
| --- | --- | --- |
| [readout_comparison/](readout_comparison/README.md) | How do Hamming, sign-bit linear, and full-state linear readouts compare, with a fixed or selected reservoir? | [Fixed](results/latest/report.html), [selected](results/selected/report.html) |
| [mixed_leaks/](mixed_leaks/README.md) | Can different per-node leak shifts preserve the first pulse and support recognition? | [Mixed leaks](results/mixed-leaks-seed24-test104/report.html) |
| [delay_chains/](delay_chains/README.md) | Can explicit finite memory fix initialization dependence and retain the relevant history? | [Delay chains](results/delay-chains-test105/report.html) |

[shared/](shared/README.md) contains signal generation, readout fitting,
evaluation, and plotting reused by all three experiments. The integer reservoir
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

The existing discovery command finds tests inside all four folders:

```sh
work/study/.venv/bin/python -B -m unittest discover -s work/study -p 'test_*.py' -v
work/study/.venv/bin/python -B -m unittest discover -s work/model -p 'test_*.py' -v
python3 -B work/tools/check_template.py
git diff --check
```
