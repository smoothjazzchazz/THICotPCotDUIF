# Shared study code

The original readout-comparison, mixed-leak, and delay-chain experiments use
these helpers:

- [signals.py](signals.py): labeled pulse-order streams and the conventional listener.
- [comparison.py](comparison.py): collect states, fit readouts, choose settings,
  measure events, and verify streaming replay.
- [report.py](report.py): common comparison plots and HTML reports.
- [test_comparison.py](test_comparison.py): causal labels, event counting, and replay checks.

The reservoir model lives in [work/model/](../../model/README.md).
See the [study index](../README.md) for experiment runners and verification commands.

The separate [broader search](../broad_search/README.md) adds [broad.py](broad.py)
for causal alternative reservoirs, four-class fitting, coefficient quantization
and snapshot replay, and [resources.py](resources.py) for analytical resource
accounting. It reuses the original `signals.py` and `comparison.py` event rules;
the historical helpers and model remain unchanged.

The [protocol study suite](../protocol_suite/README.md) is an empty scaffold for
future work that can reuse these helpers. It has no evaluation code yet.
