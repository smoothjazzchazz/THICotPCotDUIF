# Hero shapes: first measured exploration

**A loaded bank of run-duration intervals is the strongest demonstration in this
screen.** It recognized all 264 known occurrences and explicitly rejected all
296 unfamiliar bursts across three continuous confirmation streams. It produced
no incorrect classes, false known events, duplicates or background alarms. Every
requested response matched its loaded waveform and started one tick after the
decision. These are finite synthetic results with explicit framing assumptions.

The useful story is configurable temporal order: the same implementation loads a
different shape table and output table. A recurrent reservoir did not earn its
extra work in this screen. That finding is limited to these shapes, settings and
readouts; it is not a general result about recurrent networks.

## Shapes and what must be remembered

Durations alternate high/low, starting and ending high. All known pairs have
equal pulse counts and total duration, and share an ending.

| Family | Class 0 / class 1 | Why show it? | Required retained information |
| --- | --- | --- | --- |
| Pulse order | `4,4,8,4,4` / `8,4,4,4,4` | Smallest, clearest first demo: which of the first two pulses is long? | First pulse width survives 20 ticks to the final falling edge; 24-tick whole burst. |
| Gap order | `4,3,4,9,4,3,4` / `4,9,4,3,4,3,4` | Identical pulses, different placement of the long silence. | First internal gap survives up to 24 ticks after measurement to the final edge; 31-tick whole burst. |
| Relative order | `3,3,7,3,5` / `7,3,3,3,5`, at loaded scales 1 and 2 | Same ordering at two speeds; demonstrates reloaded timing hypotheses. | Early pulse widths survive 18 or 36 ticks after measurement; 21/42-tick bursts. |

Every run accepts independent ±1 tick variation around one consistent loaded
scale. The relative family does **not** promise arbitrary scale invariance.
Unknowns share prefixes, suffixes, count or duration; include missing/extra edges,
partial bursts and junk; and reserve prefix/suffix splices, missing delimiters
and scale 3 for confirmation. The definitions preceded architecture screening.
The conventional interval recognizer directly expresses this declared grammar;
that advantage is explicit, not evidence of equal statistical supervision.

## Compared on the same streams

Cells below are **correct known / known; false known events on unknown input**.
The full [per-condition tables](results/screen_v2/CONDITIONS.md) also separate
wrong classes, rejected knowns, missing observations, explicit unknowns, startup,
background and duplicate events. No aggregate score determined the winner.

| Topology and readout | Pulse order | Gap order | Relative order | Decision |
| --- | --- | --- | --- | --- |
| Streaming absolute intervals | 72/72; 0 | 72/72; 0 | 120/120; 0 | Retain as first demo on all three. |
| Streaming percentage error | 57/72; 0 | 56/72; 0 | 88/120; 0 | Reject current metric: strict rejection misses allowed jitter. |
| Explicit run history + exemplars | 65/72; 0 | 56/72; 0 | 89/120; 8 | Retain representation for investigation, not current acceptance rule. |
| 12-sample history + exemplars | 61/72; 16 | 0/72; 0 | 31/120; 3 | Reject: forgotten prefixes and real state collisions. |
| 64-sample history + exemplars | 0/72; 0 | 39/72; 0 | 16/120; 0 | Reject current readout: longer history alone does not give timing tolerance. |
| Existing three-node recurrence + exemplars | 55/72; 0 | 55/72; 0 | 22/120; 0 | Reject this configuration. |
| 16-node ring, leak 0.45 + exemplars | 23/72; 0 | 54/72; 0 | 36/120; 0 | Reject this configuration. |
| 16-node sparse recurrence, leak 0.25 + exemplars | 15/72; 0 | 55/72; 0 | 37/120; 0 | Reject this configuration. |

The interval candidate separately rejected all 96/96, 96/96 and 104/104 unknown
bursts. Each of its clean, jitter, interior-glitch, minimum-gap and recovery
conditions achieved full recognition. Startup tests add nine invalid first
bursts and eighteen valid recovery bursts across the three families; all were
handled correctly. Eight single-sample background glitches per confirmation
stream were filtered away and produced no events; those are suppressed inputs,
not explicit unknown classifications. All candidates had zero missing framed
observations, duplicates and background events in these confirmation streams.
Gap/sample12 had one wrong known class; relative/sample12 had three.

