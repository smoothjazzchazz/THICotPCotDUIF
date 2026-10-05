# Nonlinear scalar with delay feedback

**Outcome: rejected in this search.**

Hypothesis: a scalar nonlinear element plus a feedback buffer could retain
useful multiple timescales with few nonlinear operations. The causal update is
`new = (1-leak)*previous + leak*f(gain*input + coupling*old_tail)`, followed by
one buffer shift. [`reservoir.py`](reservoir.py) exposes every buffer position
for the fitted linear readout. This is a discrete delay-feedback RC analogue,
not a simulation of a physical time-multiplexed device.
[Appeltant et al.](https://www.nature.com/articles/ncomms1476) motivates the family.

Compared 8/16/32/64 stored states, feedback 0/.3/.6/.9, and tanh versus a sine
variant. No candidate passed nominal decisions. At 32 positions, coupling .3
had 72.6% validation F1, close to the no-feedback control's 72.5%; stronger
feedback did not help. At .6, training-prefix initialization-tail discrepancy
was .055 (limit .03125); 64 positions retained .542. Nonzero memory distances
coexisted with poor decisions. Support would have required retained useful
history, fading initialization, and improved rejection; the sweep falsified
that combination for these settings. Costs include the entire delay buffer.

Reproduce:

```sh
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_screen --family delay
```

[Saved screening](../results/broad-screen/20261005T011146.539052Z/screen.json),
[experiment ledger](../broad_search/LEDGER.md).
