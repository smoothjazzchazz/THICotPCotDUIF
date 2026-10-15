# Decisions after the first matched block

2026-10-13. Before evaluating follow-up trials, the original >=20 point recovery
or >=15% MAC/parameter thresholds remain fixed; six-seed fresh replication is
required for a result. No first-block architecture is rejected for UART failure.

The completed registered first-block clocked fits all achieve exact development
messages, including tight setup. Some SPI1 fits retain one cold-start boundary
error; an earlier working summary incorrectly generalized zero boundary errors
from the displayed successful fits. The original scores and traces are unchanged.
The first block does
not distinguish those shapes by accuracy and is not qualification. UART remains
at zero complete messages, motivating continuation and structural comparisons.

Replay of historical seed-11 weights on the **new development** set shows:
SPI1/SPI3 full models recover 0/32 tight-setup transactions; deleting layer-1
readout contribution recovers 32/32 while retaining nominal/duty/pause recovery.
Deleting first-layer readout destroys reception. These are interventions on
trained configurations, not retrained shapes or independently confirmed results.
Complete traces are saved in `diagnostics/`. I2C needs some recurrent state in
that intervention; deleting all recurrence destroys its message recovery.

Next matched structural hypotheses:

| Candidate | Hypothesis | Support | Next step if it fails |
| --- | --- | --- | --- |
| SRR reverse | Direction matters relative to unchanged sparse inter-layer routes | Replicated UART improvement at equal cost | Direction alone is insufficient; test route alignment |
| SHH | Self edges restore local retention lost in a simple ring | UART recovery improves relative to SRR | Try fixed skips to mix context rather than self retention |
| SKK | Ordered ring+skips controls the sparse baseline's four edges/node | Better recovery than SSS at equal edges | Ordering alone insufficient; change inter-layer routing |
| SPP | A one-input random permutation is edge matched to true rings, but may have multiple cycles | Distinguishes single-cycle order from merely lower fan-in | Report component-cycle lengths and isolate routing |
| SRR aligned1 | One aligned inter-layer edge/node reduces computation; input-layer readout handles prompt decisions | Matched clocked recovery with >=15% lower model MACs/parameters | Restore fan-in or inject input into later layers |

All retain 24/20/20 nodes, same activation, leaks, generic features, all-node
readout, and registered schedule initially. Three seeds, seven profiles, initial
30 epochs matched to the baseline; UART receives an additional 90 epochs across
all original comparisons before interpreting shape-related training differences.
Further training follows measured improvement, with lower-rate/longer-window
rescue before describing a recipe plateau. Structural screens are not allowed
to replace the six-seed qualification suite.

## UART loss diagnostic, before its results

Additional UART training still gives very low exact-message recovery. Compare
inverse-frequency class weighting (capped at 128, normalized to mean weight 1)
against the existing square-root weighting on the exact same corpus schedule.
The receiver equations, features and event interface are unchanged. Apply this
to SSS/SRR/SRS registered and SRR current, all three screening seeds, both UART
profiles, for 120 epochs. The support criterion is the same >=20 point exact
message gain after paired fresh replication; lower loss alone does not qualify.
If it only improves event recall, inspect timing offsets and recurrent state
before changing node allocation or initialization. It is a training-recipe
comparison, and cannot establish a topology advantage by itself.

## First fresh structural replication selected from development only

All five follow-ups retain exact clocked-protocol development recovery across
three seeds. SRR with one aligned inter-layer input saves 240 MACs/tick relative
to SSS (1016→776), with 1086→846 learned parameters. Advance that pair to all
six seeds for I2C and SPI0–3, freeze those weights, then generate >=1000 fresh
messages per timing condition plus startup/rejection/recovery. This tests a
**clocked-receiver resource result**. UART is still unresolved, so even a pass
cannot qualify either multi-protocol shape or end the search. Constant LUT,
preprocessing, buffering, state and schedule costs remain explicitly reported.

## Input access, allocation and timescale tests

The routing counterexample proves a last-layer-only registered readout cannot
see a data change one tick before the sampling edge. It does **not** prove a
limitation for the actual all-node readout. The state-sensitivity probe shows
some trained configurations retain distinctions at 160 ticks without successful
UART messages. Retention alone is not useful temporal encoding.

Before evaluating these tests, preserve the same >=20 point replicated exact
message improvement threshold. Compare SRR 24/20/20 with input to all layers
(tests delayed credit/input access, explicitly more input edges), SRR 24/16/24
with unchanged leaks (allocation), then 24/16/24 with middle-layer leak 1
(tests a ring of sixteen actual state transitions, rather than a smoothed loop),
then 32/16/16 with those same leaks (more nonlinear extraction nodes). These are
generic rings and programmable leak values, not hardcoded protocol state or
timing counters. They use the same nine features and event-only assembly.
All six UART fits per configuration receive 120 matched epochs initially.
If loss falls without exact recovery, retain the trial and inspect timing
offsets; do not declare a capacity bound or select by loss. Clocked-protocol
coverage is required before promoting a UART-improving shape.

## Fresh clocked comparison 01 and next action

Frozen clocked comparison 01 recovers all valid complete messages in every
condition for both shapes and all six seeds. SRR-aligned1 passes all profile
gates in 6/6 seeds except SPI1 (5/6); SSS passes 6/6 except SPI1 (4/6).
SPI1 failures are a false STOP at tick zero, also present in the saved
development scores. SRR seed11 is worse than paired SSS seed11 on that boundary,
so do not describe all six paired configurations as uniformly better.
Keep this frozen confirmation, and extend **both** shapes' SPI1 fits to 60
epochs for all six seeds, with unchanged data/recipe/criteria. If the extra
training fixes development startup, freeze new snapshots and use a disjoint
fresh seed family. No masking or startup grace period is allowed.

## Generic readout factorization

UART remains unresolved after the initial connectivity/allocation/input-access
comparisons and loss rebalance; rare complete-message successes are below the
predeclared threshold. Test whether coupling "event now" and "bit value" in a
single six-class competition obstructs learning repeated UART sampling events.
Keep six affine readout channels, but interpret them as occurrence, bit value,
and four event types (bit/START/STOP/INVALID). All outputs are learned; inference
uses signs/argmax and the identical event-only assembler. No counter, waveform
decoder, new feature or teacher state enters inference. The node equations,
recurrent masks and total affine parameter count are unchanged.

Compare this head on SSS and SRR-aligned1 with the same 120-epoch exposure,
three seeds and both UART profiles. >=20 point exact-message gain remains the
screening target; six-seed fresh replication is still required. This tests the
readout organization **and its corresponding loss**, not an isolated recurrent
connectivity effect. If it helps, require a paired same-head topology comparison
and all clocked profiles before advancing. Loss values are not comparable across
the two objectives. Finite-difference gradients and streaming agreement must pass
before fitting this distinct architecture.

## Simple timing curriculum and input conditioning diagnostic

Train SSS and SRR-aligned1 on the same explicit 240-epoch curriculum: 60 epochs
of independent single-byte zero frames, 60 of 00/ff/55/aa, 60 of random single
bytes, then 60 on the full mandatory timing/error mixture. State remains
continuous within each stream. Independent simple and nominal development
streams measure whether the basic sampling sequence is learned before the full
mixed task. No simplified condition can count as qualification.

Generic input centering/scaling is encoded into **initial input weights and
biases**, estimated from training features without labels. The nine inference
features themselves are unchanged. Gain is bounded at 20 and parameter magnitude
at 7.99; unused constant lanes are centered through bias. This combined diagnostic
changes curriculum and initialization, so an improvement must be separated by
ablations before causal attribution. It is matched across both physical graphs.
The >=20 point exact-message gain threshold and full qualification remain intact.

## Circulation protected from distributed forcing

Simple-zero UART traces at curriculum epoch 60 show roughly periodic bit pulses
that drift/disappear within a character. Long-lived state alone did not provide
stable sampling phase. Hypothesis: distributing changing upstream values into
every ring node disrupts circulation. Compare the same SRR 24/16/24 allocation,
leaks 1/1/0.125, registered schedule and all-node readout with original routing
versus **one upstream edge into the first node of each ring**. Input into the
first sparse layer remains identical. Both start each ring edge at +1.05, zero
node biases, with the same 240-epoch simple-to-full curriculum and three seeds.
All weights remain trainable; no periodic stimulus, explicit phase register,
counter, protocol decoder, or additional inference state is added. The generic
ring's length is a physical allocation, shared across protocol configurations.

Support requires the original replicated >=20 point exact-message gain, with
clocked profiles and fresh confirmation before advancement. Failure suggests
that ring forcing is not the main training bottleneck; inspect learned ring
weights/phase before adding hardware. Initialization differs from earlier
recipes, so compare the two matched circulation fits to attribute routing.

## Counted dynamic gates as a distinct physical architecture

The previous plain-tanh routing/curriculum variants have not produced a replicated
UART advance. Test an explicitly different node organization: 32 stored scalar
states, each with one tanh proposal node and one sigmoid update-gate node. **All
64 nonlinear computational nodes count toward the limit**, allocated 24/20/20
as 12/10/10 pairs. Gates are input-dependent learned interpolation, not protocol
state machines. Each state obeys `h=(1-g)*old+g*tanh(z)`. The proposal and gate
have separately learned weights on the same fixed incoming mask. Both are
counted in parameters/MACs; mixing multiplies, nonlinear evaluations, state and
readout costs are explicit. No decoder, timing counter, auxiliary teacher state,
new feature, or extra hidden reservoir is introduced.

Hypothesis: learned update gates can preserve useful state selectively instead
of fixed leak settings forcing memory/timing tradeoffs. Compare SSS registered,
SRR registered and SRR current at 64 **computational** nodes, same data, seeds
and 120 epochs. They have 32 stored states, so they are not claimed as matched
64-state plain networks or an isolated ring-only effect. Then continue promising
fits in blocks. The original >=20 point replicated exact-message threshold
applies; full seven-profile six-seed confirmation remains mandatory. Float first;
integer gating is unimplemented until a gated candidate warrants that work.

## Off-chip timing supervision diagnostic

The gated screen also fails to produce useful UART recovery at 120 epochs.
Test training credit assignment directly: three auxiliary **off-chip training
readouts** supervise fine four-tick phase, coarse four-phase position and frame
progress from the existing causal UART label oracle. Their gradients shape the
same counted recurrent state; the auxiliary weights are excluded from deployed
configuration files, and runtime does not import the teacher. No timer, phase,
counter, generator boundary or auxiliary readout is provided to inference.
This is structured training supervision, disclosed separately from ordinary
event-only training; it cannot by itself prove a physical topology advantage.

Compare SSS, SRR-aligned1 and the counted gated SRR with identical training data,
three seeds and 120 epochs. Keep the same exact-event/message selection and
>=20 point meaningful-improvement threshold. Auxiliary loss/accuracy cannot
qualify a model. Verify prefix-causal targets, unchanged hidden trajectories
when only the auxiliary readout is exchanged, and checkpoint replay. If this
helps, repeat a paired same-recipe topology comparison and full confirmation;
if it fails, distinguish failure to learn phase from phase learned but complete
message assembly/boundaries still failing.

## Context feedback into feature extraction

The original layer routes form a feed-forward stack across layers, though each
layer recurs internally. The first layer cannot use deeper learned frame
context when interpreting a new input edge. Hypothesis: sparse return routes
allow contextual modulation of early feature extraction. Compare the same
SRR 24/16/24 one-port ring stack (leaks 1/1/0.125), with and without one registered
top-layer connection into each first-layer node. These 24 additional edges are
explicit in masks and resource counts. The cycle is causal: every return edge
uses the preceding tick. Both use positive-ring initialization and the same
off-chip auxiliary timing supervision, 120 epochs, three seeds, both UART
profiles. Inference is unchanged except the counted graph edges. Support and
failure criteria remain the original exact-message threshold; additional loss
improvement alone does not advance the shape.

## Protected generic circulation versus fully trained circulation

The auxiliary-supervised feedback trials are still improving, so extend both
matched routing variants to 600 epochs; they remain training-limited unless the
specified plateau/rescue diagnostics actually occur. In a separate named recipe,
hold the middle 16-node ring's recurrent gain at `atanh(0.5)/0.5`, with zero
internal biases except the trainable injection node. A pulse of amplitude 0.5
then circulates without intrinsic amplitude decay under zero forcing. The
initialization and freezing are generic reservoir dynamics, not a runtime timer
or protocol parser. Input, injection bias, other layers and readout still learn
off chip. All physical edges and parameters count even when this training
control holds some weights fixed. This is a partially fixed-reservoir control,
distinct from the fully trainable network; inference retains only the original
counted states and same nine input features.

Compare both return-routing choices with this recipe at 120 epochs, same seeds,
data and auxiliary supervision. The original complete-message threshold still
applies. If the protected loop retains timing but decoded messages fail, inspect
injection/reset interference and framing, rather than claiming a successful UART
receiver from oscillation alone.

## Loss targets versus the existing pulse-forming interface

The deployed pulse former already treats a held non-NONE class as one event.
The old loss nevertheless demanded a one-tick bit class followed immediately by
NONE, a stronger training demand than the event interface requires. Test a
three-tick **forward hold of BIT0/BIT1 training targets**, keeping START/STOP/
INVALID targets unchanged. Assert `pulses(expanded_targets) == original_events`
for every training stream before fitting. The hold uses an already observed
event value, so no future waveform information is introduced. Inference,
development labels, exact-boundary comparison and all qualification thresholds
remain unchanged. This is training-objective alignment, not a timing tolerance
or scorer relaxation.

Compare SSS and SRR-aligned1 at 240 epochs, three seeds and both UART profiles.
The same >=20 point exact-message gain is required before calling it meaningful;
any recipe benefit must be separated from the paired physical-topology result.

## Promising feedback result: continue and replicate, do not stop at ranking

At 600 matched epochs, top-feedback UART 8E1 seed11 reaches 92.37% exact
development messages (worst condition 84.375%); seed29 reaches 58.47%, seed47
remains poor. The matched no-return graph remains at zero 8E1 messages.
This is not yet a five-of-six replicated advance. Both graphs now receive the
same 600-epoch 8E1 training for seeds 71/101/131, and the same clocked-profile
screen. The first three seeds are refined at learning rate 0.0003 from their
selected 8E1 checkpoints, preserving Adam moments, with source epoch/hash and
total pretraining exposure recorded. For 8N1, use the same-shape 8E1 checkpoint
as off-chip pretraining, then learn separate 8N1 weights; this tests whether
already-learned timing transfers across the one-cell frame-length difference.
Both shapes use the identical selection/transfer rule and target exposure.
No source checkpoint, confirmation data or acceptance threshold is changed.

## Second feedback shape motivated by the observed advance