## Failures that explain the comparison

1. **Percentage tolerance mismatched the vocabulary.** The retained
   [first development screen](results/screen_v1/README.md) appeared to pass pulse
   order. Independent probes then changed only a long run by two ticks: the
   percentage cutoff still accepted it. The second screen retained that failure,
   added the near-unknown condition and added absolute-tick intervals as the
   eighth setting. Both screens, all 474 threshold trials and source snapshots
   remain. No confirmation result caused a revision.
2. **Short memory destroys information.** Pulse-order `(4,4,8,4,4)` and unknown
   `(6,2,8,4,4)` have identical 12-sample decision vectors. Gap order and relative
   order also have exact cross-class collisions. This cannot be repaired by
   fitting the readout more. The 64-sample vector avoids those measured exact
   collisions, but its nearest-exemplar classifier still fails the strict
   recognition/rejection tradeoff; loss of information is not its demonstrated
   failure. The three-node recurrence retains only extremely small differences
   on some relative-family probes (minimum known/unknown MSE about `9.9e-19`);
   no quantized arithmetic was tested.
3. **Normalization discards a needed validity check.** Scale-3 durations have
   exactly the same normalized run vector as loaded scale 1. The relative
   run-history model falsely accepted all eight out-of-range scale cases and
   emitted responses. A larger readout cannot reconstruct discarded absolute
   duration. Also, its jitter recognition was only 1/32. Absolute bounds and a
   more appropriate distance rule are separate missing pieces.

The conventional bank retains progress and worst error for each loaded timing
hypothesis as edges arrive. This combines order recognition and validity checks
without storing the waveform. The history/reservoir alternatives use at most
eight farthest-first observed exemplars per class and an explicit measured
run-count gate. Recurrent candidates each have one fixed coefficient seed; no
broad recurrent optimization or richer fitted readout was attempted.

## Timing, framing and cost

One binary lane, one already sampled input per tick. A raw waveform passes through
one tick of delay and two-sample conditioning. A burst completes only after
twenty conditioned low samples. There are no generator boundaries, per-example
resets, future samples or labels in inference. All streams reset once; only
observed framing resets the run-template state. Startup reset fill does not count
as observed idle. A missing delimiter merges two shapes into one rejected burst.

All receive stages run in the same modeled tick. **Decision occurs 21 ticks after
the raw final falling edge; response begins at +22.** Recorded starts are shifted
by two ticks. Interval-candidate raw-start-to-decision ranges were 44–50 ticks for
pulse order, 48–56 for gap order and 39–67 for relative order. Matched-event latency
does not hide misses: they are tabulated separately. The filter deliberately
removes isolated interior glitches; adjacent/longer glitches and analog behavior
are outside this guarantee. A long enough low gap is framing, even if a sender
intended it to be internal silence.

| Pulse-order implementation | Recognition state, excluding shared control | Loaded recognition numbers | Computation |
| --- | --- | --- | --- |
| Streaming intervals | 2 errors + run progress; 3 extra trace-only features | 10 durations + 1 scale, plus cutoff/margin | Two absolute errors/max updates per completed run. |
| Run history | 5 duration values + count | 80 exemplar values, plus scale/count/cutoffs | Store one duration per edge; normalize and compare exemplars. |
| Sample history 12 / 64 | 36 / 192 values plus equally sized falling-edge latch | 576 / 3,072 exemplar values | Shift sample frames; squared distances at decision. |
| Three-node recurrence | 3 nodes + 3-value latch | 19 dynamics values + 48 exemplar values | 18 drive products + 6 blending products + 3 tanh per tick. |
| Ring / sparse recurrence | 16 nodes + 16-value latch | 305 dense dynamics slots + 256 exemplar values | Actual implementation: 304 drive products + 32 blending products + 16 tanh per tick. |

