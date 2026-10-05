# Preregistered scope and procedure

Written before implementing or running the architecture search. This is a local
synthetic study, not a released-design amendment or a project gate artifact.

## Tasks and observable framing

Two sampled binary lanes, idle `00`. A burst ends after **10 consecutive idle
samples**. Internal idle runs are shorter. A common causal 3-sample majority
filter is tested alongside no filtering. A receiver is initialized once at
stream entry, never at a generator boundary. It receives samples only. A
one-shot end detector re-arms on nonidle input; all methods use the same detector.
An emitted class is 0, 1, or 7 (unknown). The observed end detector is substantial
deterministic preprocessing, not learned synchronization. These tasks exclude
unframed continuous traffic and idle runs indistinguishable from delimiters.

* **pulse:** high widths (3,8) or (8,3), separated by 3 low ticks. Unknown equal
  widths and intermediate widths. Same known total duration and occupancy.
* **biphase:** six synthetic bits encoded into opposite half cells (3 ticks each),
  common preamble and suffix; known 001101 / 110001, unknown other codewords.
  This is a biphase-shaped burst, not a compliant named protocol.
* **clockdata:** the same six-bit codebook on clock/data lanes, 3 low-clock then
  3 high-clock ticks per bit, with a common prefix and suffix. Lane relationships
  matter. No SPI mode, timing, or electrical claim is made.
* **context:** eight pulse-width bits, widths 3/6 and 3-tick low separators.
  Class is XOR of bits 0 and 5; bits 1–4 are nuisance, bits 6–7 are a fixed 01
  footer. Invalid footer or invalid marker widths are unknown. A last-symbol
  classifier cannot solve the known classes; the first marker must be retained.
* **transfer (held out):** differential transition-coded eight-cell bursts.
  Two known transition words and other unknown words; common suffix and absolute
  starting level randomized. Generator contract may be inspected, but no family
  data or performance is used until architecture and adaptation recipe freeze.

Labels attach to intended waveform completion (first idle tick after last active
sample); injected noise does not rewrite labels. Training uses only completed
observed gate features with offline labels. Gates outside the expected timing
window train as unknown. Receivers never receive labels, original clean samples,
frame offsets, or randomized generator parameters. Signal-inferred masking of
old run history is allowed and charged to the run-memory front end.

## Streams and scoring

Training, development, confirmation seed namespaces are disjoint. Class and idle
choices are independent. Clean, ±1-tick run jitter, independent 1% per-lane sample
flips, combined perturbations, unseen unknowns, wide/short idle, and midstream
startup/error-recovery are reported separately. Unknowns occupy one third of
bursts. Near-match test unknowns differ from the training unknown codebook.
Startup crops remove truth events for incomplete leading bursts, leaving their
samples visible; any known emission on such a fragment is a false detection.

One-to-one matching, same class and emission time in [completion+8, completion+14].
This fixed tolerance covers the declared delimiter and filter delay, not arbitrary
late recognition. Count every duplicate/wrong/out-of-window known output as false.
Report known event precision/recall/F1, false known per 1,000 samples, explicit
unknown event recall, unknown acceptance, spurious unknown outputs, matched-event
latency and timestamp error. A wrong known class is both a miss and a false output.
Report exact 4-burst transaction success: intended symbol list (including 7),
order and absence of extra emissions must agree. This is the defined downstream
symbol-list contract, not a TX engine or complete firmware transaction.

## Architectures, controls and budgets

Compare (1) explicit sample-delay linear/quadratic memory (including an adapted
20-sample polynomial baseline), (2) sparse integer recurrent reservoirs with
single/multiple timescales and matched-total-node modular variants, (3) Boolean
cellular dynamics, and (4) run-duration event memory with linear or nonlinear
features. Include a generic deterministic run-template nearest-neighbor control
and a no-history/short-history ablation. Reuse mechanisms, not old selected scores.

Practical analytical envelope: at most **32,768 parameter/configuration bits**,
**4,096 dynamic-state bits**, **4,096 readout contributions per gate**. These are
study budgets, not a tile-area claim. Explore at least one larger history to
diagnose horizon failure, marking over-budget results. Count both input lanes,
filtering, counters, run storage, topology/coefficients, feature expansion,
accumulator width and event stabilization. Persistent memory and combinational
features are separate. No measured cell count, timing, or RTL equivalence claim.

## Selection and refinement

Identical train/development streams and readout tuning grid for learned methods.
Ridge fits plus score/margin rejection; compare integer q8 and q12 coefficients
for promising models, including integer states and explicit score bounds. Keep
all trials, including failed configurations. Inspect early failure modes and
add bounded hypothesis-driven candidates; record each in the ledger before its
run. Prefer the minimum per-task F1, then macro F1, subject to unknown recall
and cost. A robust recommendation needs every core task F1 >= .85 and explicit
unknown recall >= .80 on the aggregate perturbation mix; if none qualifies,
report the tradeoff/failure instead. Per-condition failures must remain visible.

Before confirmation, freeze the selected architecture/tradeoff set, all front-end
settings, readout/threshold adaptation grid, training seeds and saved configurations.
Use three independently trained readouts (and three topology seeds for stochastic
families), eight fresh confirmation seed blocks, and the same streams for paired
comparisons. Bootstrap blocks and training replicates to quantify paired differences;
do not treat individual ticks as independent trials. Report 95% empirical intervals,
no universal-optimum or statistical-population guarantee. One confirmation batch
is planned. Any confirmation-driven tuning requires relabeling that batch development.

Transfer uses the frozen structure and adaptation recipe, designated family
training/calibration streams only, and untouched fresh test streams. No architecture
or grid changes in response to transfer outcomes.

## Verification and preservation

Independently hand-check small generator vectors, causal prefix/suffix behavior,
framing, scoring duplicates/mismatches, temporal counterexamples, integer bounds,
and saved-config replay. Save source hashes, environment, inputs, full gate traces,
representative waveform traces and seeds. Re-evaluate saved confirmation with a
scalar integer readout path. Snapshot every repository file outside this suite,
including ignored files, and compare at delivery. Use `-B`, suite-local cache/temp
paths, no installs, no branches, no commits, no external hardware/protocol documents.

## Pre-confirmation amendments

Development refinements and their timing are recorded in `LEDGER.md` before each
run. Exact run counts versus duration-only support are frozen as a tradeoff set.
The eight final comparisons and quantization modes are in `configs/selection.json`.
An additional blind prefix-splice unknown probe is reported separately from the
seven-condition primary endpoint. No confirmation-driven refinement is allowed
within this batch. Transfer framing fixture seed 421 is development verification
only; fresh test namespaces and the unchanged adaptation grid are locked by
`artifacts/frozen/recipe.json` before transfer fitting. Parameters and source hashes
are subsequently locked by `artifacts/frozen/lock.json` before test generation.
