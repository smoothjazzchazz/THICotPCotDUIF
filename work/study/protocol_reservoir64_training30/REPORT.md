# Stronger training, fixed 64-node architecture

**The previous failure was not evidence that 64 nodes cannot handle the declared
I2C task.** With the expanded training setup, seed 47 and the seed-11 original-loss
control pass every valid I2C final condition in both arithmetic modes. **UART
remains unresolved, and training adequacy is not established.** The full
all-seeds UART/I2C qualification still fails; USB remains gated.

All nine main candidates and three original-loss controls completed 30 epochs:
360 saved weight/optimizer checkpoints, 28,800 updates, and 160,436,400 non-padding
tick presentations. No main run had a numerical failure. Exactly 64 nodes,
256 recurrent connections, six features, leaks, float/integer arithmetic,
decision margin, event rules, controllers, buffers and timing envelopes remain
unchanged. Hash checks confirm all 379 original files are preserved.

## Budget and experimental control

| Profile | Original nonpadding ticks / updates | New transaction / nonpadding ticks | New updates | Exposure / update ratio |
| --- | ---: | ---: | ---: | ---: |
| uart_n | 64,937 / 552 | 412,943 / 444,355 | 2,250 | 6.36x / 4.08x |
| uart_e | 71,488 / 600 | 398,957 / 424,813 | 2,130 | 5.58x / 3.55x |
| i2c | 75,903 / 600 | 459,385 / 467,802 | 2,820 | 6.05x / 4.70x |

Each candidate uses 12 streams, a 512-tick gradient window, and 30 full passes.
State carries across chunks and transactions. Idle and padding do not count
as transaction exposure; padding is loss-masked. The exposure ratio above uses
all original nonpadding ticks as its denominator. Unique counts mean generated
sample positions, not distinct binary substrings. Repeated presentations equal
unique ticks × 30 per candidate. Padding and actual exposure are recorded in
[exposure.json](runs/run01/exposure.json).

The main loss upweights bit events 2x and START/STOP/INVALID 4x relative to the
original formula. Original-loss seed 11 receives identical expanded data and
updates. Adam's learning rate remains .003. I2C training now uses the existing
live peer/controller against an offline reference observer, covering actual SDA
response timing and stretching. Thus the experiment tests a **stronger training
setup**; it does not isolate epoch count, window length, data volume and bus-timing
coverage as separate causal factors.

## Fresh final results

Float and quantized results have the same byte-exact and strict case counts:

| Candidate | Original exact / strict cases | Follow-up exact / strict cases | Reserved phrase |
| --- | ---: | ---: | --- |
| UART 8N1, each main seed | 0/10 / 0/10 | 0/10 / 0/10 | Failed |
| UART 8E1, each main seed | 0/10 / 0/10 | 0/10 / 0/10 | Failed |
| I2C seed 11 | 10/12 / 0/12 | 12/12 / 0/12 | Exact |
| I2C seed 29 | 2/12 / 0/12 | 12/12 / 0/12 | Exact |
| I2C seed 47 | 10/12 / 0/12 | 12/12 / 12/12 | Exact |
| I2C original-loss control, seed 11 | Not run previously | 12/12 / 12/12 | Exact |

Both new UART original-loss controls also returned zero bytes. Every I2C
candidate delivered all 4,571 valid data bytes per mode, including 2,048 random
bytes, a 1,024-byte message, all byte values, repeated patterns and all timing
corners. The I2C denominator includes one correctly rejected foreign address.
The phrase was excluded from fitting/calibration. Final transaction/payload seeds
were fresh and disjoint; fixed every-byte/pattern/phrase challenges intentionally
remain comparable to the old run.

I2C seeds 11/29 have **one extra event at tick zero in every case**: INVALID for
11, BIT1 for 29. All expected events were correctly recovered. These startup
failures remain strict failures. Seed 47 and the original-loss control had zero
event errors, including malformed/recovery and disturbance cases. All I2C
candidates recovered after those disturbances; no buffer overflow or I2C response
deadline miss occurred. Matched response latency was one tick; stretch waits
reached 11 ticks. These are simulation measurements.

UART improvement was inconsistent. Float 8N1 event recall changed from
10.9/37.1/18.8% to 45.1/57.6/17.3% for seeds 11/29/47, without delivering a byte.
Selected 8E1 recall worsened from 25.6–32.6% to 9.0–10.8%. The predeclared rule
selects some UART epoch-3 checkpoints because no checkpoint delivers a complete
development exchange and boundary F1 later deteriorates. **Every candidate still
trained through epoch 30**; epoch-12/30 progression is retained separately. This
selection outcome is evidence of an objective/behavior tradeoff, not successful
UART learning. [Selections](runs/run01/selection.json),
[original comparison](runs/run01/analysis/original_comparison.json).

All 36 reservoir-disabled/no-recurrence matched controls failed byte delivery
and strict acceptance. These controls establish dependence for the retained
weights, not universal necessity of recurrence.

