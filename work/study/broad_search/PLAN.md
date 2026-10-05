# Broader reservoir study: audit and preregistered rule

Written before new candidate screening, 2026-10-05 UTC. Study proposals only.
Historical sources/results are hashed in `historical_hashes.json`.

## Audit

The saved fixed reservoir collapses to one sign fingerprint (74% clipping).
The selected `seed24/forward_leak0` removes collapse but has only three ticks
of effective memory: known/unknown pairs collide exactly. Mixed `cycle3210`
has the strongest saved full-state F1 (81.9–82.1%), but unknown recall is
50–52%, precision 77%, and initialization residuals fail. Its unknown (8,8)
decisions are wrong even without a prefix. The delay age chain flushes its
initialization but has only 15 past ticks, insufficient under jitter. Its
clean magnitude distinctions are unusable by the fitted readout. The level
chain's **Hamming** readout is also a strong control (79.3% F1, 85.9% unknown
recall); the latest full-state result is not the strongest baseline.

Existing inspected seeds 23, 24, 104, 105 are development evidence. No old
result is a confirmation of this study. Reuse the causal sample generator,
four-tick target labels, continuous state, 20-tick metric exclusion, unchanged
six-tick event matching, and the conventional listener from `shared/`.

## Numerical acceptance, fixed before search

Retain validation precision, recall, and unknown-tick recall >= .80; all
20 nominal reset decisions correct; >= .90 correctness in EACH continuous
target/offset group; no required full-state cross-prefix collision; initial
state tail discrepancy <= one six-bit normalized count (1/32) after the
existing 128-tick low/high/training probes; at least two distinct states.
For integer legacy models the original <=1-count rule remains unchanged.

The <=50% clipping screen applies to saturating arithmetic. Boolean states
are inherently on rails, so applying clipping to them measures the wrong
property: report bit diversity and collisions instead. NGRC delay states
are also binary samples, not arithmetic overflow. This exception is declared
before screening and does not relax recognition or initialization requirements.

On confirmation, require these conditions for the frozen implementation:

* Clean precision, recall, unknown recall >= .95; false events <= .5/1000 ticks.
* Aggregate precision, recall, unknown recall >= .80; false events <=4/1000.
* EACH jitter/glitches/mixed condition: precision >= .75, recall >= .65,
  unknown recall >= .65, false events <=6/1000 ticks.
* Matched-event p95 latency <=5 ticks in every condition; report misses too.
* Aggregate F1 >= strongest rerun legacy reservoir F1 + .03. Paired uncertainty
  interval for that F1 improvement must exclude zero. Unknown recall must
  improve over cycle3210 with an interval excluding zero, and be within .03
  of the best legacy unknown recall among legacy methods with F1 >= .75.
* Pass the original validation/probe requirements above, reload/replay, and
  focused correctness checks. Quantization is a separately evaluated variant.

Stress floors differ from clean because observation noise preserves intended
labels even when distinct intended signals become observationally identical.
These are additional requirements; the old validation limits stay unchanged.
Beating the conventional listener is not required.

## Search and hypotheses

Use small screening sets first, then more independent development streams.
No full Cartesian sweep. Every run gets immutable config, source hashes,
seeds, purpose and metrics in `results/<experiment>/<unique-run-id>/`.

1. **Polynomial memory (NGRC):** finite delays preserve first-pulse information;
   nonlinear products expose known/unknown interactions to a linear readout.
   Support: longer windows remove collisions; quadratic beats matched linear.
   Falsify: collisions persist or nonlinear expansion cannot improve rejection.
2. **Boolean/cellular automaton:** local rule evolution creates cheap nonlinear
   temporal features. Compare rules, input placement, feedforward and rings.
   Support: useful diversity, initialization forgetting, reliable decisions.
   Falsify: persistent initial bits or states with poor class separation.
3. **Nonlinear delay feedback:** a nonlinear scalar and delayed self-feedback
   provide multiple timescales without a dense network. Support: useful memory
   and better rejection at matched storage; falsify via initial-state residue,
   collisions or inferior decisions. A discrete study analogue, not a physical
   time-multiplexed implementation.
4. **Modular dynamical controls:** 8/16/32/64/128 nodes, sparse/ring/local/skip
   structures; single versus parallel, stacked, weakly coupled and specialized
   reservoirs at equal total node/storage budgets. Support must survive seed
   replication; a single favorable random topology is insufficient.
5. **Readout controls:** implicit versus explicit unknown, linear versus
   nonlinear features, same training and preprocessing. Training augmentation
   and any causal filter get matched controls and separate attribution.

## Confirmation procedure

At most THREE confirmation attempts for this study. Each must freeze candidates,
readouts, thresholds, acceptance rule and source hashes BEFORE generating its
data. Record a failed attempt permanently and return to development. No picking
successful seeds or stopping a batch early. Each attempt uses 12 independent
waveform seed blocks, four original conditions, two 48-pattern streams per
condition/block. Record every stream. Deterministic architectures need no
topology seed; stochastic finalists require three topology seeds frozen together
and all must satisfy point thresholds. Use 10,000 paired block bootstrap draws,
98.333% two-sided intervals (Bonferroni .05/3 across attempts; conjunctive
success claims). Bootstrap intervals are empirical uncertainty, not formal
coverage guarantees. Report all block results and their spread. A fresh seed
batch is generated only after development/probes qualify. Replays never count
as new evidence. If three attempts fail, preserve a checkpoint and explicitly
report that the objective has not been achieved.

## Primary research and definitional boundaries

* Gauthier et al., [NGRC](https://www.nature.com/articles/s41467-021-25801-2):
  delayed inputs and nonlinear expansion with a fitted linear readout. This
  qualifies under the NGRC convention, not as a recurrent nonlinear network.
* Yilmaz, [CA reservoirs](https://arxiv.org/abs/1410.0162): fixed cellular rules
  transform input-driven state and only a readout is fitted. Our causal online
  injection is a study variant, not a reproduction of the paper's benchmark.
* Appeltant et al., [delay feedback](https://www.nature.com/articles/ncomms1476):
  nonlinear dynamics plus delayed feedback can supply the reservoir substrate.
* [A critical perspective](https://www.nature.com/articles/s41467-021-27715-5)
  distinguishes NVAR from physical/recurrent reservoirs. A hand-coded pulse
  parser is a conventional decoder; it will not be renamed a reservoir here.

All state bits, connections, operations and readout storage are accounting
estimates, not synthesis or area evidence. No RTL/specification/gate changes.
