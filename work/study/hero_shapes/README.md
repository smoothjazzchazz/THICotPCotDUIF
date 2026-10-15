# Hero shapes: first shared-stage exploration

Question: which small, understandable temporal shapes make a useful configurable
recognize/reject/respond demonstration, and which memory arrangement earns its
cost? This is an experiment, not adoption into the reference design.

## Hypotheses and initial budget

- Ordered pulse widths distinguish equal-count/equal-duration shapes; remembering
  only their common ending should fail.
- Ordered gaps and a separated motif test retention across longer quiet periods.
- Relative-duration shapes test whether loaded scale-tolerant templates generalize
  more directly than sampled-state prototypes.
- A conventional streaming template bank may solve these tasks with less stored
  history. Explicit run/sample history and recurrent memories are comparisons,
  not presumed winners. Waveform definitions are fixed before model screening.

Initial budget: three waveform families, at most eight architecture settings per
family, at most twelve rejection settings per fitted model. Use small training
and development streams, retain all trials, then freeze every candidate and the
scorer before a single fresh confirmation. No confirmation-driven revision is
planned. Standard-library Python; no external protocol documents.

## Assumptions and shared interface

One already sampled binary lane. A low run of 20 consecutive conditioned samples
is an observable delimiter; internal gaps stay below it. All candidates share
conditioning, framing, streams, event scoring, controller, TX and the existing
`run_simulation` loop. A stream resets once, never at its annotated examples.
Mid-frame startup is invalid until a delimiter is observed. Short gaps that omit
the delimiter are malformed combined bursts, not secretly separated examples.

`FramedTemporalEncoder` extends the existing sample record with `frame_started`,
`frame_complete`, `frame_valid`, `frame_start_tick`, `frame_run_count`, and
`frame_active`. Completed runs exclude the leading/trailing idle. A completion
occurs on the twentieth low sample, 19 ticks after the final falling edge.
Only inference-visible samples generate these flags. No labels or annotations
enter online stages. Memory latching at the last falling edge preserves a
snapshot while waiting for the delimiter; its storage and latency are counted.

Related implementations live in `work/model`; definitions, fitting, scoring,
saved settings and evidence live here. Loaded duration templates and learned
prototype vectors express recognized behavior. Signal-derived frame resets are
explicit; generated-example resets and lookahead are prohibited.

## Success and evaluation

A promising candidate must achieve at least 95% correct known events in each
clean, timing-varied, filtered-glitch and recovery condition, at least 95%
explicit unknown rejection in each observable unfamiliar condition, zero false
known events on unfamiliar/background input, zero duplicates, and exact loaded
responses beginning on the next unqueued tick. Report misses and incorrect
classes separately. Boundary and reset challenges are separate conditions;
unobservable corruption is documented, not silently relabeled as a success.

Measure startup versus warm streams, decision and response latency, timestamps,
state/parameter counts, computation and software scheduling assumptions. Check
causal prefixes, reset, stage interaction and independent instances. Exact or
near collisions between known and unknown memory snapshots are diagnostics;
more readout fitting cannot repair an exact collision.

Training, development and confirmation have separate fixed seeds. Unfamiliar
prefix/suffix splices and additional malformed bursts are reserved for
confirmation and never select thresholds. Save source hashes, inputs, settings,
commands, all failed candidates, per-condition metrics and readable traces.

Historical reports suggest memory loss and prefix-splice failures worth testing;
their removed implementations and old percentages are not current evidence.
No result here establishes electrical compliance, hardware feasibility, RTL
equivalence, formal verification, physical frequency or a project gate.

## Frozen definitions and development revision

All tuples alternate high/low durations, starting and ending high:

| Family | Class 0 | Class 1 | Nominal burst length |
| --- | --- | --- | --- |
| Pulse order | `4,4,8,4,4` | `8,4,4,4,4` | 24 ticks |
| Gap order | `4,3,4,9,4,3,4` | `4,9,4,3,4,3,4` | 31 ticks |
| Relative order | `3,3,7,3,5` | `7,3,3,3,5` | 21 or 42 ticks |

