# Shared waveform translator model

This is a readable, standard-library Python scaffold for **sample → recognition
→ response waveform**. It starts from the simple pulse receiver/controller/TX
model and preserves its tested behavior. It is not a complete golden model of
the chip, a processor emulator, or a validated choice of memory architecture.
Python 3.10 or newer is required.

[Experimental scope](../../knowledgebase/experiments.md) permits replacing,
bypassing, combining, or rearranging these stages. They are shared building
blocks, not a permanent architecture. For ordinary experiments, change settings,
swap a stage, or add a related implementation in its existing module. Reuse the
runner rather than copy the pipeline into another modeling framework. Put
experiment settings, stimuli, fitting, scoring, and results under `work/study/`.

## Run and swap

From the repository root:

```sh
python3 -B -m work.study.stage_demo.run_demo --memory history
python3 -B -m work.study.stage_demo.run_demo --memory reservoir
python3 -B -m work.study.stage_demo.run_demo --memory reservoir --stable-ticks 2
```

All three use the same runner. `--stable-ticks 1` passes samples through;
`--stable-ticks 2` requires two equal samples before changing the conditioned
level. `--delay-ticks 2` adds a deterministic two-sample delay before filtering.
`--memory pulse` selects the original exact-width baseline. The earlier command,
`python3 -B -m work.model.system_simple_model`, now runs the shared stage demo.

Each run prints every intermediate output and the entire memory vector at every
tick. The [example README](../study/stage_demo/README.md) explains fitting and
contains links to saved traces and settings. Neither memory is a selected winner.

## Data flow and execution order

```text
sampled 0/1 → conditioning → temporal measurements → memory
          → readout scores → rejection/stabilization → event
          → mapping controller → response request → transmitter → 0/1 or idle
```

There are two short pieces of execution code, both in
[`system_simple_model.py`](system_simple_model.py):

1. `run_simulation` advances TX from earlier requests.
2. `StagedReceiver.step` visibly executes conditioning, encoding, memory, readout,
   then decision, in that order. Readout sees the **new** memory state this tick.
3. The controller consumes this tick's event and optionally queues a TX request.
4. The runner snapshots the observation, event, request, and output into its trace.

Thus a request made at tick `t` starts at `t+1` if TX is free, or later if earlier
patterns are still playing. Patterns play contiguously without extra idle ticks.
The old receive deque was consumed in the same tick it was filled; this runner
calls the controller directly with the same timing. There is no modeled RX FIFO
capacity, CPU instruction latency, or clock-domain scheduling.

The runner takes an iterable of binary samples, including a one-pass generator.
It never reads its length, a future sample, a label, or a generator boundary.
It resets supplied components at the start of each call and begins at tick zero.
It does **not** flush a final high run or drain TX when input ends; provide actual
trailing input samples to advance time. For streaming receive experiments, call
`receiver.step(level, tick)` with consecutive ticks and call `reset()` explicitly.

## Stage contracts and where to edit

| Stage and module | Input → output | Runtime state / update |
| --- | --- | --- |
| `InputConditioner`, [`conditioning.py`](conditioning.py) | Raw 0/1 → `ConditionedSample(raw_level, delayed_level, level)` | Delay line, pending level/count, accepted level; delay first, then filter each tick. |
| `TemporalEncoder`, [`temporal.py`](temporal.py) | Conditioned level + tick → `TemporalSample` | Current level, run start, last tick; detects transitions and completes the previous run on an observed edge. |
| `ExplicitHistory` / `RecurrentReservoir`, [`memory.py`](memory.py) | `TemporalSample` → tuple of numbers | Last N feature frames, or recurrent node values; updates once each sample. Both expose `state` and `reset()`. |
| `PrototypeReadout` / `PulseLengthReadout`, [`readout.py`](readout.py) | Memory tuple + measurements → `ClassScores` or `None` | Loaded parameters only; no fitting or mutable inference state. |
| `DecisionStage`, [`decision.py`](decision.py) | Scores or `None` + tick → `DecisionOutput(candidate, stable_ticks, event)` | Pending class, first timestamp, count, emitted flag; rejects before stabilization. |
| `MappingController`, [`controller.py`](controller.py) | `SymbolEvent` or `None` + tick → `ResponseRequest` or `None` | Last event/request, replaced each tick; mapping is copied configuration. |
| `Transmitter`, [`transmit_simple_model.py`](transmit_simple_model.py) | `send(symbol_id)` and `step()` → sample or `None` | Request list, current symbol index, position; one pattern sample per tick. |

Use the module in the table for new related variants. Use `StagedReceiver` to
compose the first five stages, and `run_simulation` for the whole system. Add a
new orchestration path only when the experiment requires a different execution
order; explain that departure rather than quietly duplicating this one.

Construct stages directly, for example:

