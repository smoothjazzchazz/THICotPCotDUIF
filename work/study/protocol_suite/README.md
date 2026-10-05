# Configurable temporal-recognition study

**Completed synthetic study; no universal winner.** A 16-run Boolean history with
pairwise features and an 8-bit readout is the strongest tested long-context
candidate. Strict run-count rejection catches all tested malformed prefixes, but
reduces noisy clock/data recall. Close unknown patterns remain a weakness.
Read the [report](REPORT.md) before using aggregate scores.

This is research inside `protocol_suite/`. It changes no released design, RTL,
protocol contract, or project gate. All five signal families are explicitly
synthetic; UART/SPI/I²C implementation contracts are still missing locally.

## Results and layout

- [REPORT.md](REPORT.md): recommendation, failures, mechanisms and hardware costs.
- [PLAN.md](PLAN.md) / [LEDGER.md](LEDGER.md): preregistration and retained trials.
- [signals.py](signals.py), [models.py](models.py), [learning.py](learning.py),
  [scoring.py](scoring.py): generators, causal engines, fitting and event matching.
- [receiver.py](receiver.py): sample-at-a-time integer inference and JSON checkpoints.
- [artifacts/frozen/](artifacts/frozen/): recipe, 120 fitted configurations, training
  inputs, source/parameter locks and a copy of the frozen inference sources.
- [artifacts/confirmation/](artifacts/confirmation/): fresh streams, every emitted
  event and per-fit/per-condition metrics, including the held-out family.
- [Full tables](artifacts/analysis/TABLES.md),
  [uncertainty](artifacts/analysis/uncertainty.json),
  [hardware accounting](artifacts/analysis/hardware_accounting.json),
  [representative trace](artifacts/analysis/representative_trace.json),
  [run states](artifacts/analysis/representative_states.json.gz).
- [artifacts/verification/](artifacts/verification/): replay, finite-width arithmetic,
  saved checkpoints and repository-boundary checks.
- [PROVENANCE.md](PROVENANCE.md): origins, environment and accounting revisions.
- `artifacts/{screen,refine,representation_v2,final_development}/`: every development
  fit, threshold trial and arithmetic variant. The failed `representation/` accounting
  run and its exception log are retained.

## Run from the repository root

The wrapper uses the existing `work/study/.venv` (NumPy and Matplotlib), disables
bytecode writes, limits BLAS threads, and puts caches/temp files inside this suite.
No install or external document fetch is needed.

```sh
# Contract, scoring, causality and checkpoint tests
bash work/study/protocol_suite/run.sh -m unittest work.study.protocol_suite.test_suite -v

# Re-evaluate all saved streams/configurations; compare every saved event/metric
bash work/study/protocol_suite/run.sh -m work.study.protocol_suite.verify replay
bash work/study/protocol_suite/run.sh -m work.study.protocol_suite.fixed_width_check

# Rebuild tables and scientific plots from frozen results
bash work/study/protocol_suite/run.sh -m work.study.protocol_suite.analyze

# Cold refit + confirmation + replay in a NEW suite-local directory
bash work/study/protocol_suite/run.sh -m work.study.protocol_suite.reproduce my_reproduction

# Also rerun all development searches (use another new directory name)
bash work/study/protocol_suite/run.sh -m work.study.protocol_suite.reproduce full_reproduction --all-development

```

New experiment directories refuse overwrite. Original `freeze`/`evaluate` outputs
are locked; use `reproduce` to repeat them without replacing evidence. The completed
[cold reproduction](reproductions/cold_check/comparison.json) refit all 120 models
and reproduced all predictions and metrics exactly. It reuses the same seeds, so
it is reproducibility evidence, not another independent confirmation batch.
Reproduction reports and logs are tracked; regenerated replicas and runtime caches
stay local and can be rebuilt with the commands above.

The saved [repository-boundary audit](artifacts/verification/boundary.json) records
the completed study before the subsequent authorized commits. It includes Git
metadata and the original checkout state, so `verify boundary` is only valid
against that original state; it is not a check to rerun after committing or cloning.

For a new development screen only:

```sh
bash work/study/protocol_suite/run.sh -m work.study.protocol_suite.run screen --name my_screen
```

Inference needs only a saved model's `config`, `readout`, and incoming packed
two-lane samples. `Receiver.step(sample)` returns an event or `None`; generator
metadata is never passed to it. The 16-bit study timestamp is distinct from the
released 12-bit symbol-interface contract; integration is future work.
