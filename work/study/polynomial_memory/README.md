# Polynomial input memory (NGRC)

**Hypothesis:** a finite delay line retains the first pulse, and pairwise input
products make its relationship with the second pulse accessible to a linear
readout. Separating retention from nonlinear expansion is the key control.

[`reservoir.py`](reservoir.py) shifts the signed current sample into N memory
slots, then emits N linear terms and every distinct pair product. With N=20 this
is 20 state samples and 210 readout features (190 products). No boundaries,
labels, pulse-width counter, feature-age counter, or future samples enter the
receiver. State continues through all patterns. A four-output ridge readout
scores classes 0, 1, background and unknown; score/margin rejection and the
unchanged stabilizer produce events. The final candidate uses quantized integer
coefficients. Fitting is off-chip and floating point.

This is reservoir computing under the **next-generation RC / NVAR convention**,
not a recurrent nonlinear reservoir. The nonlinear expansion follows a linear
input-memory reservoir. See [Gauthier et al.](https://www.nature.com/articles/s41467-021-25801-2)
and the [critical discussion](https://www.nature.com/articles/s41467-021-27715-5).
It is also accurately described as a quadratic finite-memory filter with a
trained readout. We do not claim a novel general RC algorithm.

## Measured development evidence

The screen compared linear histories of 8, 16, 32, 64 and 128 samples, and
quadratic histories of 16, 24 and 32. Linear memory alone remained inadequate.
Follow-up compared 20/24/28/32/40 samples, explicit unknown training, training
augmentation, age-carrying input, and 4/6/8/10/12/16-bit readout coefficients.

On identical larger development streams (4,608 patterns), the 20-sample model
with 8-bit coefficients reached 90.0% F1 and 95.1% unknown recall; clean metrics
were 100%. The matched augmented linear model reached only 63.2% F1. An implicit
unknown readout reached 90.2%: an explicit unknown output is **not the main cause**
of the gain. Four-bit coefficients failed (50.7% F1); six bits reached 88.8%.
The age-input variant reached 71.8% F1. All these are development observations.

For frozen confirmation results, limitations and costs, use the
[research report](../broad_search/REPORT.md). A 20-sample horizon is finite: longer
or ambiguous waveforms can still collide. This study establishes one synthetic
loaded line code, not arbitrary protocol recognition or hardware feasibility.

## Reproduce

From the repository root (set BLAS threads to avoid small-solve overhead):

```sh
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_screen --family polynomial
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_robust
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_quantized
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_ablations
```

Each command creates a unique new result directory. The last two use the saved
preceding stage. [The study runner](../broad_search/README.md) documents the full
sequence, frozen replay, tests, ledger and artifacts.