The top-return stack is the first topology with substantial UART development
recovery. Test one additional return from the middle timing ring into each
first-layer node, alongside the existing top return. This costs 24 additional
connections; all other allocation, one-port routing, leaks, initialization,
training exposure and interfaces remain identical. Hypothesis: direct access
to faster phase state plus slower frame context improves contextual input
processing. Train 8E1 for the same 600 epochs on seeds 11/29/47 initially. A
>=20 point unresolved-condition gain supports that hypothesis; comparable
recovery alone does not establish a resource improvement because it adds edges.
A full qualifying second shape would still require all seven profiles and the
unchanged six-seed fresh gates. Retain failed seeds and initialization dependence.

## Broaden a single injection point without driving every ring node

After 300 lower-rate refinement epochs, top-return seed11 reaches 97.03% 8N1
and 97.88% 8E1 development messages; seed29 reaches 79.24% 8N1. Several other
initializations still fail. This is not a replicated qualification result.
Hypothesis: the one-scalar inlet is a training bottleneck. Give the same single
entry node four evenly spaced upstream sources; all other ring nodes remain
undriven except by the actual closed ring. This adds six total inter-layer
edges relative to the two one-edge ports. Compare top-return and both-return
versions at the same 600 8E1 epochs and three initial seeds, before six-seed
advancement. Support requires >=20 point recovery gains on unresolved seeds/
conditions, confirmed under the original replicate rule. If it fails, retain
the seed-dependent result and inspect the inlet state instead of calling it a
node-count limit. The graph, not a protocol counter or extra feature, changes.

## Refine supported timescales without adding hardware

The original contract permits per-node programmable leaks; their storage and
mixing multiplies already appear in the resource ledger. Test learning only
the slow last layer's leak configuration during lower-rate refinement, while
keeping the first layer and the unsmoothed 16-node timing ring fixed. This adds
no inference state, feature, gate, decoder or arithmetic operation. Fitted leak
values must accompany each profile/seed's weights; float and integer replay
must both load those actual values. The graph and supported node equation are
the same across profiles. Initialization leak values in earlier shape manifests
are not claims that the printed leak registers are unprogrammable.

Compare weight-only refinement (`phase_fine`) with weight-plus-leak refinement
(`phase_leaks`) from each seed's own selected transfer checkpoint. Both use the
same full mixed streams, auxiliary teaching loss and 0.0001 weight learning
rate; leak Adam uses 0.00001 and the declared [1/64,1] supported range. Start
with seeds 11/29 on the top-return and both-return candidates. This is refinement
toward the unchanged absolute qualification gates, not a new >=20 point claim
on a profile already near 98%. Validate analytic leak gradients and bitwise
agreement with the original forward computation before fitting.

## Distinguish reused-data fitting from incomplete timing learning

Near-successful UART seeds still fail a few complete messages, most often at
combined jitter/mismatch corners. Preserve the original corpus and add 24
independent training banks from seed family 203000000, with exactly matched
per-epoch tick counts, the same timing support and the same generic features.
Compare `phase_rich` with `phase_fine` from identical same-seed checkpoints:
both have 0.0001 weight learning rate, the same auxiliary training loss, and
fixed leak settings. Only training examples differ. At these near-ceiling
scores, support means reducing remaining exact-message/boundary errors across
paired seeds without new invalid acceptances; it is a recipe diagnosis, not a
standalone topology advance. Record full selected-checkpoint event traces and
auxiliary phase accuracy to separate sampling drift from lost frame context.

## Expose phase combinations to the existing nonlinear first layer

Selected wider-inlet/both-return seed11 emits 20 extra events exactly eight
ticks from legitimate sample events. At those ticks its off-chip heads still
decode the correct fine/coarse phase and frame-progress classes. This rules
out erasure of those decoded distinctions for those errors, but does not prove
that a linear event readout can combine them. Rearming the event pulse only
after NONE does not change message accuracy; the extra pulses are isolated.

Add a second, quarter-ring-offset return from each ring into every first-layer
node (`both2`), costing 48 more physical edges. Retain the same 64 node states,
input interface, readout and registered schedule. Compare with `both1` starting
from each seed's own selected 600-epoch 8E1 checkpoint. New routes and optimizer
moments start at zero; common weights/moments are copied by exact edge identity.
Verify bitwise-identical initial predictions, then train both for 300 identical
full-mixed epochs at 0.0003. A replicated >=20 point gain on unresolved
conditions under the original rule supports a topology-dependent advance;
smaller reductions of the half-cycle false pulses are diagnostic only. If it
fails, investigate readout separability or training coverage without claiming
that the stored phase information disappeared.

## Is trainable circulation destabilizing some initializations?

Several wider-inlet seeds improve and then lose reception while the learning
rate stays at 0.003. Test the strongest wider/both-return graph with the same
positive 1.05 ring initialization as `phase_circulation`, but freeze the 16
middle-ring recurrence weights and the 15 undriven middle-node biases during
off-chip training. The driven inlet and all other weights remain trainable.
This differs from the earlier 120-epoch `phase_clock` trial, which used a
different graph and gain. Run all six seeds for the same 600 epochs. This is a
training-stability diagnostic on the same physical graph, not a cheaper graph
or hidden oscillator added to the receiver. Evidence would be improved
worst-seed complete messages without sacrificing successful conditions; a loss
plateau alone will not establish representational failure.

## Isolate the event readout from recurrent learning

Fit only the existing six affine event outputs on fixed causal state
trajectories from the selected wider/both-return 8E1 models. Twelve training
banks are retained; development data is used for selection only. State capture
must agree bitwise with the deployed kernel and all fitted development
decisions must agree with scalar inference. Use 60 passes over the entire
training-state set, shuffled 4096-row minibatches, 0.003 Adam, original class
weighting and the original parameter range. This has much more readout
exposure than a normal single-stream epoch and is recorded accordingly.
Eliminating the half-cycle events with a readout alone would locate a recipe
bottleneck; failure of this optimizer is not proof of linear inseparability.

## Declared two-recipe off-chip selection, preserving every seed

The fixed-ring recipe reaches 99–100% 8E1 development recovery for seeds
11/47/71/101, while seed29 learns better with trainable ring gains. Both use
the identical physical graph. Define an explicit off-chip training portfolio:
for every seed, run both 600-epoch recipes, select its own checkpoint by the
unchanged development key, and refine separate 8N1/8E1 configurations for 300
full-mixed epochs at 0.0003. A selected frozen-ring recipe keeps its training
mask; a selected trainable-ring recipe keeps all its weights trainable.
Include the selected starting checkpoint as epoch zero so refinement cannot
silently discard a previously successful configuration.

This spends 1200 pretraining epochs per seed before profile refinement. It
tests reproducibility of the declared training program, not one optimizer
trajectory. Every seed gets the same alternatives and selection rule; no
successful seed's weights replace another seed, no failed trial is deleted,
and no qualification threshold changes. Any comparison with a second shape
must give it the same two-recipe budget. Configuration selection is still
frozen before new confirmation data is generated.

## Fresh UART confirmation exposes remaining coverage gaps

`uart_fixed01` freezes all six wider/both-return fixed-ring configurations
before generating seed family 211000000. The unchanged full UART gates fail:
even development-perfect seeds retain rare corner/boundary errors, and some
miss recovery after cold mid-frame startup or fail long continuous messages.
Keep that confirmation immutable. It is a failed confirmation, not a relaxed
qualification or a new training corpus.

Generate separate training family 223000000 and development family 224000000.
Include 1024-byte continuous random/repeated payloads, 256-byte cases,
malformed/recovery sequences, and cold startup partway through a frame.
Reference labels remain causal offline teaching labels. The ambiguous startup
prefix is handled exactly as in the original confirmation gate. No frame reset
or protocol-specific feature enters inference. Extend both candidate graphs
under the same recipe and exposure before any comparative claim. Use a new
untouched confirmation family after this refinement; never recycle 211000000
as fresh evidence. Larger training banks mean more ticks per epoch and must
be reported by exposure rather than compared by epoch count alone.

The extended refinement starts from each seed/profile's selected portfolio
checkpoint, retains its frozen-ring mask where applicable, and uses 60 full
extended-bank epochs at 0.0001. Its larger development distribution is scored
separately from the original one, including at epoch zero. Continuous chunked
development inference is tested against full-sequence inference to bound
memory use without changing results.

8E1-to-8N1 transfer is particularly weak for one otherwise successful 8E1 seed.
Test independent 8N1 fixed-ring training from scratch for all six seeds on both
return-path graphs, at the same 600-epoch budget. This isolates whether that
failure depends on transferring a previously learned frame length. Report
this additional fitting exposure; do not attribute a recipe rescue to fewer
nodes or silently replace one seed by another.

## Which added return routes matter?

The two-return graph reaches perfect original-development 8N1 reception on all
six seeds during portfolio refinement. Before defining another graph, ablate
the additional fast-ring return and additional slow-ring return separately
from every selected 300-epoch seed. Each ablation zeros exactly 24 existing
weights. It is a causal diagnostic on the fitted model, not a smaller trained
architecture or a qualification result. If one removal preserves nearly all
recovery across seeds, test that physically pruned graph with matched
refinement; if both removals break reception, retain the added hardware and
investigate the remaining long-traffic/recovery failures instead.

## Distinguish repeated-bank fitting from broader sequence coverage

An additional paired recipe gives every epoch a new independently seeded
extended training stream (family 241000000), instead of cycling through the
same twelve banks. Match each epoch's exact tick count, class weights, starting
checkpoint, learning rate, gradient mask, auxiliary targets and development
distribution to `phase_extended`. Keep every generated bank and its hash.
Stream one bank at a time to bound memory. This is a controlled training-data
comparison, not a new topology claim. Support would be fewer complete-message,
startup/recovery and boundary failures on the independent extended development
set; any final claim still requires another frozen fresh confirmation.

## Profile-specific initialization before fresh-stream refinement

The same physical graph can succeed when 8N1 is fitted independently while
8E1-to-8N1 transfer fails. Give every seed on both return-path graphs the same
two source options: its own selected portfolio checkpoint and its own native
profile fixed-ring 600-epoch checkpoint. Evaluate both on the independently
generated extended development set and select by the unchanged key. Then use
60 fresh-stream epochs at 0.0001, preserving the selected training mask.
This separately named `phase_profile_fresh` program includes extra native
profile fitting; it is not the isolated repeated-bank versus fresh-bank
comparison. Preserve both source scores/hashes and shared pretraining
provenance so exposure is neither hidden nor double-counted. Selection never
uses confirmation examples or another seed's weights.

## Focus refinement on errors after phase has been learned

Test gamma=2 multiclass focal loss against weighted cross-entropy from the
identical selected extended-development checkpoints. Both refinements reset
Adam moments, use the same 0.0001 learning rate and fresh training streams,
keep the same frozen-ring mask, and omit auxiliary-head training so it cannot
dominate the now-small main classification gradients. The deployed node
equations, weights supported, readout and event decoder remain unchanged.
Start with seeds 11/131 of the two-return graph: one unresolved 8N1 seed and
one unresolved 8E1 seed, with the opposite profiles as regression controls.
Run 30 matched fresh-stream epochs, preserve both results, and advance only
if exact-message/boundary errors improve without new rejections or losses of
previously correct behavior. A small pilot is not a topology claim or proof
of representational limits.

