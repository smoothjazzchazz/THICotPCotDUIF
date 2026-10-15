# Six-seed UART with the unchanged I2C receiver

Question: can the shared 64-node, 256-edge receiver learn UART 8N1/8E1 reliably?
The exact original StreamReceiver is imported, including all six generic features,
leaks, state equations, event pulses, margin, arithmetic and timing. Only learned
weights differ. No UART timing state or boundaries enter inference. Controllers,
transmitter, output decoder and assumed timing envelopes remain unchanged.
Previous experiments are hash-protected. This is an opt-in simulation, not a
reference-design change, hardware qualification or electrical-compliance claim.

Before main runs, audit prior labels, 512-tick derivatives, complete-frame credit,
repeated bits, state continuity and batch/online agreement. Compare three initial
weight recipes on two 8,192-tick prefix passes of twelve existing training streams:
previous initialization; input weights ×.2, recurrent nonself weights ×.1,
self weights .95 or 1.05, and NONE output bias .5. These use existing trainable
parameters only. Choose one initialization for both UART profiles by the sum of
profile development protocol selection keys after two passes. Retain every pilot.
Write recipe.json before main fitting. The pilot budget is separate from mains.

Main seeds are 11,29,47,71,101,131 for each UART profile, plus seed11 matched
previous-recipe controls. Every candidate receives 30 full epochs, TBPTT 512,
effective batch 12, previous weighted objective and Adam .003. Exact previous30
train/dev corpora are copied without modification, guaranteeing at least its
transaction exposure and update counts. No final data are used to choose a recipe.
State and generic feature ages continue across transactions/chunks. Epoch starts
are cold independent stream starts as previously. Save every epoch, Adam moments,
step count, ending state, deterministic next position and failure evidence.

Select only epochs 1,3,6,9,12,15,18,21,24,27,30, lexicographically by strict valid
exchanges, byte-exact exchanges, aligned bytes, minimum START/STOP F1, macro F1,
negative false-event rate, negative dev loss. Cold-start events count. Exact ties
retain earlier epochs. Compare epochs 18/21/24 with 24/27/30: >=1 strict/exact
exchange, >=.01 byte/boundary/macro gain, or >=2% loss reduction means
training-limited / not converged; otherwise plateau for this recipe, not capacity.

Live development seeds use 40,000,000+, final seeds 50,000,000+, profile offsets
100,000 and case offsets 90,001. Prior final seed families are excluded. Final
payloads include the reserved House Improvement Committee (final-only), every
byte, 2,048 random bytes, 1,024-byte messages, constant/pattern runs, back-to-back
and gapped frames, timing ratios .97/1.03, jitter and combined corners, malformed
stops/parity, disturbances and recovery. Freeze all sources/config/weights before
final generation. Evaluate float and quantized complete waveform paths separately,
retain seed11 disabled/no-recurrence controls and fresh frozen-64-node I2C checks.
Fix harness jitter routing (no receiver changes) and verify actual emitted cells.

From repository root:

```sh
export OPENBLAS_NUM_THREADS=1
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
OUT=work/study/protocol_reservoir64_uart6_training30/runs/run01
$PY -B -m work.study.protocol_reservoir64_uart6_training30.run generate --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_uart6_training30.investigation "$OUT"
$PY -B -m work.study.protocol_reservoir64_uart6_training30.pilot_replay "$OUT"
$PY -B -m work.study.protocol_reservoir64_uart6_training30.validation pre_main "$OUT"
$PY -B -m unittest work.study.protocol_reservoir64_uart6_training30.test_experiment -v
$PY -B -m work.study.protocol_reservoir64_uart6_training30.run audit --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_uart6_training30.run train --output "$OUT" --workers 6
$PY -B -m work.study.protocol_reservoir64_uart6_training30.run freeze --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_uart6_training30.run evaluate --output "$OUT" --workers 6
$PY -B -m work.study.protocol_reservoir64_uart6_training30.run report --output "$OUT"
$PY -B -m work.study.protocol_reservoir64_uart6_training30.run verify --output "$OUT"
```
