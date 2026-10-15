# Fixed architecture, stronger training

Question: was the original UART/I2C result limited by training? This follow-up
imports the original 64-node receiver, feature encoder, arithmetic, topology,
leaks, decisions, controllers, transmitter and independent checkers unchanged.
The original experiment and frozen run are read-only. No reference adoption or
project gate is claimed. Protocols remain the same assumed simulation profiles;
external protocol sources and USB qualification remain missing.

## Preregistered recipe

Each profile (UART 8N1, UART 8E1, I2C) receives fresh seeds 11, 29, 47 and a seed-11
original-loss control. All 12 candidates run 30 complete epochs. Adam is the
original implementation: learning rate .003, betas .9/.999, epsilon 1e-8, global
gradient norm cap 1, coefficient clipping [-7.99,7.99], fixed masked recurrence.
No learning-rate schedule, early stopping, or architecture search.

TBPTT is 512 ticks; batch size is 12 streams. State is carried across every chunk
and transaction; only gradients are truncated. As in the original, independent
streams start cold at each epoch. No transaction boundaries reach inference.
Each stream has at least 32,768 **transaction ticks**, excluding added idle and
batch padding. This stricter count must exceed four times the original total
non-padding ticks per profile. Padding is loss-masked and does not satisfy the
budget. All valid ticks are presented once per epoch. Total updates must be at
least twice the original candidate's 12-epoch total; generation checks both
requirements before fitting. Counts and sample presentations are saved separately.

Original loss: min(12, sqrt(max class count / class count)), computed on this new
corpus. Main loss multiplies that vector by [1,2,2,4,4,1,4,1] for
NONE/BIT0/BIT1/START/STOP/FALL/INVALID/BOUNDARY. These are training-only weights;
event pulses, margin .15, timestamps and scoring tolerance remain unchanged.
The original-loss control gets identical data, initial weights and update budget.

Training streams concatenate complete varied transactions without state resets.
UART includes random bytes, repeated bytes, 00/FF/55/AA, short/long batches,
back-to-back frames, gaps, parity errors, low stops, clock ratio .97..1.03 and
cell jitter 0/1. I2C examples are emitted by the original live master against a
test-only edge observer and the original target controller, with observer delay
0..2, low/high 8..12, jitter, real target stretching, ACK/NACK, repeated START,
STOP/read, unrelated addresses and malformed/recovery. This changes training
sampling, including matching the live bus's response timing; it changes no
inference mechanism. Ground-truth events are used only to create offline data.
I2C negative rapid transitions and idle prefixes accompany recovery examples.

Whole-transaction seed spaces are train 1,000,000+, dev 2,000,000+, final
3,000,000+, with nonoverlapping 100,000-profile and 1,000-stream offsets.
The original 10,000/20,000/90,000 spaces are excluded. The reserved phrase
`House Improvement Committee` is final-only. Every-byte and fixed patterns are
deliberate shared condition types, not claims of novel byte values.

## Selection, convergence and final testing

Every epoch saves weights, Adam first/second moments, step count, ending recurrent
state, deterministic continuation position and history. Each epoch records
online training loss and fixed-weight development loss plus emitted-event
precision/recall by class and false events. Complete live development exchanges
run at epochs 1,3,6,9,12,15,18,21,24,27,30. Only these epochs can be selected.
Selection lexicographically maximizes: strict passing valid exchanges; byte-exact
valid exchanges; correctly aligned delivered bytes; minimum START/STOP F1; macro
F1 across supervised event classes; negative false-event rate; negative dev loss.
Exact ties retain the earlier epoch. No final data enter selection.

Training adequacy compares epochs 18/21/24 with 24/27/30: any improvement of
>=1 strict/byte-exact exchange, >=1 percentage point aligned-byte fraction or
boundary/macro F1, or >=2% relative dev-loss reduction means
**training-limited / not converged**. Otherwise report a plateau for this recipe,
then inspect objective/control differences, gradients, event timing, state
separation/saturation and float/quantized differences. Neither result proves a
64-node capacity limit. Resumable checkpoints remain available.

After all 30 epochs, freeze source, data, config, selection and checkpoints.
Final conditions retain the original payload sizes (2,048 random, 1,024 long,
all 256 bytes, 512 pattern bytes), phrase, timing corners, malformed/recovery,
rejection, buffering and response deadlines. Use new payload/transaction seeds.
Both arithmetic modes use complete waveform paths and independent decoding;
I2C uses the live peer. Seed-11 disabled/no-recurrence controls retain matched
phrase/every-byte/pattern conditions. No gate thresholds are weakened. Final
evaluation is resumable by completed condition, with no fitting after freeze.

## Reproduction

From repository root, set `PY` to a Python environment with NumPy/Matplotlib:

```sh
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
export OPENBLAS_NUM_THREADS=1
OUT=work/study/protocol_reservoir64_training30/runs/run01
$PY -B -m work.study.protocol_reservoir64_training30.run generate --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_training30.run audit --output "$OUT"
$PY -B -m unittest work.study.protocol_reservoir64_training30.test_training -v
$PY -B -m work.study.protocol_reservoir64_training30.run train --output "$OUT" --workers 3
$PY -B -m work.study.protocol_reservoir64_training30.run freeze --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_training30.run evaluate --output "$OUT" --workers 3
$PY -B -m work.study.protocol_reservoir64_training30.run report --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_training30.run verify --output "$OUT"
```

`train` resumes at the next full epoch using the last optimizer checkpoint.
Epoch checkpoints describe exactly how state is initialized for continuation;
an interrupted partial epoch is rerun from its beginning. Numerical failures
retain the current weights, optimizer, incoming state, chunk position and error.
