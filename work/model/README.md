# Python models

This small scaffold demonstrates input waveform → recognized symbol → controller
decision → output waveform. It uses Python's standard library, one input lane,
and one output lane. Each loop iteration is one simulated tick; nothing sleeps.

The receiver uses **run-length recognition**, not a reservoir. The skeleton checks
component interaction, not reservoir effectiveness, hardware timing, or project
completion. It is not the planned golden model or ISA reference described in v0.3
section 7, and it does not establish that a project gate has passed.

```text
input levels (0 or 1)
  → PulseReceiver
  → RX event {class_id, start_tick}
  → receive queue (deque)
  → Controller
  → transmit symbol ID
  → Transmitter + TX_TABLE
  → output levels (0 or 1), or None when no output is pending
```

## Run and read

From the repository root:

```sh
python3 -B -m work.model.system_simple_model
```

This prints two tables: the two recognized pulses, then a three-tick unknown
pulse with fresh component state. Each table also has input and output sequences
aligned by tick. In the output column, `idle` means `None`, which is distinct
from `0`. **`None` is a software marker, not an electrical state**: it does not
specify low, high, or high impedance. A dash in the RX event column means no event.
The high count is shown after receiver processing, so it is zero on an event tick.

Start with `run_simulation()` in [system_simple_model.py](system_simple_model.py).
Its loop advances TX, samples RX, queues any new event, lets the controller handle
one event, and records the trace, in that order. `print_trace()` only formats that
trace; it does not step the components. `main()` contains the two example inputs.

## What each component remembers and produces

| Component | Remembers | Produces |
| --- | --- | --- |
| `PulseReceiver` | Pulse-length-to-class mapping, consecutive high count, starting tick | An event on the first low sample after a pulse, otherwise `None` |
| Receive queue | Events waiting in an unbounded `deque` | The oldest event when the controller removes it |
| `Controller` | Class-to-transmit-symbol mapping | At most one `send(symbol_id)` request per tick and a short action description |
| `Transmitter` | Requested symbol list, current symbol index, position within its pattern | One output level per tick, or `None` when no output is pending |

Input levels and output levels are samples, while received class IDs and transmit
symbol IDs are labels with separate meanings. The receiver maps two high ticks to
class `0` and four to class `1`. Any other positive pulse length becomes unknown
class `7`. Idle low samples emit nothing. A pulse needs a following low sample to
finish; there is no look-ahead or automatic flush when the input list ends.

The controller maps class `0` to transmit symbol `2`, and class `1` to transmit
symbol `1`. It consumes unknown or unmapped events without transmitting. It only
reads events and requests symbols; it never reads input samples or drives output
levels. The trace retains newly emitted events even if consumed that tick.

The existing [transmit_simple_model.py](transmit_simple_model.py) is reused:

- `Transmitter([])` starts with no requests; an initial symbol list is also allowed.
- `send(symbol_id)` appends a request. An unknown symbol ID raises `ValueError`.
- `step()` plays queued patterns in order, with no inserted idle tick between them.
- `TX_TABLE` currently has `0: [0, 0]`, `1: [0, 1]`, `2: [1, 0]`, `3: [1, 1]`.

This transmitter has no capacity limit and keeps completed requests in its list,
moving its index past them. That simple state is sufficient for these short runs;
it is not the full hardware transmitter.

## Follow the first pulse

1. Tick 1 starts a high pulse; the receiver remembers `start_tick = 1`.
2. Tick 2 raises the high count to two. There is still no event.
3. Tick 3 is low. The receiver emits `{"class_id": 0, "start_tick": 1}` and
   clears its pulse state. The queue receives that event and the controller removes
   it in the same tick, requesting transmit symbol `2`. Output is still `None`.
4. Ticks 4 and 5 play symbol `2` as output levels `[1, 0]`.

TX advances before the controller runs, so a request made during tick `t` can
first play during tick `t + 1` (or later if earlier requests are still playing).
This is a simulation convention, not a hardware timing claim.

The second pulse starts at tick 5 and emits class `1` at tick 9. Symbol `1` plays
`[0, 1]` at ticks 10 and 11. All other output ticks are `None`. Eight extra low
samples give the last response time to finish. The separate three-tick pulse
emits class `7` at tick 4 with `start_tick = 1`, and produces no transmit response.

## Try a change

- **Input:** edit `input_levels` or `unknown_input_levels` in `main()`. Leave low
  samples after the last pulse so it can finish and its response can play.
- **Recognition:** edit `{2: 0, 4: 1}` passed to `PulseReceiver` in `run_simulation()`.
- **Response:** edit `{0: 2, 1: 1}` passed to `Controller` there. Class `7` stays unknown.
- **Transmit patterns:** edit `TX_TABLE` in `transmit_simple_model.py`.

For example, change the first pulse from two high samples to three and watch its
class change to `7` and its response disappear. The checks below describe the
original example, so intentional behavior changes may require updating them.

Later, the receiver can contain the reservoir, readout, conventional classifier,
and stabilizer while preserving the same `{class_id, start_tick}` event interface.
This scaffold does not implement those blocks, training, an instruction
interpreter, reflex arbitration, protocol framing, a hardware loader, RTL, or
electrical behavior.

## Small checks

From the repository root:

```sh
python3 -B -m unittest discover -s work/model -p 'test_*.py' -v
```

The two system checks cover the expected events and output ticks, and unknown-pulse
consumption without a response. The existing three transmitter checks cover its
current simple API and playback behavior.
