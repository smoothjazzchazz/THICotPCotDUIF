# Shared-stage demonstration

Question: can the same readable online pipeline run with explicit sample history
or a small recurrent memory, exposing each stage and preserving simple response
timing? This is a wiring and causality diagnostic, not a memory-selection study.

## Assumptions and comparison

One sampled binary lane; one update per tick; reset at each run. Known high pulse
widths are 2 (class 0) and 4 (class 1). Widths 3 and 1 are unfamiliar. Low gaps are
eight ticks. The readout triggers on an observed falling edge. All stimuli are
synthetic and deterministic; there is no random seed. Input timing and memory
math are described in the [model README](../../model/README.md).

Experimental departures from the reference include one listener/lane, floating
point arithmetic, three recurrent nodes or four explicit feature frames, a
distance readout, Python timestamps, a mapping controller, and one output lane.
No synchronizer physics, core instructions, finite FIFOs, or hardware scheduling
are modeled. The seven stages are an initial decomposition, not restrictions on
future experiments; [experimental scope](../../../knowledgebase/experiments.md)
and its evidence requirements apply.

Success for this diagnostic means the known pulses emit the right events and
responses, unfamiliar completed pulses emit unknown events without responses,
filtering suppresses the isolated glitch, and reset/causal-prefix checks pass.
Report every condition and false known event; do not select a winning memory
from this tiny deterministic example.

## Files and run commands

- `stimuli.py`: training examples and demonstration waveform/annotations.
- `fitting.py`: offline mean-prototype fitting. It calls the shared runner with
  an empty readout and no response mapping, then extracts measured completion
  states. Labels only group those states outside inference.
- `scoring.py`: compare emitted events with annotations after the simulation.
- `run_demo.py`: small configuration, stage construction, CLI, saved artifacts.
  It imports the model's runner; it does not copy the simulation loop.
- `test_demo.py`: one parameterized diagnostic over 18 constructions.

Run from the repository root (standard library only):

```sh
python3 -B -m work.study.stage_demo.run_demo --memory history
python3 -B -m work.study.stage_demo.run_demo --memory reservoir
python3 -B -m work.study.stage_demo.run_demo --memory history --stable-ticks 2
python3 -B -m work.study.stage_demo.run_demo --memory reservoir --stable-ticks 2
```

`--memory pulse` uses the original exact-duration baseline. `--delay-ticks 0|1|2`
adds a deterministic input delay. The sample filter supports 1 or 2 here so both
known training pulses survive; the common conditioner supports any positive
filter length. When changing that assumption, revise training and scoring too.

Offline training uses widths 2 and 4 with two idle-prefix lengths. Each memory
receives exactly the same training inputs. The class prototype is its mean
completion state. Before constructing the demo waveform, freeze the score cutoff
at minus one sixteenth of the smallest between-prototype mean squared distance,
and the margin cutoff at one eighth. These are illustrative development rules,
not probabilities or calibrated unknown-detection guarantees. There is no
held-out evaluation. Fitting runs again for a different conditioning setting
or memory so the readout matches the resulting representation.

To save a new run without overwriting previous evidence:

```sh
python3 -B -m work.study.stage_demo.run_demo --memory history --output work/study/stage_demo/results/my-history-run
```

The new directory contains `trace.txt` and `manifest.json`: settings, matrices or
history depth, fitted prototypes, decision thresholds, controller/TX mappings,
training and demo samples, source SHA-256 hashes, command, and per-condition
results. Existing directories are refused. Results must stay under `work/study`.
The full source trace is printed even when no output directory is requested.

## Recorded diagnostic, 7 October 2026

The initial four runs below all recognized the three known occurrences (including
the short pulse after unfamiliar traffic), rejected the width-3 input, and
produced zero known events on unfamiliar/background input. Both unfiltered runs
emitted unknown for the one-tick glitch; both filtered runs suppressed it before
recognition. No extra events occurred. These are observations of this waveform,
not accuracy estimates for a distribution of inputs.

| Construction | Full tick trace | Settings and per-condition results |
| --- | --- | --- |
| History, pass-through | [trace](results/history/trace.txt) | [manifest](results/history/manifest.json) |
| Reservoir, pass-through | [trace](results/reservoir/trace.txt) | [manifest](results/reservoir/manifest.json) |
| History, two-sample filter | [trace](results/history-filtered/trace.txt) | [manifest](results/history-filtered/manifest.json) |
| Reservoir, two-sample filter | [trace](results/reservoir-filtered/trace.txt) | [manifest](results/reservoir-filtered/manifest.json) |

Without filtering, raw-start-to-decision latency is 2 ticks for the short known
pulse and 4 ticks for the long known pulse. Two-sample filtering adds 1 tick.
An explicit delay adds its configured ticks as well. Unqueued transmission
starts 1 tick after the decision. Timestamped pulse starts follow conditioned
edges, so the scoring records raw and conditioned starts separately.

The model suite passed 14 tests (including the original 5); the study test passed
all 18 memory/filter/delay combinations; `git diff --check` passed. The template
integrity script could not check its baseline because this checkout lacks the
`template-cmos5l` tag (`fatal: bad revision 'template-cmos5l'`). No template files
were changed by this work. Focused checks verify TX queuing and zero output,
parallel recurrence, stabilization, reset, independent state, and unchanged
prefixes under incompatible suffixes. This record establishes no named-protocol
compliance, hardware feasibility, project gate, or general rejection behavior.

The model README accounts for state, coefficients and arithmetic. These runs do
not benchmark wall time, synthesize the floating-point model, or investigate
jitter, arbitrary gaps, distribution shift, sampling phase, or long-term memory
quality. No candidate was tuned against the demonstration, and no failed
candidate trial was discarded. Historical reports elsewhere in `work/study`
remain unchanged.