The objective is `-(1-p_y)^2 log(p_y)` with the existing class weights. Its
gradient multiplies the ordinary softmax cross-entropy gradient by
`(1-p_y)^2 - 2 p_y (1-p_y) log(p_y)`. Finite differences check input, recurrent,
bias and readout gradients; forward state and logits must be bitwise identical
to ordinary inference. The motivation is error-focused fitting, following
[Lin et al., Focal Loss](https://arxiv.org/abs/1708.02002), not evidence from that
paper that protocol receivers will work.

## Adaptive continuation of unresolved configurations

The focal pilot does not outperform its cross-entropy control on the remaining
8E1 boundary errors, so it is not promoted. Preserve both trials. Apply one
rule to both graphs and every profile/seed: configurations missing any exact
message, exact boundary, invalid-acceptance or background-acceptance gate
after 60 fresh-stream epochs continue to 120. Already passing configurations
receive no additional fitting solely to reduce loss. Generate banks 61–120
with the same deterministic disjoint family and preserve the first 60 banks.

For those same unresolved cases, if native fixed-ring fitting also failed its
original-development gates at 600 epochs, continue that source run to 1200.
This checks training adequacy rather than declaring its graph incapable.
The full selection lists are immutable job manifests. Adaptive budgets and
all still-failing seeds remain visible; qualification thresholds do not change.

## Route invalid-frame context directly to the slow ring inlet

The remaining two-return seed131 8E1 boundary error is a confident false STOP
exactly 16 ticks after a framing INVALID, while the line has returned high.
A small NONE-bias shift cannot suppress its 3.88-logit margin. This motivates
a routing hypothesis: the final ring receives first-layer input context only
through the circulating middle ring, so its frame state can persist too long.

On the cheaper one-return graph, compare its current routing with four direct
first-layer-to-final-inlet connections. An edge-matched control adds four
different middle-ring sources to that same inlet. All rings remain genuine
closed directed cycles, and only the existing inlet is driven. Each added
route is registered; each variant adds exactly four weights/MACs. Start seeds
11/29/47 from their own selected 60-epoch profile-fresh 8E1 configuration.
New routes start at zero; copy common parameters, moments and frozen masks
by exact identity and verify identical initial predictions. Train all three
for 30 epochs using the same fresh banks 61–90 at 0.0001.

This near-ceiling refinement targets the unchanged absolute qualification
gates, not a new claim that a small percentage gain meets the original
20-point meaningful-advance threshold. Boundary/recovery improvement without
regression supports advancing to six seeds and all profiles; a full result
still requires frozen independent confirmation. A four-edge hardware increase
will remain explicit even if the experiment helps.

## Separate readout error from persistent recurrent context

The bridge pilot did not give a replicated improvement. Fresh-stream continuation
also leaves near-ceiling errors, while native fitting to 1200 epochs improves
some previously weak seeds. This is evidence of recipe dependence, not a
representational impossibility result.

Choose each graph/profile/seed's best latest native-fixed, profile-fresh, or
extended checkpoint using the unchanged extended-development key. Preserve
already passing configurations without extra updates. For unresolved ones,
compare 60 epochs of readout-only cross-entropy at 0.001 with all previously
trainable parameters at 0.00001. Reset Adam for both; omit auxiliary fitting.
Alternate new recovery-heavy 65536-tick streams (family 271000000) and the
existing independent long-message fresh streams. Invalid bytes, error types,
following payloads and idle durations are broadly sampled, not copied from
failed confirmation. The runtime remains identical.

Support for a readout limitation is correction by frozen-state readout fitting;
support for state correction is improvement only when recurrence is fitted.
Neither failed recipe proves infeasibility. Promotion requires the same exact
message, boundary, rejection and recovery gates, followed by a frozen fresh
confirmation. These refinements do not independently claim a topology advance.

## Reallocate equal hardware toward phase returns

Removing either extra return set from fitted two-return receivers collapses
8N1 recovery. Test whether those routes are more useful than first-layer
feedback: retain both returns from each ring, but reduce the first sparse
layer from self+three to self+one connection per node. The mask is selected
once by a fixed topology seed, shared by every profile and training seed;
it is a strict subset of the original sparse mask. Both directed rings,
inlets, leaks, inputs, readout and registered schedule stay unchanged.

This removes 48 recurrent connections and preserves the 48 extra return
connections. It therefore exactly matches the one-return shape's 792 MACs
and 862 parameters, compared with 840/910 for the full two-return graph.
Train all six 8E1 seeds from scratch for 600 fixed-ring epochs with the same
data and exposure as both existing controls. No pretrained larger topology
is used. Strong development repeatability supports extending to 8N1 and all
clocked profiles; failure motivates retaining local mixing or changing which
phase routes receive those resources. Qualifying this as a second physical
shape still requires all seven profiles and frozen fresh confirmation.
The original 20-point or 15-percent meaningful-improvement rule is unchanged;
a smaller gain is only a diagnostic or progress toward absolute qualification.

## Full-profile freeze 01

Recovery-heavy readout-only fitting corrected both remaining two-return 8E1
seeds. All six 8N1 and all six 8E1 selected models pass extended development.
The matched low-rate full-state control did not remove their final boundary
errors, so useful frame context existed in the frozen representation for these
cases. This is a recipe diagnostic, not a general proof of linear separability.

Freeze the complete two-return 24→16→24 graph with separately trained weights
for all seven profiles before generating family 261000000 (`full_shape01`).
Use recovery-readout selection for UART and existing matched clocked fits.
SPI1 seed11 still has one development boundary error, which remains visible;
other clocked seeds meet development gates. Run float and Q3.12 separately on
the full unchanged confirmation suite. No confirmation result has been seen
at the time of this freeze. A development pass alone is not qualification.

At the first mid-run reallocation check (about 320 epochs), five of six 8E1
seeds recover 86–100% of original development messages and one remains near
41%. This is enough promise to start the other mandatory profiles while
8E1 completes its predeclared 600 epochs; it is not six-seed qualification.
Train native 8N1 for the same 600 fixed-ring epochs and clocked profiles with
the existing matched 30-epoch recipe (SPI1 continued to 60 for all six seeds).
Retain every seed and inspect learning curves before deciding continuation.

## Precision and cold-start coverage after failed full confirmation

`full_shape01` is preserved: 8N1 passes 3/6 seeds and 8E1 passes 0/6 in both
float and integer replay. No invalid or background messages were accepted.
Failures are rare complete-message/boundary errors, concentrated at timing
corners and recovery after cold mid-frame entry. All development passes did
not imply qualification. No failed confirmation waveform is used for fitting.

Generate fresh development families 303000000/304000000: 256 messages per
valid timing condition plus 64 independent cold starts, with long/all-byte/
repeated-pattern coverage. Add 256 independent cold training streams from
family 301000000. Each stream is continuous; state resets occur only at an
explicit independent cold-start experiment, never between its messages.

Test fixed-state readout fitting on the full two-return graph, all six seeds
of both UART profiles. Keep every input, recurrent, route, bias and leak
parameter fixed. For 20 rounds, mine low-margin training states from one
existing fresh long stream, one recovery-heavy stream, and 16 new cold-start
streams. Fit the six existing affine outputs using bounded L-BFGS-B on squared
multiclass margin loss (margin 0.5) with 1e-6 squared distance to the source
readout. Keep up to 100000 hardest accumulated training states. Selection uses
worst development-case exact recovery, total exact recovery, boundary and
rejection errors; all absolute qualification gates remain unchanged.

This tests whether missed coverage/readout separation explains the rare failures.
A successful fit must retain long-message performance; inability to fit sampled
states is not a proof that the architecture is incapable. Preserve solver status,
retained training supports, full learning curves, every checkpoint, source hashes,
and scalar deployed-inference validation. If errors remain in fixed states,
the next comparison must fit recurrent recovery or change its routing. SciPy
1.17.1 is installed only in this run's dependency directory; NumPy remains 2.5.3.

## Current-sample routing in the learned phase architecture

The edge-reallocation pilot is less repeatable at 600 epochs than the full
registered two-return graph. Retain it, including still-improving seeds and
its native-profile trials; this does not establish a capacity limit.

Test current-sample forward routing in the same S24→R16→R24/two-return graph.
Only inter-layer forward-edge delay changes from one tick to current sample.
All intralayer ring/sparse edges and all return paths remain registered, so
there is no algebraic loop. Node count, weights, leak constants, input/readout
access and seed-keyed initialization remain paired. The hypothesis is that
faster arrival of input/frame context improves phase recovery after invalid
traffic or cold entry. The cost is three activation stages on the sample path
instead of one, even though connection/MAC counts match. No frequency/STA
claim is made.

Start all six 8E1 seeds with 600 native fixed-ring epochs, exactly matching the
registered control's original exposure. A replicated improvement on the broader
cold/timing development suite supports training the other profiles and a frozen
confirmation. Keep the original 20-point meaningful-advance criterion; any
smaller improvement is qualification progress, not a newly declared advance.
Failure suggests the recovery representation or context feedback, rather than
one tick of forward routing alone, needs improvement.

## Fit recovery dynamics while preserving fast circulation

The margin pilot currently degrades the broader suite. Its raw-class margin
objective is stricter than pulse-level event correctness, so residual support
errors are not an event-interface infeasibility proof. Preserve the declared
20 rounds and solver diagnostics.

In parallel, from each two-return seed's own recovery-readout selection, fit
existing context/recovery parameters for 60 epochs at 0.00001 with reset Adam.
Hold the learned middle-ring edges and its undriven biases fixed in every seed;
all other existing weights may adapt. Use one long fresh stream and eight
independently cold-started training streams per epoch, cycling all 256 startup
cases. There are no resets within a stream or between its messages. Omit
auxiliary heads during this refinement. Evaluate the new broad precision suite
every five epochs with the original worst-condition/exact-message/error key.

Compare with the fixed-state readout trial on the same precision development
suite. Improved recovery only when context weights change supports a state
adaptation explanation; neither failed optimization proves a capacity bound.
This is targeted recipe work on unresolved behavior, not a new topology claim.

## Distributed phase-ring inlets with an edge-matched control

Many cold-start cases remain difficult despite near-perfect ordinary messages.
Test whether a single driven ring node delays or restricts clearing phase state.
Keep the registered two-return graph and add three more evenly spaced fast-ring
inlets, each receiving the same four first-layer source nodes with independently
learned weights. An edge-matched control adds twelve first-layer sources to the
original inlet instead. Both add exactly 12 MACs/weights (852 MACs, 922 total
parameters); the closed rings, slow inlet, feedback and input/readout stay fixed.

Start seeds 11/29/47 for both UART profiles from the exact source used by the
existing single-inlet `phase_precision` baseline. New weights start at zero;
verify bitwise identical initial predictions and map parameters by edge identity.
Apply the same 60-epoch precision recipe, data, reset optimizer and frozen fast
circulation mask. Faster and more reliable cold recovery from distributed
injection, beyond the single-inlet equal-edge control, supports the routing
hypothesis. No change or equal benefit suggests extra mixing/training rather
than inlet position; failures are not capacity proofs. This pilot targets the
unchanged absolute qualification gates and must expand to six seeds/all profiles
before any full qualification claim; the original meaningful-gain threshold is
unchanged. Additional wiring and arithmetic remain explicit costs.

## Startup oracle audit and corpus correction (not a gate relaxation)

The explicit payload audit found 49 affected cases among 148 inspected cold
startup/development cases. In `full_shape01`, the recomputed UART reference
misdecodes one declared valid 8N1 message and four declared valid 8E1 messages.
A short high gap is not guaranteed synchronization from an unknown UART phase;
the reference can still be completing a false frame started inside the prefix.
Consequently, matching that reference is not proof of the declared payloads.
All affected results remain preserved. The clocked confirmation cases have no
payload mismatch, so the confirmed clocked cost result is unaffected.

Stop `precision60` and `distributed_precision60` at their retained checkpoints;
mark their affected cold-start evidence invalid for qualification/architecture
claims. The completed `hard_readout20` trial also used that corpus, so it is not
a capacity result. Earlier cold-cut training/refinements remain historical
recipes, with this supervision limitation now explicit. Correctly labeled
ordinary timing/invalid trials remain individually usable. Source checkpoints
for new fitting remain the pre-audit recovery-readout models, not interrupted
precision or margin-fitted models.

Version 2 uses new disjoint families 311/313/314/315 million. Insert 256 high
samples after the unscored arbitrary-start prefix and before scored recovery.
This exceeds a complete 8E1 frame even at +3% timing and one-tick edge jitter;
any pending false frame ends during the mark interval, and a subsequent falling
start edge is observable. The receiver receives only samples, with no reset,
boundary, timer state or synchronization flag. Assert every valid post-cut
payload against generated bytes. Prefix scoring ends only at the predeclared
first valid message after this guaranteed synchronization opportunity.

This implements the original requirement of recovery **after an observable
synchronization opportunity**, rather than silently treating an ambiguous
short gap as one. It does not waive any scored message, boundary, rejection,
timing or seed requirement. Keep ambiguous-short-gap cases as a separate
diagnostic; do not turn their apparent failures into a representation claim.
Run the same baseline/distributed/equal-edge precision comparison again under
`phase_precision_v2`, in new directories. Future frozen confirmation uses
`confirm_v2`, verifies payloads, and uses an unused family (331000000 reserved).

## Continue promising reduced-feedback fits

Apply the same original-development continuation rule used for the other
ported graphs to the equal-cost first-fan-in-two graph. Configurations missing
any message/boundary/rejection gate at 600 native fixed-ring epochs continue
to 1200; passing configurations receive no extra fitting. This corpus begins
from idle and is unaffected by the cold-cut audit. The preserved 600-epoch
comparison remains the matched structural result; 1200-epoch rescue is a
separate training-adequacy result with its own exposure manifest. Do not call
this lower-cost graph incapable from its first block or mix rescue scores into
the matched 600-epoch table.

The corrected development distribution also warrants re-evaluating each seed's
already-trained native fixed-ring (600 epochs) and portfolio (300 epochs after
its recorded pretraining) alternatives. Apply these same two options to every
seed/profile of the full two-return graph; record every score and source hash.
This is checkpoint/recipe selection on development, not a matched architecture
comparison or a new confirmation. It may avoid spending more fitting on an
inferior source chosen by the older, smaller development set.

Expand both inlet-location variants to seeds 71/101/131 under the same corrected
60-epoch precision recipe. The initial pilot shows that both can preserve full
recovery in easier cases, but does not establish a routing advantage. The
remaining seeds include the base graph's unresolved conditions and are needed
for the unchanged six-seed gate. Keep both equal-edge alternatives, all failures
and exactly paired starting functions/exposure. This expansion is not a winner
selection. Generate long-stream training banks 61–120 non-destructively in
case unresolved configurations need a further declared block; preserve the
original 60-bank manifest and all source snapshots.

## Readout refinement on verified precision coverage

After each corrected 60-epoch precision block, preserve configurations that
already pass every development gate without further fitting. For unresolved
ones, freeze every recurrent/input/context parameter and fit only the six
existing affine outputs for 60 epochs at 0.001 with reset Adam, using verified
long banks 61–120 and the corresponding cold-start rotation. This cross-entropy
fit uses all training ticks as anchors, unlike the earlier margin-mining pilot.
It starts from each seed's own selected corrected block. No confirmation sample
enters fitting or selection. The rule applies uniformly to all seeds and graphs;
new output directories retain the complete source and exposure chain.

## Native training with both cold-start modes

Verified traces show phase slips rather than only wrong bit readout: in one
remaining 8N1 seed, the first valid frame's bit events are one tick early;
other rare frames acquire extra phase-shifted events. A readout-only block
has not corrected them. The v2 refinement supplies arbitrary mid-frame cold
starts followed by guaranteed synchronization, but direct-from-idle cold starts
are underrepresented in that refinement even though they appear in confirmation.

Add separately generated known-idle cold streams (family 341000000) and
independently started malformed/recovery streams (342000000). Keep the verified
v2 development suite unchanged. Train the registered two-return graph natively
from every original seed for each UART profile: ten original clean/pattern
curriculum epochs, then one long verified stream, four mid-frame/synchronized
streams, four known-idle streams and two malformed/recovery streams per epoch.
Use the original 0.003 fixed-ring/auxiliary recipe and 512-tick windows for 120
epochs, preserving fast-ring circulation and all checkpoints. This gives each
profile its own native learning trajectory and tests whether low-rate rescue
or cross-profile pretraining trapped earlier fits. Report actual training ticks;
epoch counts are not comparable to 32768-tick native pretraining.

This is a data/recipe experiment on an unresolved graph. It does not change
interfaces, physical state, runtime features or qualification thresholds, and
cannot itself establish a topology gain. The independent stream boundaries
are training/test cold starts, never hidden resets within deployed messages.

## Matched coverage-complete schedule and allocation comparison

Extend the native-v3 program to two targeted alternatives with the same six
seeds, profile-specific training, 120-epoch curriculum/data exposure, interfaces,
ring initialization and checkpoints:

- Current-sample 24→16→24: only forward execution delays change; return paths
  remain registered. This asks whether one-tick forward delays impair phase
  acquisition. It costs three activation stages per sample instead of one.
- Registered 16→16→24: preserve the fast 16-node and slow 24-node memory rings,
  while reducing the first sparse mixer. All nine inputs still enter each
  first-layer node; both returns per ring and all-state readout remain. Costs
  are 656 MACs and 718 parameters versus 840/910 (21.90%/21.10% reductions).
  This asks whether fewer local feature-mixing nodes suffice while memory
  length is retained. The resized family's sparse mask and quarter-spaced
  routing are fixed and recorded; this is an allocation-family comparison,
  not a claim that all common edge identities are unchanged.

Before evaluation, meaningful lower-cost improvement still requires within one
point on every claimed valid condition at >=95%, no worse boundary/rejection,
and >=15% fewer MACs and parameters, replicated across seeds on fresh frozen
confirmation. Full qualification still requires every exact-message/boundary/
rejection/recovery gate in >=5/6 seeds per mandatory profile. If the reduced
mixer loses recovery, examine lost context features or restore width; do not
infer a representational limit from an unfinished training curve. Neither
alternative inherits a successful larger model's weights.

## Calibration after correcting both startup modes

Native-v3 is a separate matched trial, not a reason to discard a stronger
same-seed configuration. For practical qualification, choose each seed's best
completed verified-development checkpoint among precision-v2, its readout-only
refinement and native-v3 where completed. Preserve every candidate and source
hash. This checkpoint portfolio is explicitly not a matched topology ranking;
training budgets and source paths remain visible.

Retain passing configurations at epoch zero. Give unresolved configurations
60 calibration epochs at 0.0001 with reset Adam, no auxiliary-head updates,
fixed learned fast-ring edges/undriven biases, and the full combination of
known-idle, mid-frame/synchronized, malformed/recovery and long-message streams.
Use new verified long banks 121–180. The existing broad verified development
suite and all qualification thresholds remain unchanged. This tests whether
complete startup coverage plus a moderate learning rate fixes remaining phase
slips without disrupting correctly learned behavior.

## Conditional slow memory with an unchanged fast ring

Register before fitting: compare registered 16→16→16 stored states, first sparse,
fast directed ring and slow directed ring. Four first-layer quarter nodes drive
one inlet on each ring; both rings return two quarter-spaced states per first
node. All nine generic features enter the first layer and all states feed the
same six affine event outputs. The control uses fixed slow leak 0.125. The
alternative adds one sigmoid update gate per slow state, reading four first-layer
quarter states, fast-ring inlet state and its own previous state. Gates read only
registered states. No event feedback or protocol logic is introduced.

The alternative has 48 stored states, 48 tanh proposals and 16 sigmoid gates:
64 nonlinear compute units, 696 MACs and 766 parameters. The fixed-leak control
has 48 compute units, 600 MACs and 654 parameters. Compare their matched graph
and training to isolate conditional memory; also compare the existing 64-unit
24→16→24 registered baseline (840 MACs/910 parameters) for the total budget.
State count and routing differences remain explicit. Sigmoid uses a shared tanh
LUT with additional fixed scaling/addition; state, bias and routing costs count.

Hypothesis: a learned hold/update decision lets slow context survive transitions
but clear during recovery without disturbing fast circulation. Support requires
replicated complete-message and boundary improvement, not lower loss. Use the
same native-v3 coverage, 120 epochs and initial seeds 11/29/47 on both UART
profiles; expand promising behavior to all six and clocked profiles. Existing
meaningful thresholds (20 points unresolved recovery, or >=15% cost reductions
with within-one-point recovery/no worse rejection) and original qualification
gates are unchanged. Failure directs examination of gate saturation/context
routing and matched gate-frozen ablations; an unfinished curve is training-limited.

## Preserve native peaks before lower-rate continuation

Native-v3 trajectories repeatedly reach useful event recovery and later collapse
under the initial 0.003 rate. This observed instability is a recipe limitation,
not evidence against the physical graph. Continue each completed native-v3
configuration from its own best 120-epoch development checkpoint at 0.0001,
reset Adam, disable auxiliary optimization, keep its fast-ring mask, and use
verified long banks 181–240 with both startup modes/error recovery. Give unresolved
configurations 60 epochs; passing configurations receive no extra optimization.
Apply the identical rule to registered/current/reduced and mixed/control trials
as their initial blocks complete. Preserve the native comparison separately;
report the adaptive extra exposure, all failed epochs and source checkpoint.
No seed/profile transfer or change to qualification/meaningful thresholds.

## Training-only error-directed continuation

The remaining developed base-model errors are rare phase slips and extra STOPs
after a true INVALID. Test a bounded 56-round continuation on independently
seeded training cases (family 351000000), covering all 256 first payload bytes,
all seven timing conditions, known-idle starts, synchronized mid-frame starts,
and malformed/recovery contexts. Development examples are never replayed as
training. Each round uses 64 cases; the byte/condition schedule crosses each
byte with every timing condition over 28 rounds, then repeats with fresh phases
and contexts. One half includes malformed frames before the scored valid frame.

Mine the existing model's pulse errors in training only. Retain at most 32
512-tick windows centered 256 ticks before a training error, plus 32 deterministic
random anchor windows. Initial window states come from the current model's own
continuous causal trajectory, never teacher state. Recompute trajectories next
round; within-round updates use those truncated initial states, an explicitly
recorded approximation. Optimize the existing event objective at 0.0001 with
reset Adam and the same frozen fast-ring edges/biases; no new runtime mechanism.
Save all selected windows, optimizer state and checkpoints. Evaluate the same
verified development suite every five rounds. Limit the first test to the five
unresolved base configurations; retain the seven passing ones without training.

Support for a training/coverage explanation is successful held-out recovery
using the unchanged graph. Continued failure is not a capacity proof. This is
an adaptive recipe diagnostic, not a matched topology result; any selected
configuration still needs a new frozen confirmation and the original six-seed
profile gates. Already successful profiles receive no further loss polishing.

### Causal context interventions (diagnostic only)

For developed base N131, the single remaining STOP-as-BIT1 error occurs at tick
141874 of the minus-jitter long stream. Keeping subsequent generic features
identical, replacing the fast-ring state with zero 512 ticks earlier corrects
that event with zero errors in the last 192 ticks (original: one). Resetting all
states 512/1024 ticks earlier or the slow state 1024 earlier also corrects it.
This is evidence that older recurrent state contributes to the error; it is
not evidence that a runtime reset is available, safe or sufficient. Replacing
states farther back does not monotonically improve behavior. No reset was added
to inference and no intervention counts as a passed case.

For E131's extra STOP at tick 1677 in cold_039, the few older-state interventions
that suppress the extra event create 16–23 other local pulse errors. That is not
a useful correction. Both full intervention grids, original margins and source
hashes are under `diagnostics/context_n131` and `diagnostics/context_e131`.
These observations support testing conditional memory and interference, rather
than assuming that more passive memory alone will fix every error.

## Complete the mandatory clocked configurations for reduced candidates

While unresolved UART work continues, fit I2C and SPI0–3 on the same fixed
16→16→24 plain and 16→16→16 plain/mixed graphs. Use all original six seeds,
matched original corrected-coverage data, 30 epochs (SPI1 60, matching the
existing full-profile 64-node baseline). This asks whether the smaller first
layer and changed slow-memory mechanism preserve the learned clocked receiver.
Every protocol sees the same physical mask, node equation and interface; only
its demonstration weights/configuration change. These fits are prerequisites,
not qualification, and do not replace the pending UART comparisons. If precise
clocked sampling fails, inspect first-layer/readout timing and gate contribution;
do not give a protocol its own physical shape. Meaningful and full-profile
thresholds are unchanged.

## Training-only boundary margin calibration

The E131 developed model's one extra STOP is linearly separable by its existing
STOP-output bias: a development-only diagnostic finds an onset-preserving bias
offset interval (-3.1369, -1.0890). This diagnostic changes no weight and does not
choose the deployed offset. It motivates an off-chip calibration using training
samples only, with the same causal pulse interface and all core weights fixed.

For each unresolved verified-development configuration, collect STOP-vs-other
logit thresholds on all 256 verified cold training cases, all 256 known-idle
training cases, all 64 malformed/recovery cases, and verified long banks 181–187.
For a STOP onset at t, the allowed bias offset is [threshold[t], threshold[t-1]);
all unwanted onsets forbid their corresponding interval. Intersect the true-onset
constraints, subtract all false-onset intervals, enforce the existing ±7.99 bias
bound, and choose the midpoint of the widest remaining interval. No development
or confirmation sample enters this computation. If no interval exists, retain
that diagnostic failure; it proves only failure of this one-parameter repair.
Validate the proposed checkpoint against the unchanged broad development suite
and keep the original if the existing selection key is better. Already passing
configurations are copied unchanged. This is an explicit same-seed checkpoint
portfolio/calibration recipe, not a matched topology advance. Preserve all source
options, constraints, proposed/selected checkpoints and state-transition identity.
Any new qualifier still requires frozen independent confirmation.

### Bias calibration outcome and paired window rescue

Training-only bias calibration found no feasible interval for E71 or E131;
E131's required lower/upper limits were 17.2854/0.5856. Thus the near-perfect
development result concealed missed STOPs in the broader training corpus. No
bias was changed, and the development-derived interval was not used to fit it.
This is failure of a scalar correction, not of the whole readout or architecture.

Next use the same unresolved source checkpoints in a paired 512-versus-1024
training-window rescue. Each round scans the same 64 independently generated
byte/condition cases, one verified long-message bank (181–240 cyclically), 16
verified mid-frame cold cases, 16 known-idle cases and eight malformed/recovery
cases. Add 512 high-idle ticks to generated short cases so both window sizes fit;
this is ordinary input, not a reset. Mine the model's own training pulse errors,
retain half hard windows and half random anchors, and optimize exactly 32,768
sample ticks per round: 64 windows at 512 or 32 at 1024. All gradients in a round
are evaluated at the same parameters/causal states and averaged before one Adam
step, removing the earlier within-round stale-state approximation. Recompute
trajectories every round, reset Adam initially, use 0.0003, preserve the fast-ring
mask and train the event objective only. Budget 120 rounds, evaluate every five,
save all windows/optimizer states/exposure; retain already passing sources at zero.

This paired recipe diagnostic tests credit assignment beyond 512 while holding
optimized ticks, corpus, optimizer steps and source weights fixed. It does not
change inference hardware or the qualification thresholds. Improvement from
both windows would implicate coverage/optimization; a reproducible longer-window
advantage would motivate deeper context-credit analysis. Lack of progress still
requires structural follow-up, not an architectural impossibility claim.

### Replicate the mixed/control physical comparison

The first two mixed-memory N seeds reach 99.96% and 95.53% exact development
recovery, versus 0.48% and 92.71% in their otherwise identical fixed-leak controls.
Neither is qualified; the second paired gain is below the meaningful threshold.
This is enough to prioritize replication, not enough to announce a topology
result. Add seeds 71/101/131 to both candidates with exactly the same native-v3
120-epoch budget, all UART profiles and subsequent lower-rate rescue rule. The
original three-seed work remains separate; no seed is replaced or hidden.

## Remove local recurrence while preserving both physical rings and return routes

Register a single new connectivity ablation: `zrr_registered_24-16-24`, with the
same one-port/four-source routing, both2 return edges, all-state readout, leaks
and input access as the existing `srr` baseline. Delete only the first layer's
96 local recurrent edges. The first layer still receives both rings' delayed
states, so this is not a memoryless network or a post-fit zeroing test. All
unchanged edges retain their identities and initialization. Retrain independently
with native-v3, seeds 11/29/47, both UART profiles and 120 epochs; apply the same
lower-rate continuation if unresolved.

Hypothesis: local sparse feedback competes with ring phase/context and contributes
to persistent wrong trajectories. Support is more reliable exact frame recovery
and fewer recovery/boundary errors after retraining. Failure would indicate that
this local feedback carries useful context or that the training recipe remains
inadequate; inspect phase/context traces before allocating width. The graph costs
744 MACs/814 parameters versus 840/910. Its 11.43%/10.55% savings alone do not meet
the predeclared >=15% cost threshold. A meaningful claim therefore still needs
the >=20-point replicated unresolved-condition gain, or a later separately
controlled reduction. Full qualification requirements do not change.

### Reduced clocked first-block results and continuation

All three reduced candidates reached six-seed exact SPI0/2/3 development recovery.
The mixed and 56-state candidates also pass SPI1 in all six; the plain 48-state
control has one seed with one false boundary. I2C short-high-duty transfers remain
at 14/32 exact messages in two or three seeds per candidate, despite correct
boundaries and sub-0.002 event loss. Other I2C conditions pass. Causal event windows
are retained before any continuation in `diagnostics/reduced_i2c_duty_traces.json`.
All these I2C curves remain training-limited under the declared rule. Continue
all three I2C candidates from 30 to 60 matched epochs and retain the initial block;
this is fitting the unresolved duty behavior, not a change in the waveform or gate.

### Additional causal findings from the recorded traces

The reduced I2C failures are extra BIT0 events at the first SCL falling edge
five ticks after START, before any data-sampling rise. The reference correctly
ignores that falling edge. START/STOP boundaries are correct; the spurious
leading bit corrupts complete transaction assembly. This is why
sub-0.002 average event loss did not establish message recovery. Continuing the
same plain 48-state graph to 60 epochs resolves the observed development failures
without adding memory, changing the waveform or altering the pulse interface.
The other two 60-epoch continuations remain separately recorded.

A weight-range diagnostic on the strongest developed E configurations shows
that the E131 core and readout are well inside the existing ±7.99 bounds (max
absolute values 5.56 and 4.88). Its residual failure is not explained by active
weight clipping. The complete per-seed values and checkpoint hashes are retained
in `diagnostics/weight_ranges_v3.json`; no range or hardware cost was changed.

## Transfer robust timing into unresolved parity configurations

All six base-graph N configurations now pass the corrected broad development
suite under the explicitly recorded same-seed portfolio; E still has four passing
seeds. Test the reverse of the earlier E→N transfer: initialize only unresolved
E71/E131 from their own successful N configuration, then learn separate E weights.
The hypothesis is that robust phase acquisition is reusable while learning the
extra parity-bit interval. This changes neither the physical graph nor deployed
interface and never copies another seed's weights. Already passing E11/29/47/101
are retained unchanged and receive no extra optimization.

Use 60 epochs at 0.0003, reset Adam, event objective only, the unchanged fixed
fast-ring mask and full verified startup/timing/error coverage. Use newly generated
verified long banks 241–300 (same declared training family; no confirmation reuse).
Warm-start E evaluation and every checkpoint are preserved. This is an adaptive
training/transfer diagnostic, not a matched topology advance. Improvement would
support a training/initialization explanation; failure directs more effort to
conditional-context architectures. Full fresh-confirmation and six-seed gates
remain unchanged; N development success is not treated as E success.

### Recheck boundary separability after the full-corpus window rescue

The late E131 window-rescue training errors have changed from groups of shifted
or missing events to isolated one-event errors per selected context. Therefore,
after each complete 120-round rescue, repeat the same training-only scalar
calibration on its final checkpoint, independently for windows 512 and 1024 and
both unresolved E seeds. Use the final checkpoint as declared now, not a checkpoint
chosen after seeing a feasible offset. Preserve the uncalibrated final proposal,
calibrated proposal, training constraints and full development replay. Global
selection may still retain the older model. This specifically tests whether
training made the boundary readout separable; it does not reuse a development-
derived offset or relax a gate. An empty interval remains a recorded failure.

## Reduce input wiring while keeping the reservoir graph unchanged

Register an input-routing comparison at 24→16→24, with both2 returns, registered
execution, the same internal graph, timescales and all-state readout. The dense
baseline routes all nine agreed features to every first-layer node (216 edges).
Two new shapes route each first-layer node only its assigned lane's level, signed
edge and capped age: eight nodes per lane, 72 input edges total. All nine features
and preprocessing remain available through the fixed mask; no decoder or new
feature is introduced. Compare round-robin lane assignment against contiguous
8-node lane banks as an equal-edge control. The four ring-inlet parents remain
nodes 0/6/12/18: all lane 0 in round-robin, and lanes 0/0/1/2 in the bank layout.
That routing consequence is explicit and is part of the physical comparison.

Hypothesis: fewer current-input mixtures reduce interference while recurrent
mixing and the shared readout still combine timing and data. Main risk: delayed
cross-lane mixing could lose tight-setup information or narrow UART context.
Both shapes retain 64 nodes and cost 696 MACs/766 parameters versus 840/910:
17.14%/15.82% reductions, with preprocessing and state storage unchanged. A cost
advance still needs within-one-point recovery at >=95% on every claimed valid
condition, no worse boundaries/rejection, >=5/6 replication and fresh frozen
confirmation. Failure directs examination of lost joint lane information before
restoring input density. No loss-only ranking counts as an advance.

Use the matched native-v3 120-epoch UART recipe with initial seeds 11/29/47 and
both profiles, followed by the same lower-rate rescue rule. All common edge
weights/biases/readout initialize identically to the dense baseline; no variance
rescaling is silently introduced. The two sparse input layouts have equal edge
counts. This is a wiring experiment, not a claim that reducing preprocessing
itself is free.

## Auxiliary progress-label alias in parity UART

The original off-chip timing targets at UART-E frame ages 151 (parity sample)
and 167 (STOP sample) are both [4,2,4]: fine phase, coarse phase and clamped
48-tick progress are identical. This is not proof of a hidden-state collision,
but it leaves the important final-interval distinction to the main event loss.
N's STOP at age151 has no following parity interval and its current targets do
not have this specific ambiguity.

Register a paired training-only comparison on the same unresolved E71/E131
base checkpoints from `phase_margin_calibration_v3`. Keep the two phase targets
unchanged. Control: original progress bins 0/48/96/144. Alternative: E progress
bins 0/48/96/160, so the final STOP interval is distinct from parity. Both arms
reset the third auxiliary projection to the same seeded draw and reset Adam;
both use the same existing three six-class auxiliary heads, coefficient 0.25,
60 epochs, rate 0.0001, fixed fast-ring mask and verified long banks 241–300 plus
both startup/recovery modes. N targets would be identical under both choices.
The deployed receiver remains unchanged; no auxiliary head, parser, frame
counter or label enters runtime. All source weights and actual exposure match.

Support is better complete messages/boundaries under the alternative, followed
by fresh qualification, not merely auxiliary accuracy. If both fail or regress,
retain that recipe result and continue the structural search. This comparison
cannot itself establish a topology-dependent advance. No classification target
or timing tolerance in development/confirmation changes.

## Reallocate sixteen nonlinear units to current-sample readout

The paired auxiliary-label change did not fix E71/E131. A scalar STOP-offset
calibration is infeasible on training, and longer windows did not eliminate the
remaining false boundary. These observations motivate a readout-capacity test;
they do not prove that the existing states are linearly inseparable.

Use the existing plain 16/16/16, port_firstlast4, both2 backbone and append sixteen
nonrecurrent tanh readout nodes. They see current backbone values and have no
feedback edges. The six affine logits see both backbone and hidden readout nodes.
This is 48 recurrent states plus16 readout units, 64 nonlinear units in total,
with two sequential nonlinear stages per tick. The software buffer's sixteen old
readout values have exactly zero influence; no new timing state is introduced.
Compare dense 48-input hidden nodes against fixed eight-input nodes (two first,
four fast-ring and two slow-ring inputs spaced uniformly per hidden node).
The plain48 backbone is the no-hidden control; primary64 is the equal-unit
reallocation reference. Common backbone weights/readout initialize identically,
new output columns initialize zero, and new hidden weights are seeded.

Hypothesis: nonlinear combinations of fast phase and slow context can suppress
spurious boundaries without extending recurrent memory. Dense costs 1464 MACs /
1534 parameters; sparse costs824/894, versus plain48 600/654 and primary64 840/910.
Any dense gain therefore has an explicit wiring cost. Original >=20pp replicated
unresolved-message or >=15% MAC/parameter criteria remain unchanged; neither
isolated seed success nor lower event loss is a structural result. Full-suite
qualification may establish a useful shape even where near-ceiling improvements
do not cross that advance threshold.

Start matched native-v3 120 epochs, seeds11/29/47, both UART profiles, followed by
the declared 60-epoch lower-rate rescue for unresolved fits. Same exposure,
features, auxiliary recipe and event interface as the existing native controls.
If dense helps but sparse does not, inspect mixing/routing dependence before
spending more on recurrence. If neither helps, keep the failure and distinguish
optimization from insufficient state information using causal state probes.

The completed uniform/stop-interval auxiliary comparison selected its unchanged
starting checkpoint in all four jobs. Final E131 exact recovery was 0.99783 with
25 boundary errors (uniform), 0.99566 with55 (stop-interval); E71 was0.98568/53
and0.99002/31 respectively. Thus the label-alias diagnostic did not resolve the
behavior. Every trajectory and proposal is retained; neither recipe is promoted.

The no-local-recurrence native120 screen retained substantial failures in all
three seeds, both UART profiles. Lower-rate continuation is now running under
the same rule as other native candidates. This supports retaining local feedback
in the next designs under this recipe, without declaring the pruned graph
incapable of learning. The mixed/control E47 and extra N71/101/131 continuations
are also running; isolated development passes remain unconfirmed.

## Release protected circulation after learning the surrounding receiver

Earlier high-rate trainable-ring trajectories were unstable, motivating fixed
fast-ring gains during acquisition. This does not establish that fixing those
31 parameters remains helpful near convergence. Before measuring the new pair,
register a late-release test on the same primary E71/E131 sources used by the
auxiliary comparison: 60 epochs, 0.00001, event loss only, reset Adam, verified
long241–300 and both startup/recovery modes. The control keeps the16 middle-ring
weights and15 undriven biases fixed; the alternative makes them trainable. All
other trainable weights, data and exposure match. There is no physical topology,
feature, pulse-interface or qualification change.

Support would be fewer exact-message/boundary failures with the released ring,
followed by fresh qualification. Regression would support retaining protected
circulation under this recipe, not a conclusion that trainable rings cannot work.
This is a near-convergence recipe diagnostic, not the claimed topology result;
most current workers remain allocated to structural comparisons.

Mixed/control E29 lower-rate60 ended with the mixed model still improving
(selected at60, 67.66% exact), whereas the control retained its near-zero source.
Extend both lower-rate histories to120 under the same recipe, consuming verified
long241–300. This continuation preserves epochs0–60 and the block60 records;
results at matched120 exposure must be reported separately. It is explicitly
training-limited at this stage, not a mixed-cell capacity verdict.

## Repeat fixed-state readout fitting on the corrected corpus

The previous full affine margin trial used the startup-invalid v1 corpus and
cannot answer the fixed-state readout question. Run a replacement in a new
phase_hard_margin_v4 folder for unresolved primary E71/E131, starting from the
same strong verified checkpoints. Fit only the existing six affine outputs;
all state transitions are fixed. Twenty rounds each scan one verified long
bank241–260,16 mid-frame cold cases,16 known-idle cases and4 recovery streams.
Thus every startup/recovery file is visited; selected worst-margin training
states accumulate up to100,000. Each round runs bounded L-BFGS-B for at most150
iterations on squared margin0.5 plus1e-6 distance to the initial readout.

State always runs through the ambiguous prefix, but that explicitly unscored
prefix supplies no readout-loss constraints. This matches the existing scoring
scope without adding an inference flag/reset. Bounds remain±7.99. Development
is evaluated by the actual scalar receiver every two rounds and used only for
checkpoint selection. Save all parameters, support examples, solver status and
curves. A useful correction supports a readout-training explanation and still
requires fresh confirmation. Solver failure or residual errors are not proof of
linear inseparability, especially because canonical per-tick class fitting is
stronger than merely correct pulse onsets. This adds no physical hardware.

## Predeclare the next full-profile freeze

At hard-margin round2 (and again4), primary E131 passes every corrected broad
message/boundary/rejection development check with the same recurrent state
transition. E71 has not improved. Preserve the declared20-round budget and select
by the unchanged development key. The seed131 correction supports a readout
training explanation for that residual error, without implying fresh success.

After the block completes, use final_portfolio.py to select each seed's own
best completed checkpoint on the same primary graph: verified-v2 development
only for UART; existing complete clocked development for I2C/SPI. It records all
alternatives and hashes before freezing. Require at least5/6 whole-development
passes for every profile before generating the reserved family331000000. This
selection is a documented adaptive training program, not a matched topology
ranking. Freeze all seven profiles together, then use confirm_v2 with float,
Q3.12 and seed11 no-recurrence replays. The fresh results, including any failures,
will remain immutable and will not become training examples.

## Bring the previously promising single-return graph onto verified coverage

The earlier 24/16/24 both1 graph has four N seeds and one E seed passing the
older extended development suite, with several other E seeds near completion.
It has not yet received corrected v2 startup training. Revisit this existing
structural candidate instead of discarding those learned configurations or
inventing another arbitrary shape. It differs from primary both2 by one versus
two returns from each ring to each first-layer node:48 fewer return edges,
792 MACs/862 parameters, same64 units. That5.7%/5.3% saving alone does not meet
the15% meaningful-cost threshold; full qualification would still be useful.

Give every seed/profile the same60-epoch phase_precision_v2 recipe used earlier
for primary both2, from its own phase_recovery_readout selected checkpoint.
All nine features, ring masks, pulse interface and corrected training/development
cases match. Then apply the same completion-directed coverage/readout refinement
rules as needed. Do not compare older and corrected distributions as equal
scores, or count this adaptive portfolio as a matched native-v3 ranking. Support
is replicated complete-suite recovery with fewer return wires; failure directs
attention to whether those missing phase/context mixtures matter in causal
traces. No qualification gate changes and no confirmation sample enters fitting.

Primary finalist full_shape_v2a is frozen from final_portfolio_v2a before family
331000000 was generated. Development preflight: N6/E5/I2C6/SPI0 6/SPI1 5/SPI2 6/
SPI3 6 out of6. Its all-profile float/Q3.12/seed11-no-recurrence confirmation is
running. No qualification is claimed before every required result completes.

The new affine readout fit selected E131 round6: all2304 development groups exact,
zero boundary/invalid/background errors. Its entire state transition and leaks
are bitwise unchanged; maximum readout coefficient4.879 remains below the bound.
The old false STOP after a framing INVALID is corrected in the stored causal
window (diagnostics/verified_readout_correction_e131.json). This is direct evidence
that this particular residual error did not require new reservoir memory.
E71's margin fit did not pass; all its failed proposals remain available.

Mixed E29 reaches82.16% exact after matched lower-rate120 (plain control remains
near zero), so training remains informative. Generate verified long banks301–420
from the existing disjoint training family. Continue this pair to lower-rate240
when generation completes, with identical exposure, preserving block120 and all
earlier checkpoints. This is targeted continuation of an improving shape and
control; no test data or qualification condition changes.

## Fresh timing failures direct readout isolation and stronger development

Full_shape_v2a has failed UART qualification: float N3/6, E1/6. Most failed
conditions miss only1–3 of1000 messages, often with correct bytes but boundaries
one tick early/late; E11 has extra STOP pulses in gaps, and E131 has a short
falseSTART/alignment cascade. E71 also emits STOP16ticks after framing INVALID.
No reference-payload defect remains in this snapshot. Preserve it as a failed
confirmation and do not use its examples for training or checkpoint selection.

The development corpus's256 groups per timing did not reveal these rare errors.
Add independent development family361000000,1000 groups each for jitter,
minus_jitter,plus_jitter,gaps in both UART profiles, with1024-byte/random/all-byte/
constant-pattern coverage. Keep every existing precision_v2 case and gate as
well. This is extra development, not fresh evidence and not a narrowed test
suite. Its payload contract is asserted against the independent parser.

Next readout isolation: fit only the STOP affine row, keeping the other five
logits and all state transitions fixed, using verified training banks/startup
cases and a margin against the strongest unchanged competing logit. This tests
whether boundary calibration can improve without changing START/bit decisions
as the full affine fit did. It adds no inference hardware. Use the enlarged
independent development suite for selection, then a new untouched confirmation
family. Implement and verify this optimizer before launch; it is not yet a
result. A failed fixed-state optimizer remains a recipe failure, not proof of
inseparability or insufficient memory.

For the frozen candidate, supplemental feedforward_control removes both local
recurrence and backward return edges while retaining forward routes, leak carry
and common age features. The original no_recurrence intervention removed only
local recurrence. Neither intervention is a retrained small architecture or a
fully memoryless baseline. Their exact zero masks and frozen inference source
are recorded separately; original weights and confirmations remain unchanged.

STOP-only fitting is now implemented with an explicit32-round budget for all
six seeds and both UART profiles. Sources are the recorded phase_margin_calibration_v3
same-seed checkpoints; thus the full-affine margin fit is not silently used as
a different source for E131. Retain any source passing the enlarged development
suite with zero new training. Otherwise each round scans verified long301–332,
16 midframe cold,16 known-idle and4 recovery streams. Keep100,000 worst-margin
training states; max150 bounded L-BFGS iterations, margin0.5 and1e-6 prior penalty.
Only65 STOP-row parameters may change. Both state transitions and five other
outputs are asserted bitwise unchanged. Develop every4rounds on original cases
plus all four new independent corner files; preserve the existing selection key.
Fixed causal states may be cached as float64 for speed, but selected decisions
must agree with actual scalar inference on the entire enlarged development set.
This is a training diagnostic with no hardware addition, not a topology win.

Pre-margin E131 replay on the failed fresh minus_jitter condition also recovers
999/1000 messages with11 boundary errors (refit:999/1000 with10). Thus the full
affine refit did not create the underlying alignment failure. That causal
control is diagnostic only and cannot be substituted into the frozen selection.

New frozen-failure state probes are filed in fresh_context_interventions_v2a.json.
For E131's alignment cascade, replacing all stored state512ticks earlier with
zero reduces54 pulse errors to1 over the fixed surrounding window; replacing
only the fast ring at512 or1024ticks reduces54 to12. Several other interventions
still create errors. For N131's one-tick START shift, none of the tested256/512/
1024/2048-tick layer replacements reduces the window's errors. This distinguishes
an older-context contribution to the E cascade from the tested N boundary issue.
No reset is added to inference and none of these partial-window corrections
counts as complete-message or qualification evidence.

The mixed E29/control pair completed lower-rate240. Mixed selects the final240
checkpoint at93.793% exact recovery and929 boundary errors; the plain control
retains its near-zero source. The last block still improves exact recovery, so
this is training-limited. More continuation remains justified; it is not a
capacity verdict. Verified banks currently end at420, exactly the consumed
180+240 schedule, so extension must first generate fresh training banks.

## Compare unsmoothed rings with commensurate and coprime lengths

The E131 failure depends on state hundreds of ticks earlier; STOP-only readout
fits have not resolved difficult N seeds on enlarged development. Register a
structural alternative to the smoothed slow-context ring. Compare64 total nodes:
24 sparse /16 ring /24 ring against25 sparse /16 ring /23 ring. Both rings have
leak1, one actual closed directed cycle, direct four-source inlets from the first
layer (port_firstlast4), and two registered returns per ring into every first
node. All links into rings remain registered; all-node readout is unchanged.
The new25/16/23 graph costs856 MACs/926 parameters versus840/910 for24/16/24.
Extra input/return/sparse wiring from the moved node is explicit.

Hypothesis: two distinct circulation lengths provide a less ambiguous joint
phase representation than an unsmoothed16/24 pair, reducing dependence on a
smoothed amplitude envelope for frame progress. In the ideal undriven shift
case,16/24 repeats after48 ticks whereas16/23 repeats after368; the real tanh,
input-driven trained network is not asserted to be an ideal shift register.
This is a generic learned graph, not a programmed protocol counter or pulse
schedule. A periodic code alone cannot detect boundaries; the first layer must
learn acquisition, context and reset through its ordinary learned connections.

Both arms receive identical native-v3 data/curriculum,120 epochs,512 windows,
three initial seeds11/29/47 and both UART profiles. Initialize all ring weights
+1.05 and freeze both rings' recurrent gains and undriven biases during this
first acquisition block; driven inlets and all other weights remain trainable.
That new recipe is named phase_dual_ring_v4 and is paired across the two masks.
The existing smoothed/native portfolios are contextual references, not an
isolated matched comparison to this changed recipe. Preserve the original
>=20pp replicated recovery / >=15% cost thresholds, and full fresh qualification.
At near-ceiling accuracy a full-suite pass is qualification progress, not a
20pp structural advance. If circulation still drifts or inherited context
persists, inspect inlet forcing and conditional retention before adding more
nodes or claiming a capacity limit. Continue unresolved improving fits under
a declared lower-rate rule; do not call120 epochs a capacity verdict.

Verified training banks421–540 are now available. The still-improving mixed E29
and its plain control continue to lower-rate360, consuming those banks under
the unchanged180-epoch offset. Old block60/120/240 artifacts remain unchanged.
This is not an additional shape or arbitrary hyperparameter sweep.

Both sparse-input layouts have completed native120 in all three initial seeds
and both UART profiles. The contiguous-lane banks include a full E11 development
pass; both layouts retain seed-dependent failures. Apply the same lower-rate60
rule to the bank layout, as already applied to round-robin. No sparse-input
shape yet has six-seed/fresh qualification, and the17.14% MAC/15.82% parameter
saving does not constitute a result without replicated recovery.

## Teach an actual circulating marker through a fixed off-chip projection

The existing auxiliary heads are learned decoders from all states. They can
report phase while leaving the physical ring's code weak or mixed with context.
Test a more direct acquisition recipe on the existing primary64 graph, paired
against its completed native-v3 baseline under identical data/budget/seeds.
Replace only the first training head with a fixed binary classifier of the driven
fast-ring node: logits−20h/20h, other four classes biased−20. Its target is positive
at one tick after an observable start edge and every16 ticks while the offline
UART label parser is active, negative otherwise. Positive examples receive
weight8, negative1. The existing0.25 auxiliary coefficient, other two learned
coarse/progress heads, event loss and physical ring gains/masks are unchanged.

These are OFF-CHIP teaching labels, exactly like the prior phase labels. No
parser, counter, phase signal, fixed auxiliary projection or target reaches
runtime. The actual loop still consists of16 directed tanh nodes and its learned
inlet connections; the fast ring's gains remain+1.05 and undriven biases zero.
The one-tick teacher offset acknowledges registered first-layer-to-ring routing.
Targets are causal; cold state and continuous inference semantics are unchanged.
The fixed projection is never optimized or counted as receiver hardware.

Run phase_inlet_v4 from scratch for120 epochs, initial seeds11/29/47, bothUARTs,
using exactly the native-v3 corpus schedule,512windows,0.003 and unchanged
checkpoint selector. Hypothesis: making the loop's code explicit during training
improves phase acquisition or precise boundaries without adding hardware.
Support needs exact-message/boundary improvements, then expanded development
and independent fresh qualification. It cannot by itself establish a topology
advance. Failure suggests inlet forcing/control or the requested marker code
is poorly matched to this graph; do not infer a capacity bound. Gradient flow
uses the already tested affine-head kernel; test target timing/causality and
verify the fixed projection/middle ring after fitting starts.

## Audit startup coverage before calling a readout fit complete

Full_shape_v2a weights fail existing training starts: N71 one case, N131 two,
E47/E101 one each, E71 fifty. N101/E11/E131 pass these320 cases. Per-case traces
are retained; a separate corrected-count file fixes an aggregation bug that
summed integer boundary counts instead of Boolean failing cases. These are
training misses, not hypothetical failures or new confirmation data.

Add independent development families371000000 (256 known-idle cases/profile)
and372000000 (64 independently started error/recovery cases/profile), with the
same construction as the existing training families341/342 million. Preserve
all original precision_v2 and corner_v4 development: total8864 valid groups per
profile. Assert every declared payload against the independent parser. Do not
fit these new development cases or any confirmation examples.

Run phase_startup_margin_v5 from each seed's own frozen full_shape_v2a weights.
Keep the complete state transition fixed and fit all six affine outputs with
the existing margin0.5/prior1e-6 objective. Scan long333–364 plus16 midframe,
16 idle and4 recovery training cases per round;32 rounds cover every startup
training case twice. Retain100000 worst-margin states, bound weights±7.99,
max150 L-BFGS iterations/round, evaluate enlarged development every4rounds.
Skip a model only when both the entire320-case startup TRAINING audit and the
enlarged DEVELOPMENT suite pass. Select by the unchanged development key;
report complete training startup results separately for the final selection.

This tests whether earlier output fits missed known training corners. Success
requires all complete messages/boundaries/rejection gates on independent data;
a failed finite fit is not a proof that the state is insufficient. No physical
cost change or topology-dependent gain is claimed. If training and development
remain inconsistent, investigate state learning/inlet control rather than tune
against confirmation traces. Keep float and quantized claims separate.

STOP-only v4 also exposed an empty-support objective bug (NaN reported after
all retained training margins exceeded the threshold). Preserve every original
v4 checkpoint/log, including those NaNs. Future objectives explicitly return
the finite prior penalty for empty support, with a regression test. Old results
remain failed diagnostics and are not silently rerun or replaced.

## Put conditional retention where feedback first arrives

The frozen E131 intervention implicates older state, and two unsmoothed
protected rings have poor acquisition in the first completed native seeds.
Test conditional retention in the first layer, where both ring returns enter,
rather than only in the slow last layer. Pair registered16/16/16 plain states
with the same graph plus16 first-layer sigmoid gates. Both begin with leaks
0.5/1/0.125; each gate initially0.5, giving exactly the same starting function
as its plain control. Gates read four fast-ring quarters, one slow-ring inlet
and their own first-layer prior state, all registered. No additional input,
counter, protocol rule or reset. Both physical rings remain simple closed rings.

Plain:48 tanh states,600MACs/654parameters. Gated:48states+16sigmoids,
64nonlinear units,696MACs/766parameters. The extra96gate connections are real
hardware and must be reported. This is not an edge-matched cost win. The prior
mixed-last study used first-layer leak1 and is contextual, not a matched arm.

Run native-v3 from scratch120epochs, initial seeds11/29/47, both UART profiles,
the same data/windows/optimizer and protected fast ring. Then apply the same
conditional lower-rate60 continuation as every other native pair. Support would
be fewer context-dependent alignment/boundary failures; if recurrence still
interferes, inspect gate traces and coupling before adding further structures.
Keep the preregistered>=20pp replicated exact-message / >=15% cost thresholds;
full qualification still needs six seeds and fresh data. Improving fits may
receive declared continuation; a120epoch plateau is not a capacity proof.

The dual-ring and fixed-inlet acquisition recipes receive their promised
lower-rate60 rule through explicit phase_dual_refine_v4/phase_inlet_refine_v4
recipes. Both use their own best native120 checkpoint, reset Adam,0.0001,
auxiliary heads off and the same long181–240 plus startup schedule. Dual-ring
continuation explicitly preserves BOTH protected ring masks; inlet continuation
preserves the fast ring. First-stage checkpoints are retained. Initial dual-ring
and inlet results are weak acquisition results under these recipes, not evidence
that the physical graph cannot represent UART.

Dense nonlinear-readout continuation now has complete development passes for
N11/N29 and E11/E29; seed47 remains unresolved in each profile. Expand this
promising graph to the remaining original seeds71/101/131 under the identical
native120 then conditional lower-rate60 rule. The48-state plain control already
has all six seeds under that rule. This is a costlier architecture (1464MACs,
1534parameters,48stored states+16 current-sample hidden readout units), not a
resource saving. Do not infer six-seed qualification from the initial passes;
all new candidates must also undergo enlarged startup development and fresh
confirmation after freezing.

## Separate first-frame classification from long-memory failure

N47 traces on existing training idle007/066 and independent development idle170
first disagree at tick168: the correct STOP is classified BIT1 while preceding
sampling ticks are correct. The later cascade is not itself proof of missing
long memory. See diagnostics/n47_startup_failure_origins.json. E47 also has a
first-frame training failure. Test a matched startup-focused continuation for
these two profile/seed pairs (N47 and E47), starting from their own frozen
full_shape_v2a weights; no confirmation examples are fitted.

Compare fixed state (only six affine outputs updated) against trainable state
(retain the existing protected fast ring). Both arms use every320 existing
known-idle/error training file's first512ticks plus32 uniformly selected512-tick
anchors from one verified continuous long training file per round. All anchors
start at the model's own causal state, recomputed with the same weights used
for that round's gradient. Prefixes start from zero only because they are actual
independent cold files. There are no message resets or state labels in inference.

Use64 rounds, one coherent averaged Adam update/round at0.0003, identical
180224 optimized ticks/round, same class weights, long365–428, no auxiliary
heads. Evaluate all8864 development groups every8rounds; preserve every round
and select with the existing key. Record complete320-case training audits
before and after. This diagnoses which parameters need learning; it is not a
topology win. Improvement must include independent complete messages/boundaries;
if both arms fail, inspect state separability and context conditioning rather
than declare a capacity limit. No early skip based on the smaller old suite.

Mixed-last E29 reached96.094% exact development recovery at selected refinement
round345, versus93.793% at the earlier240-round block. The final60 rounds still
fluctuate around94–96%, with hundreds of boundary errors; it is not converged
or qualified. Extend this model and its existing matched plain control from
360 to600 lower-rate rounds under the unchanged recipe/offset180. Generate
verified long training banks541–780 first; keep every old checkpoint/block.
This allocation addresses one unresolved profile, not already-passing models.

Frozen startup-idle probes add0/16/64/256/1024 observable high ticks before
selected existing cold training files. Recompute generic ages and independent
labels and verify the original event suffix is unchanged. These diagnostic
prefixes test initial-state sensitivity; they never replace required cold-start
conditions or introduce a runtime reset/initialization allowance.

The frozen idle probe fixes all seven N47 training failures and N71's tested
cold failure with just16 additional high ticks; E47/E101's tested failures
persist through1024 added ticks. The startup core/readout pair then reaches
8864/8864 development messages and zero boundaries for N47 with state learning
at rounds16/24/32; the matched readout-only arm retains nine failed messages.
These are development and causal diagnostics, not independent qualification.

## Strengthen the next frozen confirmation against the observed startup gap

Before the next finalist is frozen, declare that its confirmation retains every
v2 gate/file and adds64 independent known-idle and64 independent mid-frame
startup/recovery cases per UART profile, eight valid messages each. Mid-frame
recovery retains the verified256-high synchronization opportunity; known-idle
cases retain their ordinary17–48 tick leading idle. Generate all new cases only
after freezing weights, with disjoint seed families recorded in that snapshot.

Also replay the corrected prior full_shape_v2a corpus with the newly frozen
weights as a separately reported regression suite. It is observed data and
must never be called fresh. No sample from it may enter training, support
selection or checkpoint selection. Require >=5/6 seeds per profile to pass both
the new fresh suite and that regression suite before calling a full shape
qualified. This additional check prevents a known failing configuration from
being accepted merely because another random draw happens to pass. It tightens
the checks; no original criterion is relaxed. No new confirmation data has
been generated and no next fresh seed family is yet selected.

## Cover sustained corner traffic as well as interleaved timing

The training-only long365–396 audit finds rare errors for N71/N101/N131 and
E11/E101, but none for E131 in those32 streams. Existing long files include one
1024-byte corner message, error/recovery traffic and then interleaved timing
conditions. Fresh confirmation also exercises1000 consecutive messages under
one timing condition. Test this possible distribution gap without borrowing any
confirmation example: add four independently seeded1000-message training banks
for each jitter/minus_jitter/plus_jitter/gaps condition and UART profile.
Use family381000000 (N) /382000000 (E), bank/condition offsets recorded per file.
Keep all earlier mixed, long, cold and error corpora. Every new valid payload
must pass the independent parser audit. These are TRAINING files only.

Hypothesis: persistent corner traffic exposes state/history failures that sparse
interleaving misses. Audit frozen source configurations first. If errors appear,
refine using only this training evidence plus earlier coverage/anchors and
evaluate on the unchanged8864-group development suite. If not, investigate the
specific state mechanism rather than assume that larger random data alone fixes
it. This coverage work changes no architecture or qualification criterion.

## Close a fixed training constraint set before judging the output fit

Register phase_closure_v6 before fitting. Wait for completed startup-margin-v5
and cold-prefix-v5 blocks, then freeze the best same-seed/profile checkpoint on
the common8864-message development distribution. No confirmation score selects
it. Preserve the complete state transition. Training pool: all16 stationary-v6
corner files, verified long365–396, all320 startup-mode files and256 verified
mid-frame training files. Revisit this entire finite pool every round instead
of introducing a different partial corpus after each solve.

Use eight full scans, retaining every newly encountered state whose canonical
multiclass margin is below0.75. Deduplicate by file/tick and never discard an
older constraint. Fit all six existing affine outputs with margin0.5 and the
same1e-6 prior penalty, at most500 bounded L-BFGS iterations per scan. Bound each
coefficient to within0.25 of its frozen starting value, intersected with±7.99;
this limits the disruptive steps observed in v5. Stop early only after a full
scan has zero canonical classification errors AND the enlarged development
suite passes. Keep pulse/message audits distinct from that stricter training
classification diagnostic. Limit retained support to two million states; if
exceeded, save the unresolved block and change the fitting approach, not the
architectural conclusion.

Evaluate development after each solve and verify the selected cached-state
result against full scalar inference. Record scanned ticks, support count and
solver iterations separately; these are not native-training epochs. This is
an output-training/coverage diagnostic, not a topology-dependent advance.
The corpus is finite: a successful fit still requires independently frozen
fresh confirmation and the separately reported prior regression suite.

For this new v6 block, verify the actual best-development readout on the entire
fixed training pool after the last solve. If jointly training-verified and
development-passing checkpoints exist, apply the same development key among
those eligible checkpoints. Otherwise retain the best development diagnostic
and mark its training failures explicitly. This rule is declared before v6
dispatch; it prevents reporting closure for a last iterate while returning an
older selected checkpoint that still misses known training cases.

The final startup-margin-v5 job (E131) failed while writing its initial
checkpoint: its source was an earlier margin-fit checkpoint that already had
support arrays, and duplicate keyword arguments were passed to NumPy. No E131
optimization step had run. The other11 model blocks completed and remain
unchanged. `startup_margin_v5_32_repair1` records old/new source hashes and
resumes only E131 after merging checkpoint fields into a single dictionary.
The original failure log and source snapshot are retained. Apply the same
serialization correction to v6 before it is dispatched. This is a software
repair, not an architectural result or an execution limit.

Dense nonlinear readout now has five of six no-parity development passes under
the declared native120/lower-rate rule (N47 remains below the gate). Audit its
selected completed weights on the enlarged8864-group development set before
any freeze. Train its I2C/SPI profiles with the same exposure as the existing
plain48 control:60 matched epochs for I2C/SPI1,30 for SPI0/2/3, all six original
seeds. Initial common-backbone function is identical to the plain control;
the16 extra current-sample readout units and their wiring are fully costed.
The remaining parity seeds are still running; none of this is qualification.

For dense-readout configurations that fail enlarged development despite an
original-suite pass, re-audit the first and last original-suite-passing saved
checkpoint in each completed native120/refine60 history. Deduplicate existing
selected checkpoints; skip configurations already passing the enlarged suite
and histories with no full original pass. Freeze this small candidate list
before scoring it. Apply the unchanged key on the common8864-group development
set and retain every alternative result. This tests selection coverage without
new training and without evaluating confirmation data. It is not evidence that
a different topology improved, and it cannot replace fresh qualification.

### Eight gates versus eight slow states, registered before native-v6 dispatch

The new whole-training audit exposes genuine event-pulse and recovery cascades
in long or independently started streams that earlier development missed. Test
whether conditional updates of the sparse layer can control feedback entering
the fast ring, while keeping that ring itself ungated. Three arms use the
primary24/16/24 graph as their parent: primary64; a56-state control retaining
nodes0 through55 and closing the shortened slow ring with55→40; and that exact
56-state control plus eight sigmoid gates at sparse nodes0,3,6,9,12,15,18,21.
Every retained proposal/input/return edge is identical to the parent; outgoing
edges of removed states disappear. Each gate reads four fast-ring quarters,
the slow-ring inlet and its own previous state. All gate inputs are registered.
This is a change in physical graph and cell type, not a runtime timing counter.

All three use first-layer leak0.95, fast-ring leak1, slow leak0.125. Initial
gates equal0.95, giving the small ungated/gated pair identical initial functions.
Counts measured before training are respectively64/56/64 nonlinear units,
840/768/816 MACs,910/830/886 parameters, and64/56/56 stored states. Eight gates
are fully counted as eight nonlinear units. These differences alone do not
meet the15% cost threshold. Sigmoid uses the shared tanh table; its fixed
arithmetic, state, leak slots and storage subtotals remain in the specifications.

Native-v6 trains all three from scratch, initially seeds11,29,47 on both UART
profiles, with the same120 epochs,512-tick windows, Adam0.003, three off-chip
teaching projections and protected16-node fast-ring edges/undriven biases.
Use the same5 clean +5 pattern curriculum. Thereafter every fourth epoch uses
one whole sustained-corner training file from family381/382million, cycling
bank-major over jitter, minus_jitter, plus_jitter and gaps, four banks each.
Other epochs use the corresponding verified precision-v2 long bank. Every
post-curriculum epoch also includes four mid-frame cold, four known-idle cold
and two error/recovery training streams. Reset only between independent files;
never crop or reset within the sustained file. All8864 enlarged development
groups select checkpoints at epoch0 and each fifth epoch. Preserve every epoch.

Support would be fewer recovery cascades in the gated64 arm than both primary64
and its exact ungated56 control, replicated under six seeds and fresh data.
The meaningful-result threshold stays >=20 percentage points of exact recovery
on an unresolved condition in >=5/6 paired seeds, without >2point regression;
or the previously declared >=15% cost saving with comparable qualifying recovery.
Near-ceiling corrections are useful qualification work, not this topology claim.
If both shortened graphs worsen, investigate lost slow-state memory/return
coverage before blaming gates. If gates lose during acquisition but continue
improving, give the matched pair a declared lower-rate continuation. If gates
help only one seed, inspect gate saturation and circulation disruption before
extending a hypothesis. No plateau will establish a representational limit.

For closure-v6's small retained failing constraint sets (N131,E47,E71), solve
an explicit linear program maximizing the minimum correct-class margin, first
within the same ±0.25 readout trust region and then within the full ±7.99 weight
range. This is a diagnostic of the current frozen state representation and
canonical training labels only. Check returned margins independently. A positive
margin would show that the squared-margin training objective's residual errors
are avoidable on these retained states; it would justify a different output-fit
recipe with a complete-pool recheck. A nonpositive optimum does not prove the
physical graph incapable: it concerns one learned state configuration, finite
precision solver tolerances and stricter canonical labels than pulse acceptance.
No LP result is a qualification score, and no development/confirmation state
is supplied as a fitting constraint.

All three full-range LP diagnostics found positive verified margins on retained
training states (N131:1.2696;E47:7.4011;E71:0.02384); every ±0.25 trust-region
optimum was negative. Follow up with linear-closure-v7: minimize the L1 change
from each completed v6 selected output layer, subject to margin0.01 on every
retained training state and absolute weight bound7.99. Scan the same624-file
training pool, retain every newly encountered margin<0.02 state, never evict,
and solve again. Up to16 scans,100000 retained-state budget,300seconds/LP;
stop on full training closure, infeasibility, solver limit or support budget.
These are recipe/solver limits, not physical representational conclusions.
The previous state cache is read-only, hashes checked; every new checkpoint and
constraint set is separate. Re-evaluate all8864 development groups and scalar
replay; select a jointly whole-training-verified/development-passing checkpoint
if any, otherwise preserve the unresolved best development diagnostic. This
tests the observed weight-change restriction with no additional hardware.

The dense nonlinear-readout shape still fails enlarged N47/E47 after its matched
native120/lower-rate60 training. Repeat the declared cold-prefix diagnostic on
those two configurations: existing affine outputs only versus all trainable
state/hidden-readout/output weights, same512-tick prefixes,32 continuous anchors,
64 coherent updates at0.0003, and identical starting checkpoint within each pair.
Protect the same16-node fast ring. This targeted transfer of the diagnostic
tests whether cold-state adaptation helps the second physical shape. Report
failure/negative transfer as well as improvements, with unchanged8864-group
development and whole320-case training audits. It is a training-parameter
comparison, not itself a new topology claim or fresh confirmation.

Linear-closure-v7 corrected every retained N131/E47 label in its first fit but
collapsed ordinary development traffic. During the next full scan it collected
millions of redundant violating states before checking its100000-state budget.
Stop that diagnostic, preserve the two completed iteration1 checkpoints and
original source/jobs, and record the collector's memory-limit bug separately.
It is not an execution limit on this research and does not stop the shape runs.

Linear-closure-v8 keeps the same frozen state/source, margin0.01, minimum-L1
objective and full624-file scans. Replace bulk collection with one worst-margin
state per true class per file (at most3744 new states/scan), retaining every
previously chosen state. Enforce a20000-state solver budget during collection,
not after allocation. A complete zero-error scan is still required; unselected
errors remain counted and are not accepted. Use bounded numeric sparse-matrix
construction instead of millions of Python objects, one worker, at most16scans
and300seconds/LP. Stop on infeasibility, time/support budget, or verified training
closure, and retain scalar development and selected-training audits. This is
a computationally bounded separation-oracle diagnostic, not relaxed acceptance.

First-layer-gated64 passes all three initial N seeds after120+60, but E29/E47
still acquire poorly. Before treating that as a parity-memory limitation, test
same-seed N→E initialization against the identical ungated48 control on those
two unresolved seeds. Each starts from its own best completed native/refine N
checkpoint, resets Adam, and trains separate E weights for60 epochs at0.0003
with no auxiliary loss; fast-ring protection is preserved. Both use long
epochs429–488, substituting whole sustained corners every fourth data epoch,
plus the same four midcold/four idle/two recovery pieces. All8864 development
groups select checkpoints. This isolates learned timing acquisition as a
training factor; different starting-function quality is reported, not hidden.
Improvement alone is not a topology claim. Existing E11 and failed native E
trials remain untouched, and six-seed/fresh replication is still required.

The N131 bounded-collector run becomes infeasible at margin0.01 after6653
retained training states include ordinary traffic. Before drawing conclusions,
maximize the actual achievable margin over that complete retained set under
the same7.99 weight bound. Independently verify primal margins and a numerical
dual residual bound, and inspect the nearest opposite-label state pair. An
optimum below0.01 explains this recipe's infeasibility; near-zero margin may
indicate indistinguishable/linearly inseparable learned states but remains a
finite floating-point diagnostic, not a proof that the physical topology cannot
learn different states. Do not substitute these probes for message qualification.

Native-v6 shows large high-rate fluctuations while the matched120-epoch blocks
are still underway. Predeclare the same lower-rate rule for every eight-gate
comparison arm: retain a completed source that already passes every enlarged
development gate; otherwise start from its own selected native120 checkpoint,
reset Adam and train60 additional epochs at0.0001 without auxiliary loss.
Keep the protected fast-ring mask, continuous state,512window and full-corner
schedule; use data epochs111–170 and all original startup pieces. Preserve all
native iterates, including collapse. Dispatch only after a source completes,
in separately snapshotted waves to use available workers; waves do not change
the training rule or candidate set. Compare fixed native budgets separately
from conditional continuation, and require six-seed fresh evidence before
any topology claim. This is informative continuation, not a plateau verdict.

The N131 numerical bound is approximately1.3e-10 maximum margin, with66 active
weighted constraints between NONE and BIT1. Nineteen constrained NONE states
occur one tick after a correct BIT1. The interface emits only a class's onset,
so strict canonical NONE labels may impose unnecessary constraints. Test one
and two additional ticks of held BIT0/BIT1 labels on the same6653 training
states. Assert that pulse extraction of each modified complete source stream
equals every original event exactly; do not hold START/STOP/INVALID and do not
modify any waveform, runtime interface, development target, or acceptance gate.
Re-solve the finite-state margin diagnostic. Positive margin would justify a
full-pool training-label comparison, not qualify a shape or establish a new
topology. Other constrained NONE states occur far from the last bit, so do not
assume this label change resolves the learned-state limitation.

Both one- and two-extra-tick bit holds make the finite N131 state set separable
with verified margin0.01076776; the original strict labels had essentially zero
margin. Choose the smaller one-tick change for a full-pool diagnostic. This
demonstrates that the earlier canonical-label limitation was not by itself an
event-interface representational limitation. Keep all original waveform/event
acceptance rules. Bit-hold-closure-v9 uses the same fixed neural state and v8
6653 retained states, with training labels recomputed and pulse equivalence
asserted per complete source file. Use minimum-L1 output change, margin0.001
(below the finite-set maximum), mining below0.002, the same bounded collector,
20k support budget,16 scans and300seconds/solve. Zero held-class errors over
the complete pool and unchanged scalar development are reported separately.
No held-class transform is applied at inference or scoring. Quantized replay
remains separate; small float margins do not imply quantized robustness.

Expanded first-layer-gate audit: N11/29/47 all pass8864 groups/boundaries;
the matched ungated48 control passes N29, while N11 misses400groups and N47
misses11. Same-seed N→E training gives expanded passes for gated E29/E47 and
ungated E29; ungated E47 still misses16groups. Gated E11's earlier native weights
miss one enlarged-development group and two boundaries. Extend that same paired
N→E60 recipe to seed11. No fresh evidence has yet been evaluated for these shapes.

Replicate the first-layer-gate/control N comparison on remaining seeds71/101/131
with the identical native-v3 first120 recipe used for initial seeds, followed
by its declared lower-rate60 rule and expanded development audit. Then apply
the identical N→E60 recipe on all remaining seeds. Keep every source and exposure
explicit; don't combine the native-v3 and eight-gate native-v6 comparisons into
one matched table. Train I2C/SPI for both masks with the previously used common
clocked budgets:60 epochs for I2C/SPI1,30 for SPI0/2/3, all six original seeds.
This extends a promising pilot to full-profile replication; the48-versus64
nonlinear-unit difference is explicit. Costs600/654 versus696/766 remain visible,
and any topology claim still needs the preregistered meaningful threshold and
independent frozen confirmation. The cheaper control is not silently dropped.

The dense nonlinear-readout candidate remains a second promising physical shape:
expanded N11/29/71/101 and E11/29/71 pass, while the paired N47/E47 cold-prefix
block completes without a full repair. Apply the already documented32-round
fixed-state startup-margin recipe to unresolved N131,E101,E131,N47,E47, starting
from each seed's best completed expanded-development checkpoint. Preserve all
48 recurrent-state and16 nonlinear-readout-unit parameters; train only its six
existing affine output rows. Use the same training corpus, support cap, bounds,
objective, scalar replay and whole320-case startup audits as primary-v5. This
tests whether output fitting can repair the remaining errors without another
hardware change. The successful seeds receive no unnecessary extra training.


### Conditional gates versus learned constant leaks — v6a
Before evaluation, freeze the five completed passing first-gated configurations
N11/29/47 and E29/47. Remove every gate-input connection, retain its learned bias,
and convert that constant sigmoid to an ordinary per-node leak in the exact
plain48 graph. Verify bitwise equivalence of the clamped and converted networks
on a deterministic random sequence, then replay all8864 development groups.
No refit, waveform change, reset, runtime filter or qualification relaxation.
If every gate can be removed without errors, pursue the same existing plain48
mask with nonuniform learned leaks as a lower-cost configuration. If recovery
breaks, the current weights use conditional gates; it does not prove that the
ungated mask cannot learn. This ablation alone is not a fresh topology result.

### Balanced cold-start coverage — v10, preregistered before scoring

Dense-readout parity seed101's completed margin-v6 block passes its320 existing
startup training cases but misses one first-byte STOP on expanded development.
Test coverage before another structural conclusion:32 allowed initial high-idle
lengths17–48 ×7 unchanged UART timing conditions ×all256 first bytes =57,344
freshly generated training cases. Families391million/392million, one independent
phase/jitter seed per combination; no development waveform is copied. The offline
builder and independent parser must agree on every complete payload. Cold neural
state and generic feature ages match deployment. No new runtime operation.

Freeze that seed's completed dense-margin source first. Hold every learned state
and nonlinear-readout parameter fixed; retain its24 existing training support
states. Up to8 rounds mine all new grid states with margin<0.75, retain them
without eviction (100,000 cap checked during collection), and fit the existing
six affine outputs with the prior margin0.5 objective, trust±0.25 and absolute
±7.99. Re-evaluate all8864 development groups each round; independently replay
selected weights through the scalar kernel, the320 startup training files and
the complete grid, including event-pulse and boundary mismatch counts. Preserve
all checkpoints, generator/data/state hashes, failed iterates and selection.

New grid failures support a coverage gap for this learned configuration. Repair
without original-suite regression supports further training; inability to fit
these fixed states motivates state changes, not a topology impossibility claim.
A plateau alone does not reject the shape. This recipe diagnostic cannot meet a
topology-improvement threshold; any structural claim still requires the unchanged
matched-seed practical threshold and frozen fresh confirmation. Successful
profiles receive no additional training merely to reduce loss.

### Paired saved-checkpoint audit — first-gate v10

After completed native120 and the declared lower-rate rule, expanded development
leaves gatedN71/N131 and plainN11/N47/N71 unresolved. Before further training,
apply the same bounded saved-checkpoint rule to both graphs: first and last
original-suite-passing checkpoint from each completed native/refine history,
deduplicated by actual parameter/leak bytes. Freeze all candidate hashes before
expanded scoring, retain the original source among selection options, and keep
all failed alternatives. A graph with no such alternatives receives none; do
not invent replacement seeds or run an unbounded checkpoint sweep. This is
ordinary development selection, not independent evidence or a topology claim.

### Full independent training-pool gate-state audit — v11

First-gate confirmation v3a exposed rare UART-E combined minus/jitter failures
in float seeds101/131. Preserve that confirmation; do not fit, mine or select
weights on its waveforms. Both source configurations remain exactly the original
development-selected checkpoints frozen before v3a. Audit/refine these two
unresolved configurations on the existing independent624-file training pool:
16 whole sustained-corner files,32 long streams,320 startup/error streams and256
midframe streams. All pool hashes are verified. No successful profile receives
extra optimization merely to lower loss.

A new mixed-cell trajectory kernel exposes the existing gated states for fitting
and is tested bitwise against both the independent scalar trace and original
inference, including first/last/eight-gate layouts with changing gate values.
Inference equations and all48 states/16 gates remain unchanged. Fit only the
existing six affine output rows with margin0.5, prior regularization1e-6,
trust±0.25 and absolute±7.99. Each full scan adds at most one worst state per
true class per file (3744maximum), retains every unique constraint, and checks a
100,000-state limit during collection. Up to16 scans,500solver iterations each.
Stop when full training has zero canonical errors, minimum margin>=0.1 and all
8864 development groups pass. Keep all failed iterates; a fixed-state plateau
is not a topology impossibility result. Scalar development replay, full selected
training audit and320 startup-training audit follow checkpoint selection.

A repair supports a fitting/coverage explanation for these learned states. If
training evidence remains unresolved, change state training or the structural
hypothesis instead of declaring the graph impossible. Any revised finalist
must be frozen before a new independent confirmation; v3a becomes regression
evidence and can never be relabeled fresh. The practical topology threshold and
full five-of-six-per-profile qualification remain unchanged.

## Gated fixed-state constrained-fit follow-up — v12

The v11 parity-seed131 training scan retains two actual STOP errors after several
rounds. On141 retained states, a numerical max-margin linear program finds the
±0.25 trust interval infeasible for even zero margin; the full declared±7.99
parameter range separates that finite set. This is a restriction of that fit,
not evidence that the topology is incapable. Both solver residuals and concrete
classifier margins are recorded; this is not a formal proof.

Try a minimum-L1-change affine fit from the same frozen development-selected
source, requiring margin0.01 on all retained constraints and allowing the full
existing parameter range. Initialize constraints from immutable v11 epoch7;
retain all subsequent unique per-file/class worst states, with the same100,000
cap. Reuse state caches only after validating their fixed-state/pool identity.
Up to16 full independent training-pool scans; stop only with zero canonical
training errors, margin>=0.0099 and full expanded development pass. All48 states,
16 gates, proposal/gate parameters, leaks and physical routes stay fixed. If the
finite constraint program is infeasible, preserve its result and proceed to
state training; do not call a topology failure. No confirmation samples are used
for fitting or selection. Meaningful architectural and six-seed qualification
thresholds remain unchanged; any new candidate needs a new freeze and fresh
confirmation plus both prior regression suites.

## Balanced invalid/recovery coverage — v13

The wider v12 fit reaches zero canonical errors on the624-file training pool,
while three false STOP boundaries remain in two independent development error
streams. Add a balanced independent training set: all256 invalid bytes ×three
error types ×seven valid-recovery timings, shuffled with seed401000000 into672
continuous streams of eight invalid/valid pairs. Each recovery payload is four
fresh random bytes; a4096-tick idle follows the fourth pair. Waveform families
begin402000000 and do not overlap earlier training or confirmation. Independent
parser equality and exact coverage counts are checked. Break stimuli ignore the
invalid-byte value, so their repeated values provide varied preceding histories,
not distinct break levels.

Retain the original624 training files and the fixed-state constrained fit,
starting with immutable v12 epoch5's retained training constraints. Reuse only
verified immutable state arrays, with a new pool identity. Fit the existing six
affine rows using minimum L1 change, margin0.01 and absolute bound7.99. Maximum16
scans, retain all unique worst-per-class/file constraints, enforce100,000 cap.
Require both full1296-file training closure and all8864 development groups with
zero boundary/rejection failures before considering a revised finalist. This
adds coverage, not hardware or a new topology result. Freeze before fresh testing
and retain both known failed confirmation suites as regression. No qualification
threshold changes; a plateau is not a representation proof.

## Gated finalist B selection and fresh confirmation

If v13 finishes with verified full1296-file training closure and all8864
independent development groups/boundaries/rejection gates, use its selected
parity-seed131 checkpoint. Retain every other development-selected source from
finalist A. This favors a jointly training-verified/development-passing fit over
an earlier lower-loss checkpoint that demonstrably fails independent training;
it does not select on either confirmation suite. Keep all six seeds, including
the still-unresolved parity101 and any failed clocked configurations.

Freeze graph, equations, all42weights, source and resource definitions before
fresh family521000000. Evaluate all previous v3 conditions and counts. Require
the same five seeds per profile to pass the new fresh suite AND both entire old
suites(full_shape_v2a andfirst_gate_full_v3a), with float/Q3.12 separate. Known
failed confirmation A is regression only. Topology count remains one unless the
second distinct physical definition actually passes the unchanged float gates.

Before inspecting revised B confirmation results, apply the same v13 constrained
recipe and1296-file independent training pool to parity-seed101, whose v11 fit
retained1667 source training errors. Initialize its retained constraints from
completed v11 epoch16. This is a separate batch with identical physical graph
and fitting rules, targeting unresolved behavior; frozen finalist B remains
unchanged. Any later use requires development/training qualification and another
fresh freeze. It cannot retroactively alter B.

## Structural readout-routing reduction — v14

Fresh gated confirmation B again misses parity reliability, including a previously
passing seed. Preserve the full result and its causal traces. The qualified dense
nonlinear-readout graph suggests a different structural test: keep all48 backbone
states and16 current-sample nonlinear output units, but reduce each unit's incoming
state edges from48 to32. Each reads all16 first-layer states and alternating eight
states from each16-node ring, with parity offset equal to its readout-node index.
The union still reads every ring node, and the original six outputs still see all64
node values. The graph has256 fewer physical edges, not zeroed weight slots.

This hypothesis is that the dense nonlinear decision surface is useful while some
ring-state access is redundant. Expected cost is1208 MACs and1278 parameters versus
1464/1534: reductions17.49%/16.69%, with the same48 stored states,64 nonlinear units,
two-stage schedule, generic features and causal interface. Success still requires
fresh paired recovery within1 percentage point per condition(at least95%), no worse
boundary/rejection outcomes, and >=15% lower MACs/parameters with seed replication.
Full qualification separately retains all exact messages/boundaries and>=5/6 per
profile. No leak-only or zero-weight variant is counted as a second shape.

First screen three paired seeds11/29/47 on UART-N/E using each seed's frozen dense
configuration, including its failed seed47. Fit a fixed32-input affine projection
of each source nonlinear unit's preactivation on independent training states. Use
the same training-state covariance for an intact48-input control; preserve the
backbone and activation equations; fit the existing hidden affine weights/biases, while retaining the six output rows and interfaces. The matched
control has an exactly feasible source solution. This is off-chip teacher fitting
on training only, not a from-scratch comparison or receiver-side teacher. Record
teacher residuals, parameter changes, exposure, exact development messages and
boundaries. Poor recovery will motivate supervised fitting of the existing nonlinear
readout weights, not a claim that pruning is impossible. Any finalist gets all six
seeds/all profiles and a new frozen independent confirmation.

## Preserve every fast-ring readout input at the same edge budget — v15

The v14 first-layer-complete32-parent pilot does not preserve UART-N recovery
in three seeds after projection. A training-only covariance diagnostic compares
three interpretable32-parent layouts: retain all first-layer nodes, all fast-ring
nodes, or both entire rings. Keeping the full fast ring reduces mean teacher
preactivation residual in all three seeds; removing first-layer access entirely
is worse. This selects the next routing hypothesis, not a meaningful result.

Test all16 fast-ring parents plus alternating eight first-layer and eight slow-
ring parents per nonlinear output, offset by output-node parity. Keep64 nonlinear
units,48 stored states,1208 MACs/1278 parameters and the same schedule/interfaces.
Reuse the identical verified training covariance and source weights from v14;
perform the same bounded affine projection. Compare exact development recovery,
not residual alone. Practical and qualification thresholds are unchanged. If
projection is insufficient, allow supervised training of the existing nonlinear
readout/affine output weights on independent training states before rejecting it.

## Supervised nonlinear readout fitting on fixed states — v16

The fast-ring-complete32-parent projection recovers the whole no-parity development
suite for seed11; seeds29/47 remain unresolved. Extend that exact graph to the
remaining three seeds and all profiles, while testing supervised head fitting on
the pilot. Keep all48 recurrent states, backbone weights/leaks and every physical
edge fixed. Optimize only the existing16 hidden readout affine transforms and six
output rows. No decoder or extra runtime state is introduced.

For each seed/profile, gather one shared independent training-state bank for the
intact control and pruned candidate. Per file and true class, include16 uniform
samples and16 lowest-margin source samples, with deduplicated file/tick identities;
the source is the frozen dense same-seed model. These training-only choices include
all existing timing/cold/error distributions, plus balanced error coverage for8E1.
Both shapes get the identical bank and a maximum eight blocks of80L-BFGS iterations,
class-balanced squared margin0.5, prior regularization1e-6 and bound±7.99. Retain
passing fits when both the entire8864-group development suite and sampled training
labels pass; report their smaller optimization exposure explicitly. Every block
is retained, and only complete development recovery/boundaries/rejection select
checkpoints. Source loss or bank accuracy alone cannot qualify the shape.

Finite-difference checks cover hidden inputs/biases and final output weights/biases;
forward computation and extracted frozen backbone are checked against the causal
scalar receiver. Final development evaluation always uses that receiver. A sampled
bank is not a full training-pool closure or a fresh confirmation. If still improving,
continue the promising fit rather than label the graph inadequate. Practical
cost/recovery and six-seed qualification thresholds remain unchanged.

## Clocked-profile projection of the same reduced-readout graph — v17

Apply the fixed fast-ring-complete32-parent layout to I2C and all SPI modes with
all six original seeds. The physical graph,48-state/64-unit budget and interface
are exactly the UART candidate's; only weights differ. Use the same intact dense
same-seed source and bounded projection as v15. Both source/control and candidate
see each tick of the same14 original corrected-coverage training corpora, including
tight data setup. Report original clocked development separately from enlarged
UART development; neither is qualification. Any failed clocked fit must receive
explicit further training. The unchanged whole-profile fresh confirmation and
cost/recovery thresholds govern success.

## Matched conditional supervised head fitting for clocked profiles — v18

The same fast-ring-complete reduced layout passes original development for six
SPI0 seeds, five seeds in each other SPI mode, and three I2C seeds after projection.
Give both intact and reduced graphs the same conditional supervised-head recipe
as v16 on shared per-seed banks from the14 corrected clocked training corpora.
Keep passing whole-development/zero-bank-error sources unchanged, and allow each
unresolved fit the same eight80-iteration blocks. Optimize no recurrent weight,
leak, gate or interface. Report adaptive exposure rather than claiming identical
additional iteration counts. Fresh confirmation remains mandatory and unchanged.

## Restore balanced first-byte coverage after head fitting — v19

The reduced readout now has five whole-development no-parity passes and four
parity passes. Parity101 has one cold-start STOP error after fitting; its intact
control also loses a cold-start boundary when optimized on the sampled bank.
The bank did not include the previously effective balanced startup grid. Reapply
that independent57,344-case grid(32idles ×7timings ×256bytes) to both completed
v16 same-seed selections, retaining the original bank as a simultaneous audit.
This is a declared training-coverage correction, not a physical-shape change.

Keep all recurrent and nonlinear hidden weights fixed; fit only the six existing
affine output rows, margin0.5/prior1e-6, trust±0.25 and absolute±7.99, at most eight
rounds. Mine one lowest-margin state per true class per grid case and per training
bank file/class; retain every discovered constraint, capped at500,000 before
allocation. Each round scans the complete grid and bank. Stop only with zero
canonical grid/bank errors and full8864development pass; independently replay
selected grid pulses/boundaries, source-bank labels and scalar development.
Preserve source selections and failed iterates. New fresh confirmation remains
required; no confirmation examples or qualification criteria change.

## Continuous pause coverage after reduced-head confirmation A — v20

Fresh readout_cost_full_v3a has a real reduced-graph failure: SPI1 seeds47/101
miss complete messages during pauses (997/1000 and998/1000, latter two boundary
errors), and SPI2 seed47 has988/1000. UART-N/E each reach5/6; other profiles
currently pass. Keep A frozen and finish its regressions. No confirmation
waveform or state enters fitting. The next freeze must regress A as well.

Hypothesis: the representative clocked head bank missed rare continuous pause
contexts. Test this on the same fixed dense/reduced states with independently
generated training family411000000 and development family413000000. For SPI1/2,
add32 continuous128-message pause streams plus8 mixed64-message streams to the
14 original corrected corpora; development adds8 independent128-message pause
streams to the original suite. Keep all six original seeds and both graphs.
Mine the complete training pool each round, retaining up to256 lowest-margin
states per file/class under margin0.75, deduplicated, capped at250,000 states.
Fit only the existing six affine outputs with squared margin0.5/prior1e-6,
trust±0.5 and absolute±7.99, up to12 rounds/500L-BFGS iterations. All earlier
constraints remain. Stop a fit when the whole expanded development and complete
training-label scan pass; record actual conditional exposure. Prefer a full
training-closure checkpoint among whole-development passes, preserving all
other iterates and the original checkpoint. This extra readiness criterion
strengthens coverage and does not relax any qualification gate.

Supporting observation: independent pause data reproduces the failure and
existing-output fitting closes it without recurrent/head changes. If sampled
states remain inseparable or new development fails, expand head fitting or
change routing; do not label the whole shape incapable from a bounded fit.
Keep the original meaningful>=15% cost / comparable recovery criterion, all
other gates, and a newly frozen independent confirmation.
