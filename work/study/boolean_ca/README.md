# Online Boolean cellular reservoir

**Outcome: rejected in this search.** This is a limited sweep, not a claim that
cellular reservoirs generally fail.

Hypothesis: fixed local Boolean evolution could supply inexpensive nonlinear
memory. [`reservoir.py`](reservoir.py) updates all cells from the previous tick,
then overwrites seeded input locations using the current pin sample. Rules 90,
110 and 150 were compared in a 64-cell ring and a directed local arrangement,
with four injected locations and the same explicit-unknown ridge readout.
[Yilmaz](https://arxiv.org/abs/1410.0162) establishes the CA-reservoir family;
our online injection and task differ from that paper.

Support would require useful class separation AND initialization forgetting;
large state distances alone are insufficient. Best screening F1 was 63.4%
(rule-90 directed case), versus 96.9% for 24-sample quadratic memory on the same
validation inputs. None passed the nominal decision probes. Rule-110 directed
and rule-150 variants retained initialization differences. Other variants forgot
the extreme initial vectors, yet their readouts still failed nominal targets.
Saved cross-prefix distances were nonzero: these failures are not explained
simply by exact state collisions. Rule-90 parity features can change sharply
under a one-sample perturbation; this is a mechanism hypothesis, not a proof
that every observed error was caused by parity sensitivity.

Reproduce from the root:

```sh
OPENBLAS_NUM_THREADS=1 work/study/.venv/bin/python -B -m work.study.broad_search.run_screen --family ca
```

Detailed configurations, decisions, initialization gaps and metrics:
[screening evidence](../results/broad-screen/20261005T011146.539052Z/screen.json).
All runs and rejection reasons are indexed in the [ledger](../broad_search/LEDGER.md).
