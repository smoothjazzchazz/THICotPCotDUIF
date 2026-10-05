# Experiment ledger

All trials and threshold searches are retained in `artifacts/`. Historical results
outside this suite are development context, never fresh confirmation for this suite.

## 0. Audit and contracts

The previous polynomial result is a 20-sample, one-lane pulse-order result. Its
840 readout contributions per tick and 6,752 coefficient bits matter more than its
20 sample bits. No evidence there establishes multiple lanes or longer context.
Local familiar-protocol contracts remain missing. `PLAN.md` defines synthetic
contracts and the budget before screening. No external documents were fetched.

## 1. Initial screen (planned before execution)

Thirteen architectures across four tasks, identical 576 training bursts and 504
development bursts per task. Three ridge penalties, nine decision thresholds per
penalty for learned models; 36 threshold pairs for the deterministic template
control. Integer q8/q12 readout quantization occurs without threshold retuning.

Hypotheses: short raw history should fail long context; recurrence may compress
history but lose precise early evidence; Boolean mixing may lose useful duration;
event memory may trade a deterministic run parser for a shorter, jitter-tolerant
representation. Linear and instantaneous ablations test whether temporal memory
and nonlinear interactions are needed. Modular and single recurrent candidates
have exactly 32 total 6-bit nodes, with whole costs reported separately.

Initial seed 11 is a screen, not evidence of topology robustness. Follow promising
or informative failures with seeds 29 and 47 before freezing comparisons.

## 2. Initial findings and bounded refinement (before refinement execution)

`artifacts/screen/summary.json` retains every initial candidate. Context F1:
run16_block float .871, q8 .636, q12 .873; run16_full q12 .839;
linear run memory .474; 32-node multiscale recurrence .451 (q12).
The block expansion is better than the larger full expansion in this screen.
The raw 20-sample model fails the new long/suffix-shared tasks. These are new
framing/training contracts; they do not invalidate its historical pulse result.

Serious failure: context novel unknown recall is **zero**, even with q12. An
unseen width of 9 lies beyond training widths and extrapolates into a known class.
The macro unknown score (~.80) hides this; it is not a robust open-set result.

Refinement hypotheses:
1. Quantizing bias to the same 8-bit scale wastes coefficient precision. Store
   q6/q8 coefficients with a separately sized integer bias, same common power-of-two
   score scale and frozen thresholds. Charge the extra bias/accumulator bits.
2. A signal-derived run-count/duration support check, calibrated from known clean
   and jitter training, can reject out-of-support widths. It cannot certify all
   unknowns. This adds parser state and four loaded bounds; retain the unguarded
   ablation so gains are not misattributed to the reservoir.
3. Compare 8/12/16/20 run slots, and a 64-prototype deterministic control. Inspect
   failure when memory is too short. Keep a 32-node single/multiscale/modular
   recurrence and Boolean rules at seeds 11/29/47 to test topology stability.
4. Disable filtering on the promising run architecture to measure how much the
   shared deterministic front end contributes.

## 3. Representation and baseline follow-up (before its execution)

The support check fixes the specific context width stranger (novel recall 0→1),
but exact clean/jitter support rejects some noisy clock/data runs. A one-tick
duration slack remains inside the unseen context width of 9 and may recover those.
Raw run q8 still loses the context relation even with a wider bias. That attempted
quantization improvement alone failed. Keep q12 as the measured faithful baseline.

Test a bounded Boolean duration representation: at each observed run, save the
two lane levels and comparisons `duration > [4,7,10]`. Keep same-component pair
products for the first three components and within-run products. These binary
features expose short/long XOR without multiplying large duration integers;
they are a new finite event-memory architecture, not a recurrent reservoir.
The threshold vector is a loaded configuration; this experiment fixes it across
all families and the held-out adaptation recipe. Test guards with slack 0/1 and
a linear ablation. Count the threshold logic/storage and validity handling.

Fairness follow-up: waiting ten idle ticks consumes raw-sample history. Add a
causal falling-to-idle snapshot (state latched at the first observed idle tick,
accepted only after the quiet delimiter). Charge the duplicate state. Refit the
20-sample polynomial baseline and test 96 samples at stride 3 (over-budget at q8)
to distinguish short horizon from a general polynomial limitation. Also test
latched recurrent state. No future sample or oracle completion is supplied.

The first representation run stopped in resource accounting (binary feature
indices were applied to a raw-duration bound vector). Its exception log is retained
as `artifacts/representation.log`; the corrected run is `representation_v2`.
This was an accounting-code defect caught before freeze, not a failed accuracy
trial. No outside file was touched.