Gap intervals load 14 durations + 1 scale. Relative intervals load 10 durations +
2 scales and keep 4 error values. Shared conditioning, edge/frame timers, count
validity, decision/controller state and output tables remain necessary. The Python
runner and TX request list are unbounded software structures. Sparse mathematical
connectivity does not remove the current implementation's dense loops. Numeric
slots and operation counts are **not** bit widths, synthesized area, physical
rates or a proved hardware schedule. See each configuration's `cost.json`.

## Evidence and its limits

Training seed `17301`, development `29303`, confirmation `94709`, separate startup
`85703`; repeat counts 8/5/8. The second screen froze all 24 configurations,
waveform generator, fitted values, thresholds and scorer before generating final
streams. [Freeze manifest](results/screen_v2/freeze.json) records source and
configuration hashes; [summary](results/screen_v2/confirmation_summary.json) and
saved inputs retain exact results. Confirmation covers 560 annotated bursts
across three fresh continuous streams. No failed confirmation was discarded.

**Known timing tuples are not unseen confirmation evidence.** An independent
preconfirmation audit enumerated all 5,832 allowed ±1 known timing cases for the
interval recognizer, including the nominal held-out perturbation partition. It
also checked 78 near-unknowns, 24 malformed frames and 236 startup/recovery checks.
Those are development-observed rule checks; the
[audit scope record](results/screen_v2/audit_scope.json) preserves this overlap.
The later frozen evaluation supplies fresh order, idle gaps and continuous
mixtures, plus reserved unfamiliar mechanisms. It does not establish independent
generalization to previously unseen known timing tuples. The audit did not alter
the already selected interval settings.

The clean vocabulary intentionally repeats across splits. Main-stream jitter
partitions differ, but the audit overlap above takes precedence over any claim
of completely blind known timing. Scale-3 collision and splice mechanisms were
declared before confirmation, withheld from fitting/calibration, and known to
the designers. These data do not establish open-world rejection, confidence
bounds, multi-lane recognition or named-protocol behavior.

The focused model suite passed 24 tests; the study suite passed 14 tests including
the existing stage demo. Checks cover causal prefixes, no end-of-input flush,
conditioning/timestamps, reset and instance independence, missing delimiters,
overflow recovery, reloading shapes/responses, and corruption of the scorer's
response evidence. `git diff --check` passed. Template checking remains unavailable
because this checkout lacks the `template-cmos5l` tag. Frozen template files and
historical reports were not changed. No project gate or reference adoption is
claimed.

## Readable end-to-end examples and next step

The [demo index](results/screen_v2/demonstrations/index.json) gives annotations and
events for full tick traces, generated by replaying entire frozen continuous
streams before selecting a display window:

- [Pulse order recognized and answered](results/screen_v2/demonstrations/pulse_order-known.txt):
  raw start 234, decision 279, loaded `11010` response begins at 280.
- [Same-duration stranger rejected](results/screen_v2/demonstrations/pulse_order-unknown.txt):
  decision 1344 is unknown; no response request.
- [Gap-order demo](results/screen_v2/demonstrations/gap_order-known.txt) and
  [two-speed-family demo](results/screen_v2/demonstrations/relative_order-known.txt).
- [Forgotten-prefix false response](results/screen_v2/demonstrations/pulse_order-sample12-failure.txt)
  and [normalized scale-3 false response](results/screen_v2/demonstrations/relative_order-run_history-failure.txt).

**Use pulse order for the first human-facing demo:** it is short, understandable,
and changes behavior through loaded tables. Keep gap order as the clearest test
that silence position matters. Relative order is useful for showing multiple
loaded speeds, with its scale limitation stated explicitly.

The next justified experiment is continuous tempo variation within a loaded
range: compare a bounded scale estimator plus run validity against a denser
streaming scale bank. Keep framing fixed to isolate that change, include unknown
out-of-range scales and within-frame tempo drift, and freeze fresh settings and
streams again. This directly tests the current scale-normalization failure and
the parameter cost of enumerating speeds. Reducing the 20-tick idle requirement
is a separate later timing experiment.