```python
from work.model.conditioning import InputConditioner
from work.model.controller import MappingController
from work.model.decision import DecisionStage
from work.model.memory import ExplicitHistory, RecurrentReservoir
from work.model.readout import PrototypeReadout
from work.model.system_simple_model import StagedReceiver, run_simulation
from work.model.temporal import TemporalEncoder
from work.model.transmit_simple_model import Transmitter

# fitted_prototypes and thresholds come from offline work/study code.
receiver = StagedReceiver(
    conditioner=InputConditioner(stable_ticks=2),
    encoder=TemporalEncoder(),
    memory=ExplicitHistory(depth=4),  # or RecurrentReservoir()
    readout=PrototypeReadout(fitted_prototypes, trigger="falling"),
    decision=DecisionStage(minimum_score=score_threshold,
                           minimum_margin=margin_threshold),
)
trace = run_simulation(samples, receiver,
                       MappingController({0: 2, 1: 1}),
                       Transmitter(patterns={2: [1, 0], 1: [0, 1]}))
```

Changing memory also requires fitting/loading matching readout parameters;
dimensions alone do not establish compatible meanings. The demo's
`build_receiver(DemoConfig(memory="reservoir", stable_ticks=2))` does this offline
and returns an ordinary `StagedReceiver`. It does not implement another loop.
Give each receiver its own stage instances; deliberately passing the same stateful
instance twice shares it. Constructors copy supplied coefficient rows, mappings,
and patterns so separately constructed models do not share mutable configuration.
Reset clears runtime state and preserves loaded parameters. TX reset restores
only the constructor's initial symbols, not later `send()` requests.

## Measurements, decisions, and timestamps

One model tick means one supplied, already sampled binary level. There is no
physical clock frequency. The optional delay pipeline models exact digital delay
only: no metastability, asynchronous phase, analog filtering, sub-tick edges,
sampling jitter, or two-flop synchronizer reliability is simulated. Changes
between samples are invisible. The filter resets to a configurable initial level
(zero by default); its delay registers use that same level.

The first observed sample starts a run at tick zero without inventing an edge.
If input was already high before reset, only its observed portion is measured.
`elapsed_ticks` is zero at the first sample of a run. On a transition at tick `t`,
`completed_run.duration = t - run_start_tick`; the new level begins at `t`.
This applies equally to high and low runs. Nothing here recognizes a class.
Features are `(signed level, signed edge, min(elapsed_ticks, 7) / 7)`; exact
uncapped timing remains in the measurement record.

The history memory stores those frames oldest first, including the current
frame, with numerical zero padding after reset. Padding is an initial memory
value, not an observed low sample. The recurrent alternative uses three nodes
by default, explicit matrices and one leak value:

```text
drive[i] = sum(input_weight[i,j] * feature[j])
         + sum(recurrent_weight[i,j] * old_state[j])
new_state[i] = (1 - leak) * old_state[i] + leak * tanh(drive[i])
```

Every node reads the old state; the new tuple is committed together. These are
floating-point starting models, not the reference 16-node six-bit reservoir.
Neither saturation nor recurrence is presented as validated useful memory.

`PrototypeReadout` scores negative mean squared distance to each prototype.
The demo scores only measured falling edges; its timestamp is the start of the
completed **conditioned** high run. No stimulus marker triggers the readout.
`PulseLengthReadout` preserves the exact-width baseline by using measurements
directly; that intentional memory bypass demonstrates no reservoir recognition.

Decision rejects absent/invalid scores, a low best score, ties, or a small winning
margin. One prototype has no competitor, so its margin is `None`; the score
threshold still applies. Rejection produces an explicit unknown candidate and
can produce an unknown event. A missing readout (`None`) means **no evaluation**,
clears pending stabilization, and produces no event.

`hold_ticks=1` disables the extra stabilization wait. Longer holds require fresh
consecutive evaluations of the same class; use `trigger="every_tick"` for that.
An isolated falling-edge score cannot satisfy a multi-tick hold. The first stable
class after reset is eligible, including unknown. Only one event emits per
uninterrupted candidate run; an absence or class change rearms it, allowing two
separate pulses of the same class to produce two events.

For continuous scoring, `start_tick` is the beginning of the candidate run; for
completion scoring, it is the measured pulse start. `decision_tick` is emission
time. `requested_tick` records the controller's request time. These are unwrapped
Python integers, not the reference 12-bit timestamp. Filtering/delay shifts
observed pulse timestamps; they are not corrected back to an estimated pin edge.

Keep these distinctions:

| Value | Meaning |
| --- | --- |
| `event is None` | No new event this tick, even if a known candidate remains stable. |
| `event.class_id is None` | An explicit unknown classification event. |
| `event.class_id == 0` | Valid known class zero. |
| `request.symbol_id == 0` | Valid requested pattern zero. |
| `output_level is None` | Software idle / no scheduled output sample. Not electrical high impedance. |
| `output_level == 0` | A real transmitted low sample. |