The relative family loads scales 1 and 2; each run may vary independently by one
tick around one loaded template at one consistent scale. Arbitrary time scaling
is not in this first vocabulary. Scale 3 is a reserved unknown challenge.
Every family has equal-count/equal-duration known alternatives with a common
ending. The first measured width/gap must survive until the end. These shapes
were selected before architecture screening for inspectable temporal information,
not from a search for a particular reservoir's strongest waveform.

The actual front end uses a one-sample delay followed by a two-sample filter.
Surviving edges shift by two ticks; reset-filled/settling samples cannot qualify
startup idle. Decision is at raw final falling edge +21 and an unqueued response
begins at +22. The one-tick glitch tests deliberately place corruption inside a
long enough run to preserve the conditioned shape; they do not establish
arbitrary glitch immunity.

The retained [first screen](results/screen_v1/README.md) used seven settings per
family. An independent development challenge found percentage-error templates
could accept two-tick errors in long runs even though the vocabulary allows one
tick. The second screen keeps that failure, adds the challenge to development,
and adds absolute-error streaming templates as the eighth setting. Total search
is 45 fitted/configured combinations across both screens, with at most twelve
rejection settings each. No final evaluation had occurred during this revision.

This gives conventional templates privileged access to the declared timing rule;
prototype models get known training examples and the shared run-count gate.
That is a useful engineering baseline, not equal statistical supervision or a
general demonstration that templates outperform recurrent networks. The latter
receive only one seed per topology and eight fitted exemplars per class.

The normalization/scale-3 collision was also identified structurally before
confirmation. Its challenge is withheld from fitting and calibration, but is
known to the designers. Prefix/suffix splices and missing delimiters are other
reserved confirmation mechanisms; they are not claimed to be unimaginable
open-world traffic.

## Results and reproduction

Read the [measured comparison](REPORT.md) first. Only the absolute-interval
streaming variant met the local criteria on all three families. The failed
first screen, every threshold trial, full configurations, source snapshots,
inputs, per-condition metrics and demonstration traces are retained under
`results/`. No adoption or hardware gate follows from this result.

**Audit overlap:** the independent interval audit enumerated the entire permitted
known timing vocabulary before confirmation, including the held-out jitter
partition. Thus final evidence is fresh continuous order/gaps/mixtures and
reserved unfamiliar mechanisms, not unseen known timing tuples. The report and
`results/screen_v2/audit_scope.json` record that limitation. No settings changed
after the audit or confirmation.

From the repository root, standard-library Python only:

```sh
# Existing frozen evidence must verify against the current Python sources.
python3 -B -m work.study.hero_shapes.run_study verify --output work/study/hero_shapes/results/screen_v2

# Reproduce into a NEW directory; existing evidence is refused.
python3 -B -m work.study.hero_shapes.run_study screen --output work/study/hero_shapes/results/reproduction
python3 -B -m work.study.hero_shapes.run_study freeze --output work/study/hero_shapes/results/reproduction
python3 -B -m work.study.hero_shapes.run_study confirm --output work/study/hero_shapes/results/reproduction

# Load a saved configuration and run the entire continuous stream; --case only
# restricts displayed ticks after inference, never its input or reset behavior.
python3 -B -m work.study.hero_shapes.replay --config work/study/hero_shapes/results/screen_v2/pulse_order/stream_intervals/config.json --input work/study/hero_shapes/results/screen_v2/inputs/pulse_order-heldout.json --case pulse_order-heldout-003

python3 -B -m unittest discover -s work/model -p 'test_*.py' -v
python3 -B -m unittest discover -s work/study -p 'test_*.py' -v
python3 -B work/tools/check_template.py
git diff --check
```

Model/study checks passed 24/14 tests. The template script cannot compare its
baseline because tag `template-cmos5l` is absent. No frozen template file was
modified. If later source edits make verification fail, the exact frozen Python
tree is under `results/screen_v2/frozen_source/`; run from that directory to use
those implementations with a new results path under its own `work/study/`.

Files are deliberately direct: `stimuli.py` defines samples and offline labels;
`models.py` loads shared stages; `fitting.py` fits/calibrates offline;
`scoring.py` accounts for events and checks response samples; `run_study.py`
orchestrates screen/freeze/confirm; `replay.py` loads saved configurations. There
is one simulation runner, in `work/model/system_simple_model.py`.