## 4. Final development follow-up (before execution)

Binary/slack q8w context F1 .982 and unknown recall .988 versus raw/slack q12
.918/.917; linear binary context .527. Sample96 sparse polynomial still fails
context (~.57 with q8w), despite retaining more history. Strict support count
reduces clock/data F1 from the unguarded .981 to .912. Test duration-only guard
(retain total count in software/accounting but disable its bound) and all five
same-component pair groups instead of only the first three. This tests rejection
of pulse near-matches, where the second duration threshold may need cross-run
interactions. Also compare q6 and q8 of the resulting representations. No more
architecture search is planned unless these reveal an implementation error.

## 5. Selection before fresh confirmation

`configs/selection.json` freezes eight comparisons. The leading representation is
16 run entries × (two lane bits + three duration threshold bits), 600 readout
features, q8 coefficients, wide integer biases. q6 is rejected: context F1 falls
to .606 for the duration-only-guard variant. Adding all five pair groups costs
more without a reliable development gain. More raw run slots did not help.

Retain both **binary_duration** and **binary_strict**: same physical structure,
different loaded run-count bounds. Duration-only guard reaches task F1
.962/.977/.979/.980; strict-count + one-tick duration slack reaches
.962/.981/.912/.982. Raw-duration q12 is a tradeoff, especially on pulse unknowns.
Compare linear binary memory, latched 20-sample polynomial, over-budget 96-sample
polynomial, the 32-node multiscale latched recurrent family, and 64-prototype
templates. Recurrent replicas fix seeds 11/29/47 across tasks; no best seed is
selected. Boolean CA is rejected on development, not subjected to more selection.

The initial transfer fixture test checked only framing at seed 421, not trained
classification. The architecture/recipe freeze precedes all transfer adaptation;
transfer test streams use fresh seeds after the learned-parameter lock.

Before freeze, transaction scoring was tightened to include spurious emissions
through the entire inter-group idle interval. Event metrics and candidate selection
are unaffected. Study timestamps are explicit 16-bit modulo integers (all study
streams <65,536 ticks), with counter and output storage counted, plus four
estimated synchronizer flops. Sampled-input latency excludes synchronizer clocks.
Ten contract/scoring/causality/quantization/checkpoint tests pass before freeze.

A **predeclared blind unknown probe** appends extra in-burst activity before an
otherwise known-looking suffix. This checks the finite-history/count tradeoff.
It is generated only with confirmation, reported separately, and must not trigger
retuning. Confirmation uses exactly the frozen tradeoff set and adaptation grid.

## 6. Fresh confirmation — no tuning afterward

One batch: 280 unique normal streams / 13,400 complete truth events, plus 960 blind
splice unknowns. Three frozen fits per task, eight stream blocks. All 120 model
configurations and every emitted event are saved. Binary duration-only context
F1 .9716, strict .9701, raw-duration q12 .9010, linear binary .4806, sample20 .4494,
recurrent32 .4563. Held-out differential-family binary strict F1 .9692; relaxed
.9757. The unchanged architecture and adaptation recipe transferred successfully
within the delimited synthetic scope.

**Counterevidence:** relaxed count accepts every blind splice; strict rejects all.
Strict clock/data F1 .8897 and mixed-condition recall .578; relaxed F1 .9681 and
mixed recall .919. Both binary modes reject only .531 of pulse near-matches and
.539 of clock/data near-matches. These serious failures prevent a universal
recommendation. Raw durations and the polynomial/template controls remain useful
on pulse shapes. No confirmation result was used to retrain or change thresholds.

The final recommendation is a tradeoff: strict binary event memory for configured
long-context bursts needing length checks; relaxed mode only when its acceptance
of malformed prefixes is acceptable to the surrounding framing contract. Neither
is a complete unknown-pattern solution. Keep deterministic firmware/framing and
the conventional listener in the larger system.

## 7. Replay, fixed widths and delivery

Ten pre-freeze tests passed. Independent nominal audit: 1,920 labels. Every saved
event/metric reproduced across 7,680 model/stream evaluations; 121,140 scalar gate
decisions and 315 checkpointed streams agreed. 282,660 integer gate score vectors
passed bounds. A post-freeze common 18-bit accumulator check exactly reproduced
3,360 score vectors with explicit signed wrapping. These are software checks,
not RTL equivalence or a formal proof.

Cold refitting of all 120 final models reproduced all metrics and predictions
exactly at the same seeds. This is reproducibility, not additional independent
confirmation. The 4,922-file outside-suite manifest is checked at delivery.
