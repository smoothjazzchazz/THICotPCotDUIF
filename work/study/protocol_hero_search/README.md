# Protocol reservoir shape search

This isolated, opt-in receive experiment executes [the supplied plan](PLAN.md).
It does not adopt an architecture into v0.31 or qualify hardware. Weights are
demonstration configurations. Historical experiments and unrelated changes are
preserved. Float reception is the primary gate; quantization is a separate result.

The common path is three sampled lanes → levels, signed edges and capped ages →
fixed-shape recurrent network → learned events → event-only message assembler.
Neither inference nor assembly receives generator boundaries. UART groups are an
offline evaluation convention. All reservoir layers and branches count as nodes.

Read [requirements and hypotheses](RESEARCH.md), [protocol choices](PROFILES.md),
and the eventual `REPORT.md` before interpreting scores. A broad screen or an
improving interrupted fit is not a qualified architecture or a capacity failure.

The executable entry point is `python -m work.study.protocol_hero_search.run`.
Run artifacts include source hashes, fixed masks, configurations, every training
checkpoint with Adam state, exposures, development decisions, failures and traces.

## Files and commands

| File | Responsibility |
| --- | --- |
| `shapes.py` | Fixed physical connections, initialization, and shared generic features |
| `network.py`, `kernel.cpp` | Streaming learned inference, BPTT kernel and separate integer replay |
| `data.py` | Offline waveform generation, independent labels, event-only assembly and scoring |
| `training.py` | Curriculum, Adam, continuations, rescue policy and resumable checkpoints |
| `run.py` | Broad screen and development-only advancement |
| `evaluation.py` | Freeze, fresh confirmation, rejection/recovery and diagnostic controls |
| `test_experiment.py`, `validation.py` | Contracts, gradients, integer reference, replay and artifact preservation |
| `report.py` | Measured tables, costs, diagrams, example weights and report |

Quick verification from the repository root:

```sh
export OPENBLAS_NUM_THREADS=1
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
$PY -B -c 'from work.study.protocol_hero_search.network import compile_kernel; compile_kernel()'
$PY -B -m unittest work.study.protocol_hero_search.test_experiment -v
```

The completed run's [report](REPORT.md) contains the full reproduction sequence.
Use a new output directory for a rerun. Do not alter frozen selection rules or
weights after confirmation. `runs/run01/demonstration_configs/` contains examples;
`runs/run01/models/` retains all seeds and failed/improving trials.
