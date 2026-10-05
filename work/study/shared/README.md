# Shared study code

All three experiments use these helpers:

- [signals.py](signals.py): labeled pulse-order streams and the conventional listener.
- [comparison.py](comparison.py): collect states, fit readouts, choose settings,
  measure events, and verify streaming replay.
- [report.py](report.py): common comparison plots and HTML reports.
- [test_comparison.py](test_comparison.py): causal labels, event counting, and replay checks.

The reservoir model lives in [work/model/](../../model/README.md).
See the [study index](../README.md) for experiment runners and verification commands.
