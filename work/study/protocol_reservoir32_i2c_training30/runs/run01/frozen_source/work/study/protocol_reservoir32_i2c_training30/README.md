# 32-node sparse I2C, matched 30-epoch training

Question: how does halving the trained recurrent state from 64 to 32 nodes affect
I2C waveform recognition and response at the same tick timing and training budget?
This is a separate experiment; both earlier studies and shared models are read-only.
UART is excluded from training and evaluation. USB remains out of scope.

## Preregistered comparison

Exactly 32 recurrent nodes, four incoming taps each: self, ring predecessor, two
seeded distinct random taps. Topology seed remains 640031; resizing generates a
new fixed graph with 128 connections (12.5% density). Fan-in stays four, rather
than preserving the old 6.25% density. Six generic inputs, eight event classes,
leaks [1,.5,.25,.125] repeated eight times, tanh update, weight initialization
distributions, float64 and integer inference equations, .15 decision margin,
and duplicate-event suppression retain their previous definitions. Dense input
and readout projections scale with node count. Input/recurrent/readout weights
and biases are all trained; this is a sparse trainable recurrent network.

The original live I2C peer, controller, transmitter, independent waveform decoder,
event scorer and acceptance gates are reused. One receiver update per simulation
tick, low/high intervals 8..12 ticks, target stretch request 18 ticks, response
setup deadline 6 ticks, address 0x32, 4096-byte storage and 512-command scheduler
stay unchanged. There is no established physical Hz value to change or claim.
No message boundaries, intended payloads or labels enter inference.

Use byte-identical train/dev I2C corpora from protocol_reservoir64_training30/run01:
12 training streams, 467,802 nonpadding ticks, of which 459,385 are transaction
ticks; 105 complete generated exchanges. Four development streams and the same
live development cases are reused for a controlled architecture comparison.
Continuous receiver state crosses chunks/transactions; only independent stream
starts at each epoch reset state. Padding is loss-masked.

Main seeds 11,29,47 plus original-loss seed 11 each receive all 30 epochs,
512-tick TBPTT, batch 12, 2,820 Adam updates, lr .003, betas .9/.999, epsilon 1e-8,
gradient norm cap 1 and coefficient clipping [-7.99,7.99]. Each candidate sees
14,034,060 nonpadding tick presentations (13,781,550 transaction presentations).
No early stopping, learning-rate schedule, or final-driven tuning. Main loss
uses the previous class weights multiplied by [1,2,2,4,4,1,4,1]; the control uses
the unchanged original class-weight formula. No new training-recipe search.

Every epoch saves weights, Adam moments, continuation state and train/dev metrics.
Complete development exchanges run at epochs 1,3,6,9,12,15,18,21,24,27,30.
The previous lexicographic selection rule is unchanged: strict valid exchanges,
byte-exact valid exchanges, aligned delivered bytes, minimum START/STOP F1,
macro F1, negative false-event rate, negative development loss. Ties retain the
earlier epoch. The previous late-epoch convergence rule also remains unchanged:
compare means over 18/21/24 versus 24/27/30; >=1 more strict/exact exchange,
>=.01 more aligned-byte fraction/boundary/macro F1, or >=2% relative loss reduction
is 'training-limited / not converged'. A plateau does not establish capacity.

## Freeze and final evaluation

Audit labels, gradients, dynamic shapes, batch/online equality, state continuity,
integer arithmetic and resumable optimization before main training. Freeze all
sources/data/weights/selections before generating fresh final traffic. Use final
seed base 4,000,000 (I2C case family 4,290,000+), disjoint from all previous final
and fitting seed spaces. The reserved phrase remains final-only. Keep all original
14 final conditions and sizes: phrase, all byte values, 2048 random bytes, 1024
long-message bytes, 512 pattern bytes, timing corners, repeated START, STOP/read,
foreign address, malformed/recovery and disturbances.

Evaluate 32-node candidates and the already selected, frozen 64-node I2C models
on identical new final cases, separately in float and quantized arithmetic.
This is a paired fresh evaluation; the old 64-node models are never refitted.
Keep seed-11 32-node disabled/no-recurrence controls on phrase/all-byte/pattern
cases. Valid qualification requires exact output, zero event errors, no overflow,
no missed response deadline and all three main seeds in both arithmetic modes.
Report negative/recovery cases separately. Save traces including failures.

These are the original assumed simulation profiles, not protocol/electrical
compliance or hardware timing/area evidence. No reference design or project gate
is modified. Logical resource reductions are separated from unchanged lookup
ROM, controller and buffering costs.

## Reproduce from repository root

```sh
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
OUT=work/study/protocol_reservoir32_i2c_training30/runs/run01
export OPENBLAS_NUM_THREADS=1
$PY -B -m work.study.protocol_reservoir32_i2c_training30.run generate --output "$OUT"
$PY -B -m work.study.protocol_reservoir32_i2c_training30.run audit --output "$OUT"
$PY -B -m unittest work.study.protocol_reservoir32_i2c_training30.test_experiment -v
$PY -B -m work.study.protocol_reservoir32_i2c_training30.run train --output "$OUT" --workers 3
$PY -B -m work.study.protocol_reservoir32_i2c_training30.run freeze --output "$OUT"
$PY -B -m work.study.protocol_reservoir32_i2c_training30.run evaluate --output "$OUT" --workers 3
MPLCONFIGDIR=/tmp/protocol32-mpl $PY -B -m work.study.protocol_reservoir32_i2c_training30.run report --output "$OUT"
$PY -B -m work.study.protocol_reservoir32_i2c_training30.run verify --output "$OUT"
```

Training resumes from the last fully committed epoch/optimizer checkpoint before
freeze. A partial interrupted epoch is repeated from its saved beginning. Failures
retain diagnostic state. Continuation beyond this preregistered budget belongs in
a new run, using the saved moments/weights and documented epoch-start state rule.
