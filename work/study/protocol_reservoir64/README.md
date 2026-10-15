# Trainable 64-node protocol experiment

Question: can one fixed sparse 64-node recurrent architecture receive reusable
UART and I2C events, then qualify for a USB low-speed data experiment, by loading
weights and configuration? This is a Python experiment, not reference adoption,
RTL, electrical compliance, or a project gate. **Training recurrent weights makes
this a trainable recurrent network, not a conventional fixed-weight reservoir.**

## Source status and scope

The UART, I2C and USB documents in `knowledgebase/placeholders/protocols/` remain
`status: missing`. No external documents were fetched. The profiles below are
explicit experimental assumptions, not checked protocol specifications. Separate
emitters and independent waveform checkers establish internal consistency only.
USB packet fields, CRC polynomials and transaction rules lack filed sources; its
packet emitter/peer must report that block instead of inventing a USB exchange.
A separate NRZI/stuffing diagnostic is not a USB implementation.

## Frozen design and event contract (before training)

Two observed binary lines, always present. Each contributes signed level, signed
transition, and edge age capped at 127 ticks and scaled to [0,1]: six inputs.
No phase counter, supplied boundaries, framing decoder or protocol logic exists
in preprocessing. Exactly 64 synchronous leaky tanh nodes; four recurrent taps
per node (self, ring predecessor, two seeded random distinct taps), topology seed
640031. Dense six-input projection and eight-output linear readout. Leak factors
repeat [1, 1/2, 1/4, 1/8], giving uncoupled retention times from zero to about 7.5
ticks; recurrence can extend or destabilize this, so these are not memory proofs.
Node count, masks, leaks, feature interface and equations are fixed across profiles.

Readout classes: NONE, BIT0, BIT1, START, STOP, FALL, INVALID, BOUNDARY.
UART: START at start-cell center, BIT0/1 for data and parity cell centers, STOP
at a valid stop-cell center, INVALID for a low stop cell. I2C: START/STOP on SDA
edges while SCL stays high, BIT0/1 on SCL rising edges, FALL on SCL falling edges.
These are small events, never whole-message classes. Output includes observation
and decision ticks (equal: no timestamp backdating). NONE produces no event;
INVALID/uncertain produces an explicit event. Consecutive equal winners emit
once, rearmed by NONE or a different winner; repeated identical bits must have
separate events. No hidden message resets. Controller may count events, assemble
bytes, check parity, recognize addresses and operate finite buffers; it receives
no waveform, labels, intended payload or generator state.

Float inference uses float64. Quantized inference uses signed Q12 weights in
int16 (range [-8,8)), signed Q14 states/features, int64 accumulators, round-to-
nearest with ties toward positive infinity, Q15 fixed leaks, saturating states,
and a 4097-entry Q14 tanh LUT over [-8,8] at 1/256 increments. Readout selection
uses integer logits with a fixed configurable top-two margin. No float tanh,
softmax, or matrix product is used in quantized online inference.

## Profiles and qualification

- UART 8N1 and 8E1: idle high, start low, eight least-significant-first data bits,
  optional even parity, one high stop. Nominal 16 ticks/bit; incoming clock ratio
  0.97..1.03, per-cell duration jitter ±1 tick, initial fractional sampling phase.
  Back-to-back frames with optional 0..2 ordinary stop-bit-length gaps, not a
  long framing delimiter. TX is nominal 16 ticks/bit. Two independent weight
  files allowed for N/E parity. Echo FIFO 32 bytes. Deadline: echo completes
  within 1024 ticks of input frame completion. Long fast streams must fit it.
- I2C target: two resolved wired-AND lines with pull-low/release drives, seven-bit
  address 0x32, most-significant-first bytes, ninth-clock ACK, master NACK ends
  reads, repeated START, STOP. Low/high periods independently 8..12 ticks. Target
  stretches SCL by 6 ticks after each acknowledged write byte; master waits on
  resolved SCL (timeout 64 ticks). Target stores up to 4096 recovered bytes,
  ACKs only its address and accepted data, returns stored bytes on subsequent
  reads, and releases on NACK/STOP/invalid events. Response setup deadline:
  6 ticks after observed falling edge, before the earliest 8-tick low completes.
  Timeout recovery: 256 ticks without events during an active transaction.
  Unrelated address and malformed aborted transactions are separate conditions.

Tick order: apply earlier TX commands; peer chooses its drives from prior bus
observations; resolve lines; receiver updates; controller consumes event and
schedules commands for no earlier than next tick; peer observes current bus.
Arithmetic is one abstract simulation update/tick, not measured hardware speed.
Finite scheduling queue: 512 line commands. RX one-event register consumed each
tick, no backlog. All external temporal storage is counted in `cost.json`.

