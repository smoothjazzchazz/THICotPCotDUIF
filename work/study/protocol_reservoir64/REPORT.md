# Fixed 64-node protocol experiment — measured result

**The shared architecture did not qualify for UART and I2C.** It demonstrated
some complete I2C write/readback exchanges, including the exact reserved phrase,
but did not produce a UART echo. USB weight fitting correctly remained stopped.
This is evidence about one bounded training run, not proof that 64 nodes cannot
solve the task.

The UART/I2C framing rules are explicitly assumed simulation profiles. Their
project source placeholders remain missing. Separate checkers establish internal
consistency, not verified protocol or electrical compliance. No external protocol
documents, reference specifications, RTL, historical results or project gates
were changed.

## What was implemented and run

One two-line receiver uses exactly 64 leaky recurrent nodes and one fixed sparse
256-connection pattern. Six generic level/edge/age features enter it; no waveform
decoder, frame reset, supplied boundary or intended byte reaches the controller.
Events represent individual bits and boundaries. Repeated identical bits need
separate events. Controllers assemble bytes, check UART parity, recognize I2C
addresses, and request a shared finite deterministic output scheduler.

UART supports the declared 8N1 and 8E1 echo profiles. I2C implements a live
pull-low/release bus, ACK/NACK, repeated START, write storage, subsequent reads,
and clock stretching. The read data comes from bytes recovered by the model.
An independent decoder reads the actual outgoing UART waveform or resolved I2C
bus; internal recognition alone never counts as delivery.

Off-chip BPTT optimized input, recurrent and readout weights, with numerical
gradient checks. This is a **trainable recurrent network**, rather than a
conventional fixed-weight reservoir. Nine trained candidates (three profiles ×
seeds 11/29/47) and three readout-only baselines each received the declared
12-epoch budget. Total: 7,008 optimizer steps and 10,191,744 training sample
presentations including repeated epochs. Every checkpoint was retained. All
selected checkpoints were epoch 12; this budget did not establish convergence.
Training/development whole-stream seeds were disjoint; the phrase appeared only
in final testing. Sources, configurations, datasets and weights were frozen
before final generation. Nothing was refitted after final evaluation.

## End-to-end results

Each UART candidate was tested on 4,507 valid input bytes across ten conditions.
Each I2C candidate attempted 4,571 valid data bytes across eleven write/read
conditions plus an unrelated-address negative case. Tests included 2,048 fresh
random bytes, every byte value, a 1,024-byte message, repeated-bit patterns,
clock mismatch, timing corners, and separate malformed/recovery cases.

| Profile / training seed | Float byte-exact cases | Quantized byte-exact cases | Exact phrase, float / quantized | Full gate |
| --- | ---: | ---: | --- | --- |
| UART 8N1 / 11, 29, 47 (each) | 0/10 | 0/10 | No / No | Failed |
| UART 8E1 / 11, 29, 47 (each) | 0/10 | 0/10 | No / No | Failed |
| I2C / 11 | 10/12 | 10/12 | Yes / Yes | Failed |
| I2C / 29 | 2/12 | 2/12 | No / No | Failed |
| I2C / 47 | 10/12 | 10/12 | Yes / Yes | Failed |

Byte-exact cases do **not** imply the stricter zero-event-error qualification.
The I2C denominator includes correctly declining the unrelated address. Seed 29's
other byte-exact case was the slow-clock condition. Seeds 11/47 returned 4,315
valid data bytes each; seed 29 returned 128, in each arithmetic mode. **No UART
candidate returned any byte.** No buffer overflow occurred in these benchmarks.

The required successful I2C path for seeds 11/47, in both arithmetic modes, was:

```text
"House Improvement Committee" → master's write waveform
  → 64-node learned receiver → timed bit events → 27 recovered stored bytes
  → master's later read → deterministic target waveform
  → independent bus decoder → "House Improvement Committee"
```

Full phrase waveforms, events, recovered bytes, enable signals and command logs
are saved for all 18 trained profile/seed/arithmetic combinations, including all
failures. [View the waveform figure](runs/run01/final/phrase_waveforms.png).

## What failed and what limits the next step

**UART failed at event recovery.** Across seeds, valid-event recall was
10.90–37.10% for float 8N1 and 25.58–32.57% for float 8E1. Quantized ranges were
10.87–36.71% and 25.52–33.23%. No correctly timed STOP event was recovered by
any float candidate; START and repeated bit timing were also unreliable. The
controller consequently never obtained a complete valid frame. Reference-event
tests delivered all 256 byte values through both UART transmit profiles, so
those TX checks do not explain away the learned receiver failure.

**I2C failed at boundary recognition and timing robustness.** Its aggregate
valid-event recall exceeded 99.97%, yet a few boundary failures broke whole
exchanges. Seed 11's phrase missed only final STOP at tick 10,415. Seed 47 also
emitted a false BIT1 at reset tick zero. Seed 29 recovered all 27 write bytes,
but classified repeated START at tick 5,345 as uncertain/INVALID, then failed to
ACK the read address. It also missed STOP and emitted a startup BIT1. This is
why high symbol accuracy is insufficient.

