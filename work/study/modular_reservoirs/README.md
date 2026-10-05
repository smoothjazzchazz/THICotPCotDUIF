# Size, topology and multiple-reservoir controls

**Outcome: promising on the original validation distribution, rejected as the
selected robust implementation.**

Hypothesis: connection structure, input placement and timescales matter more
than node count alone. [`reservoir.py`](reservoir.py) uses fixed random weights
and fitted readouts. The screen measures 8/16/32/64/128-node sparse networks;
32-node rings, local neighborhoods and skip connections; and equal-total-size
32-node arrangements with two parallel, stacked, weakly coupled or specialized
16-node reservoirs. Specialized halves receive level versus edge/age features.
The second half uses a slower leak in the multiple-reservoir configurations;
these comparisons change both arrangement and timescale, not topology alone.
All use the same causal `FeatureExtractor` and shared evaluation.

A 32-node ring reached 87.7% validation F1, versus 67.0% for 128 sparse nodes.
The parallel/stacked/coupled/specialized arrangements reached 85.6/82.2/83.2/76.7%
on the same original validation. These do not establish an advantage from using
multiple reservoirs. Follow-up repeats all five arrangements with seeds 31/32/33,
and changes leak, nonlinearity (tanh/clipped) and state precision (4/6/8 bits).
Support would require improvement across seeds at comparable storage and useful
rejection under stress. The [validation evidence](../results/broader-validation/20261005T011251.428831Z/validation.json)
records seed variability and failures; rounded recurrent state introduced
initialization/probe failures in some otherwise promising float configurations.

Reproduce:

```sh
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_screen --family modular
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_validate
```

[Shared ledger and comparison](../broad_search/LEDGER.md). Floating-point results
are not evidence for an equivalent six-bit implementation or synthesized area.
