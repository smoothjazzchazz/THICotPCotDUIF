# Experiment archive and fresh start

The previous experiments were removed from the working tree on 6 October 2026
at the user's request. This directory now retains their Markdown documentation.
All 21 pre-existing Markdown files were preserved without changes, including
the detailed confirmation tables and frozen plan.

## What remains useful

- [Comprehensive experiment report](EXPERIMENT_REPORT.md): waveform families,
  methods, results, failures, interpretation, and hardware limitations.
- [Original receiver experiments](readout_comparison/README.md),
  [mixed leaks](mixed_leaks/README.md), and [delay chains](delay_chains/README.md):
  state collisions, initialization, memory horizon, and rejection failures.
- [Broad-search report](broad_search/REPORT.md) and
  [ledger](broad_search/LEDGER.md): the confirmed sample-memory candidate,
  alternatives, ablations, and rejected trials.
- [Protocol-suite report](protocol_suite/REPORT.md),
  [ledger](protocol_suite/LEDGER.md), and
  [confirmation tables](protocol_suite/artifacts/analysis/TABLES.md): explicit
  run memory, per-condition results, unknown rejection, recovery, and cost.
- [Suite provenance](protocol_suite/PROVENANCE.md): the historical verification
  and reproduction record.

These are historical research records. References to Python scripts, JSON
settings, plots, traces, logs, environments, and runnable commands describe the
pre-cleanup tree; those non-Markdown files are no longer present. Some links
therefore intentionally point to removed artifacts. The old shared README's
description of the protocol suite as an empty scaffold was already outdated;
the suite report documents its completed experiments.

The results remain synthetic-study evidence. They do not establish a completed
hardware design, named-protocol compliance, or a passed project gate.

## Cleanup scope

- Removed every non-Markdown file under `work/study/`: implementations, runners,
  tests, requirements, study ignore files, configurations, raw data, plots, logs,
  frozen source copies, and generated results.
- Removed `work/model/reservoir_model.py` and
  `work/model/test_reservoir_model.py`, as explicitly requested.
- Removed the editor's references to the old study Python environment.
- Retained the simple controller/transmitter scaffold and its tests. Its generic
  receiver argument remains available for future implementations; the old
  reservoir-specific examples in `work/model/README.md` are historical.

The deletion covers 1,585 files containing 93,858,391 bytes (about 89.5 MiB).
No existing Markdown, released specification, RTL, or workflow was changed.

## Recovering exact old information

All removed files were tracked and unchanged in Git before cleanup. Their exact
contents remain in the existing pre-cleanup commit:

`0120180bd2529e5fbf15848fc782a222bb00e303` (`study_report_1`)

For example, inspect the former receiver or its frozen polynomial settings:

```sh
git show 0120180bd2529e5fbf15848fc782a222bb00e303:work/model/reservoir_model.py
git show 0120180bd2529e5fbf15848fc782a222bb00e303:work/study/polynomial_memory/compact_20_q8.json
```

Replace the path after the colon to inspect any other former artifact. This
preserves access to raw measurements, exact coefficients, seeds, and source code
without retaining the old experiments in the working tree. A Markdown-only copy
of this folder does not itself contain that raw evidence; retain the repository
history if exact recovery matters. No history rewrite or new commit was made
as part of this cleanup.