## Is training adequate?

**Ten of twelve runs are “training-limited / not converged” under the predeclared
late-epoch rule.** UART 8N1 main seed 11 and UART 8E1 original-loss seed 11 plateau
under this recipe. Neither plateau establishes a 64-node capacity limit.
I2C's late loss fell about 39–40%; task behavior was mostly flat, although seed
47 first cleared the strict development checks at epoch 30. Decreasing loss
alone is distinguished from improving protocol behavior.

The failure investigation found:

- **Supervision:** UART cell centers, values and parity labels passed independent
  reconstruction; I2C labels match the observed edge contract. Two clean jittered
  UART examples defeated the fixed-period conventional decoder; their exact
  cell labels passed, and both failures remain recorded. Rare boundaries and
  absent BOUNDARY/I2C INVALID teacher classes are explicit in the audit.
- **Optimization and timing:** analytical gradients passed 512-tick finite
  differences. On one fixed development prefix per UART profile, epoch-30
  STOP-logit sensitivity to states 176 ticks earlier was only 2.6e-7–1.5e-4 of
  zero-lag sensitivity across seeds. A longer window therefore did not guarantee
  useful long-range credit. This is a limited diagnostic, not a capacity proof.
- **Representation/readout:** on the first development stream at epoch 30,
  STOP was the top class at only 13–35% of its true centers; allowing ±2 ticks
  raised that to at most 39%. Weak class separation remains, beyond a simple
  timestamp offset. State/gradient diagnostics are retained without claiming
  an unavoidable state collision.
- **Objective and quantization:** the original-loss I2C control passes where
  the upweighted seed-11 recipe retains a startup false event. More boundary
  weight was not uniformly beneficial. Float/quantized I2C outcomes agree;
  UART fails in both, so quantization is not the primary demonstrated blocker.

Resume improving checkpoints and test startup exposure / temporal-credit
optimization before declaring architecture failure. A layered 64-node comparison
is reasonable as a separate measured hypothesis after a repeatable plateau or
a targeted memory/representation diagnosis motivates it. This run gives no
capacity-based reason to replace the I2C architecture. Any layered comparison
needs equal total nodes, explicit extra state/cost, fresh held-out seeds and the
same gates. No reference design or project phase is changed here.

## Evidence and reproduction

- [Preregistered recipe and full commands](README.md),
  [source/data/weight hashes](runs/run01/freeze.json),
  [all weights and resumable optimizer states](runs/run01/models/).
- [Learning curves, with epoch 12 marked](runs/run01/analysis/learning_curves.png),
  [304 per-condition rows](runs/run01/analysis/per_condition.csv),
  [convergence](runs/run01/analysis/convergence.json),
  [diagnostics](runs/run01/analysis/diagnostics.json),
  [complete waveform traces](runs/run01/final/traces/),
  [waveform figure](runs/run01/analysis/phrase_waveforms.png).
- [Preflight](runs/run01/audit/preflight.json),
  [retained checker misses](runs/run01/audit/checker_timing.json),
  [preflight implementation fixes](runs/run01/audit/preflight_notes.json).
- **39 tests passed:** [15 experiment tests](runs/run01/study_tests.log) and
  [24 shared-model tests](runs/run01/model_tests.log). All 360 weight files satisfy
  the fixed topology; all 12 initializations/selections match. Six actual
  epoch-29→30 continuation replays reproduce weights, Adam moments and ending
  states exactly. All 24 saved phrase traces replay exactly from observations.
  [Weight audit](runs/run01/audit/architecture_check.json),
  [continuation audit](runs/run01/audit/resume_check.json),
  [trace audit](runs/run01/analysis/phrase_replays.json).
- [Resource costs](runs/run01/final/cost.json) and
  [inherited storage-accounting clarifications](runs/run01/audit/inherited_cost_clarifications.json):
  1,224 learned coefficients; 2,448 bytes if packed as int16; 1,152 sparse MACs
  per tick versus 4,992 in the current dense NumPy computation. No added inference
  memory, synthesis result, hardware clock or electrical compliance is claimed.
  [USB: zero fitting steps](runs/run01/final/usb_status.json).

From repository root, after the README's generation/training/freeze/evaluation
commands, reproduce the analysis with:

```sh
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
OUT=work/study/protocol_reservoir64_training30/runs/run01
export OPENBLAS_NUM_THREADS=1
MPLCONFIGDIR=/tmp/protocol64-training30-mpl $PY -B -m work.study.protocol_reservoir64_training30.run report --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_training30.runs.run01.audit.original_comparison
$PY -B "$OUT/analysis/finish_report.py"
$PY -B -m work.study.protocol_reservoir64_training30.run verify --output "$OUT"
```

Protocol sources remain unfiled; these are the original assumed simulation
profiles. The original and follow-up final datasets differ, so changes are
condition-matched evidence, not paired measurements on identical random traffic.