`PulseReceiver`, the queue-based `Controller` wrapper, and trace `rx_event`
preserve the old dictionaries with class 7 for unknown. New code should use
`row["event"]` and the typed stage outputs; they do not reserve a numeric class.
The legacy dictionary cannot distinguish a known class 7 from unknown.

## Follow one pulse

In the default history demo, input rises at tick 8 and stays high at tick 9.
At tick 10 the observed falling edge completes a two-sample run starting at 8.
Memory updates with that edge; the prototype readout prefers class 0; decision
accepts it and emits `SymbolEvent(0, start_tick=8, decision_tick=10)`. The controller
requests symbol 2 at tick 10. TX emits `1` at tick 11 and `0` at tick 12.

The unfamiliar three-sample pulse completes at tick 21. Its scores fail rejection
thresholds, so it emits an unknown event with start 18 and requests no response.
With two-sample filtering, surviving edges and decisions shift one tick later;
the one-tick glitch produces no conditioned high run and therefore no event.
The trace prints features, full memory, scores, decision reason/hold count,
timestamps, request, and TX level for every tick, including idle ticks.

## Scope, cost, and checks

For the demo's three features and two classes, history depth 4 holds 12 numeric
values and its readout loads 24 prototype values. The reservoir holds 3 node
values, 18 matrix weights plus one leak, and 6 prototype values. Each reservoir
tick computes 18 weighted products, 6 blending products, and 3 `tanh` calls;
history shifts four frames. A scored tick computes 24 or 6 squared differences
respectively. The encoder has three scalar state fields; conditioning adds
`delay_ticks` samples plus level/counter state. Decision and controller add their
inspectable small records/counters. These are software storage/operation counts,
not bit widths, cell counts, a hardware schedule, or measured execution time.

All receive stages execute in the same simulated tick. Real preprocessing,
buffering and arithmetic scheduling would need separate implementation evidence.
TX retains completed requests in an unbounded list, and trace storage grows with
the input length. This is deliberate scaffold simplicity, not finite hardware
FIFO/backpressure behavior. Short examples include enough tail samples to finish
transmission; the runner otherwise returns with queued work still inspectable.

```sh
python3 -B -m unittest discover -s work/model -p 'test_*.py' -v
python3 -B -m unittest discover -s work/study -p 'test_*.py' -v
python3 -B work/tools/check_template.py
git diff --check
```

Checks cover the five pre-existing behaviors plus stage timing, synchronized
state updates, explicit zeroes, unknown/absence, stabilization, queue order,
reset/replay, instance isolation, and unchanged trace prefixes under different
futures. The example check exercises both memories, the pulse baseline, both
filters, and three sample delays through the same runner.

This scaffold does not implement dual listeners, ISA, host loader, electrical
behavior, full reference FIFOs, RTL arithmetic, or named protocols. The
[reference architecture](../../knowledgebase/architecture.md),
[doctrine](../../knowledgebase/doctrine.md), and
[evidence gates](../../knowledgebase/phases.md) remain separate. No protocol
compliance, hardware feasibility, or project gate pass follows from these checks.
Historical study reports and their cleanup record remain intact in
[`work/study/`](../study/ARCHIVE.md).

## Framed multi-run experiments

The [hero-shape study](../study/hero_shapes/README.md) adds reusable variants in
the same stage modules and uses this same runner. `FramedTemporalEncoder` detects
a loaded low-idle delimiter, invalidates startup without observed framing, and
caps run counts so malformed prefixes cannot roll into a fresh valid count.
`startup_ignore_ticks` excludes conditioner reset fill and settling; the study
loads `delay_ticks + stable_ticks - 1`. Its frame-age limit includes delimiter
waiting. These are explicit experimental assumptions, not reference mechanisms.

`RunHistory` stores durations on observed edges and can normalize their total.
`LastFallingLatch` wraps the existing sample history or reservoir, continuously
updates that memory, and saves the final falling-edge vector while waiting for
the delimiter. It adds a full vector of storage. No generated-example reset is
introduced; run-history clearing uses the observable frame-start signal.

`FramePrototypeReadout` scores loaded exemplars once per completed frame, with
an optional measured run-count validity check. `StreamingTemplateReadout` instead
accumulates worst-run error for each loaded class/scale, with either absolute
tick error or relative error. It bypasses memory for recognition and stores only
progress and error values, rather than the whole waveform. The readout receives
the same observed framing and emits the same `ClassScores` interface. Controller
and TX timing are unchanged. Definitions, fitting and all comparisons live in
the study; no waveform constants are embedded in the shared stage classes.