Seeds 11/47 failed readback at 8/8 low/high ticks and at the asymmetric 12/8
condition, despite successful nominal, random-jitter, all-byte and long-message
cases. Some missed boundaries made the read address appear as an extra stored
write byte. Successful SDA response commands took one tick from their matched
observed falling edge; measured master stretch waits were 7–11 ticks. These
are simulation scheduling measurements, not a hardware timing result.

Malformed/rapid-transition recovery succeeded for I2C seeds 11/47 and failed for
29; UART recovery failed. The I2C partial transaction was recoverable without
being reliably flagged: missed STOP events prevent a universal malformed-input
claim. There is no claim to detect ordinary data-bit corruption in parity-free
UART or I2C. See the separate recovery, false-event and controller-error columns.

Float and quantized I2C outcomes matched; UART failed in both. Quantization is
therefore not the primary demonstrated limit. **The immediate bottleneck is
training reliable timing and boundary events.** Longer temporal credit assignment
(the current BPTT window is 128 ticks versus 160/176-tick UART frames) and stronger
rare-boundary supervision are reasonable *next-experiment hypotheses*, not
measured fixes. No architecture change or extra training was used to rescue this
held-out run.

## Controls, arithmetic and cost

Readout-only baselines returned no positive payload in either protocol. Disabling
the reservoir state or removing recurrent connections failed all 36 matched
phrase/every-byte/repeated-pattern controls across both arithmetic modes. The
successful seed-11 I2C exchanges therefore depended on its trained representation
under these controls. This does not establish that recurrence is universally
necessary, or excuse the failed configurations.

Quantized online inference uses Q12 int16 weights, Q14 states/features, Q15
leaks, int64 accumulation, specified rounding and saturation, and a 4,097-entry
integer tanh table. A separate scalar-integer audit matched every state and logit
for 384 ticks. Float success and quantized success were scored separately.

| Resource | Count / logical storage |
| --- | --- |
| Learned coefficients, including biases | 1,224; 9,792 bytes float64 or 2,448 bytes int16 |
| 64-node state, old/new buffers | 1,024 bytes float64 or 256 bytes int16 |
| Fixed leaks / packed tap indices / tanh table | 128 / 192 / 8,194 bytes in proposed quantized storage |
| Weighted operations per update | 1,152 sparse MACs, 128 leak-blend products, 64 nonlinear evaluations |
| Actual NumPy implementation | Dense recurrence: 4,992 MACs/update; quantized arrays use int64 containers |
| Additional temporal storage | Two previous levels, two capped ages, last decision, timestamps, event register, controller state |
| Buffer limits | 32 outstanding UART frames; 4,096 I2C bytes; 512 scheduled line commands |

The scheduler is about 12,800 bytes if packed as 512 × 25-byte commands; it is
not free hidden memory. The logical UART frame capacity is represented by
commands/deadlines, not an additional allocated byte queue. Detailed counts and
packing caveats are in [cost.json](runs/run01/final/cost.json) and
[cost clarifications](runs/run01/final/cost_clarifications.json). Diagnostic trace
lists are not decision inputs. No synthesis, 6×4 fit, physical clock rate, power,
RTL equivalence or hardware execution schedule was established.

## Evidence and reproduction

- [Predeclared design and commands](README.md), [saved profile configurations](runs/run01/config/), [freeze hashes](runs/run01/freeze.json).
- [304 per-condition rows](runs/run01/final/per_condition.csv), [24 model summaries](runs/run01/final/summary_tables.json), [measurement notes](runs/run01/final/measurement_notes.json).
- [All learned weights/checkpoints](runs/run01/models/), [training log](runs/run01/training.log), [final evaluation log](runs/run01/evaluation.log).
- [Independent audit results](runs/run01/audit/results.json): 12 weight/topology checks and all 18 complete phrase-path replays matched exactly.
- Tests: [24 shared-model tests](runs/run01/model_tests.log) and [23 study tests](runs/run01/study_tests.log) passed, including nine new experiment tests. Frozen hashes and `git diff --check` passed. Template comparison could not run because this checkout lacks tag `template-cmos5l`; protected template files were unchanged.

Use Python 3.12.14 / NumPy 2.5.3 as recorded, with
`OPENBLAS_NUM_THREADS=1`. The README commands generate, train, freeze and evaluate
into a **new** directory. To inspect this retained run:

```sh
PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python
export OPENBLAS_NUM_THREADS=1
$PY -B -m work.study.protocol_reservoir64.run verify --output work/study/protocol_reservoir64/runs/run01
$PY -B -m work.study.protocol_reservoir64.run replay --output work/study/protocol_reservoir64/runs/run01 --profile i2c --mode quantized --seed 11
PYTHONPATH=. $PY -B work/study/protocol_reservoir64/runs/run01/audit/independent_audit.py
$PY -B work/study/protocol_reservoir64/runs/run01/audit/summarize.py
MPLCONFIGDIR=/tmp/protocol64-mpl $PY -B work/study/protocol_reservoir64/runs/run01/audit/plot_traces.py
```

USB recorded **zero fitting steps** because the UART/I2C gate failed. Its separate
module and checker exercise only the locally supported NRZI/six-one-stuffing
diagnostic. A USB packet generator and interactive peer deliberately report
missing source instead of fabricating packet fields, CRC polynomials or handshake
timing. Enumeration/configured-device transaction behavior is not implemented.
[USB status and required material](runs/run01/final/usb_status.json).