Valid traffic acceptance: exact independently decoded output, zero byte edits,
zero missing/duplicate/wrong events (event timing tolerance 2 ticks), no buffer
errors, all declared response deadlines. Every condition and each training seed
is reported; qualification requires all three trained seeds in both arithmetic
modes to meet all valid-traffic checks. Malformed detection/recovery is separate:
no claim that parity-free framing or I2C detects arbitrary data-bit corruption.
Reservoir-disabled and recurrence-disabled controls use identical test streams.

## Predeclared budget and splits

Three initialization/training seeds: 11, 29, 47. Fixed topology seed 640031.
Per profile: 12 training streams of at least 4096 ticks, four development streams
of at least 4096 ticks; complete independently generated streams and transaction
seeds, never randomly split overlapping windows. Training split seeds 10000+,
development 20000+, final 90000+. Payloads are new per split; the exact reserved
phrase is excluded from training/development. Truncated BPTT chunks 128 ticks,
batch 12, 12 epochs, Adam lr 0.003, gradient norm cap 1.0. State carries between
chunks; reset only at stream/epoch starts. Best epoch by development weighted
cross entropy. No final-test tuning or architecture search. One readout-only
baseline per profile (seed 11), same budget with input/recurrent weights frozen.
Fixed decision margin 0.15 float-logit units. Optimization steps and parameter
changes are saved, including rejected seeds and checkpoints.

Final traffic per profile includes reserved phrase, every byte, 2048 fresh random
bytes, 1024-byte long stream, repeated 00/FF/55/AA and ramp patterns, timing
extremes, unrelated address, malformed input followed by valid recovery, and
idle/rapid-toggle disturbances. Final generation and inference happen only after
source and weights are frozen. No further fitting after this evaluation.
USB fitting is automatically gated on both UART profiles and I2C qualifying;
missing USB packet source is an additional explicit blocker.

## Layout and reproduction

Shared numeric receiver: `work/model/stream_reservoir.py`. Shared finite line
scheduler extends `work/model/transmit_simple_model.py`. The experiment runner
uses a two-line interactive loop because the old one-line `run_simulation`
cannot resolve a bus or feed the peer; all protocols use the same receive and TX
components. Emitters, offline checkers, event-only controllers, fitting and
scoring live here. Existing models and historical artifacts are preserved.

Requires Python 3.10+, NumPy. This checkout has no study venv; the measured run
uses `/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python`. Set `PY` to
that interpreter or your own NumPy environment. From repository root:

```sh
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
$PY -B -m work.study.protocol_reservoir64.run generate --output work/study/protocol_reservoir64/runs/run01
$PY -B -m work.study.protocol_reservoir64.run train --output work/study/protocol_reservoir64/runs/run01
$PY -B -m work.study.protocol_reservoir64.run freeze --output work/study/protocol_reservoir64/runs/run01
$PY -B -m work.study.protocol_reservoir64.run evaluate --output work/study/protocol_reservoir64/runs/run01
$PY -B -m work.study.protocol_reservoir64.run replay --output work/study/protocol_reservoir64/runs/run01 --profile uart_n --mode quantized
$PY -B -m unittest work.study.protocol_reservoir64.test_experiment -v
```

Generation refuses an existing run directory. Freeze stores exact source,
weights, data and hashes. Evaluation refuses a changed freeze or existing final
results. Replay reproduces a saved phrase trace from observations only and checks
event equality. See REPORT.md for measured outcomes and limitations.

## Implementation clarifications filed before final evaluation

The I2C controller holds SCL low for **18 ticks after its response request** on
write ACKs. The resulting stretch beyond the master's low period depends on the
8..12-tick low duration and receiver delay; it is measured, not assumed to be
exactly six ticks. This corrects the shorthand "by 6 ticks" above without
changing the fitted receiver or training budget. Final I2C jitter randomizes
each low/high period in 8..12; two additional asymmetric timing cases and UART
combined mismatch/jitter corners are included. Edge-event timing allows 0..2
ticks after I2C edges; UART center estimates allow ±2 ticks. Cold reset happens
once per independent case, never between its frames, repeated START, or its
write/read transactions. Controls cover the same phrase, every-byte and repeated
patterns in both arithmetic modes for seed 11. The readout-only baseline runs
all final conditions. Neither control is a fallback receive path.

Saved profile JSON selects controller program, timing, buffer limits, weight
files and readout margin. All programs use the same StreamReceiver and scheduled
line transmitter. Protocol-specific controller code is experiment firmware, not
preprocessing. The current discrete event model applies RX arithmetic and the
controller in the observation tick; TX takes at least one additional tick.
