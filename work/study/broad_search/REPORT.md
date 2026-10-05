# Confirmed improvement: compact polynomial memory

**On fresh, identical streams, the new integer recognizer increased known-event
F1 from 80.9% to 90.0%, raised unknown recall from 53.0% to 94.0%, and reduced
false known events from 834 to 248 (70% fewer).** It passed the numerical rule
written before screening, on the first confirmation attempt. The comparison is
against the strongest of 30 rerun historical reservoir/readout combinations,
not just the latest delay-chain experiment.

The main improvement is a usable representation: retain 20 samples and expose
pairwise relationships between them. More training alone did not repair the
legacy reservoirs. This is a **study-only NGRC/NVAR implementation**, not an
adopted change to the 16-node hardware design. Recognition remains limited to
the studied synthetic pulse-order task.

## Confirmation evidence

[Before-search acceptance rule](PLAN.md) · [94-row experiment ledger](LEDGER.md) ·
[Frozen configurations and sources](../results/broad-confirmation/20261005T012024.954575Z/freeze.json) ·
[All metrics, seed blocks and intervals](../results/broad-confirmation/20261005T012024.954575Z/metrics.json)

Candidates, readouts, rejection thresholds and the rule were frozen before
creating 96 streams: 12 independent seed blocks × four conditions × two streams,
48 patterns each. There were 4,608 patterns, including 3,072 known events.
State continued across patterns; receivers received only causal pin samples.
Labels, the four-tick decision target, 20-tick startup exclusion, stabilizer and
six-tick event-matching rule were unchanged. Earlier inspected test data were
regarded as development evidence.

| Receiver | Event precision | Event recall | Event F1 | Unknown tick recall | False events | Median / p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **20-sample NGRC, 8-bit coefficients** | **91.6%** | **88.5%** | **90.0%** | **94.0%** | **248** | **1 / 2 ticks** |
| Same candidate, float coefficients | 91.5% | 88.3% | 89.9% | 94.0% | 251 | 1 / 2 |
| Mixed `cycle3210`, full-state linear | 76.1% | 86.4% | 80.9% | 53.0% | 834 | 2 / 3 |
| Level chain, Hamming | 75.6% | 76.9% | 76.3% | 86.5% | 762 | 2 / 2 |
| Age chain, sign-bit linear | 60.1% | 74.2% | 66.4% | 81.1% | 1,514 | 2 / 4 |
| Original selected, full-state linear | 33.4% | 92.1% | 49.0% | 0.0% | 5,644 | 2 / 3 |
| Conventional run-length reference | 93.4% | 63.2% | 75.4% | 84.3% | 137 | 2 / 2 |

The reference remains useful: it emits fewer false events and has slightly higher
precision. Beating it was not the objective. Latencies describe matched events
only; the integer candidate missed 353 known events. They include stabilization,
not a hardware pipeline, synchronization, or timing closure.

![Confirmation comparison](../results/research-report/20261005T012524.648650Z/comparison.png)

| Condition | Precision | Recall | F1 | Unknown recall | False / 1,000 ticks | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Clean | 100% | 100% | 100% | 100% | 0.00 | 1 |
| ±2-tick duration variation | 94.2% | 81.9% | 87.6% | 90.1% | 1.13 | 3 |
| 2% independent sample flips | 89.6% | 99.7% | 94.4% | 99.0% | 2.59 | 1 |
| Both perturbations | 82.2% | 72.4% | 77.0% | 87.0% | 3.48 | 3 |
| Aggregate | 91.6% | 88.5% | 90.0% | 94.0% | 1.80 | 2 |

The paired block bootstrap used 10,000 draws. The 98.333% interval for F1 gain
over the best legacy receiver is **+8.56 to +9.90 percentage points**; the best
legacy competitor is selected again within each draw. Unknown recall gain over
`cycle3210` is **+39.12 to +42.90 points**. Candidate F1 spans 87.8–91.6% across
individual seed blocks. The interval level accounts for up to three declared
confirmation attempts; only one was used. These are empirical bootstrap
intervals, not formal coverage guarantees. The selected architecture is
deterministic, so there is no favorable topology seed to choose.

The original validation requirements also pass after quantization: precision
92.2%, recall 99.0%, unknown recall 96.4%. All 20 nominal reset decisions and all
1,000 continuous-prefix target/offset decisions are correct. Initialization-tail
gaps are zero on all three inherited probes. Required cross-prefix distances
are nonzero at all four offsets, with zero nominal same-target prefix diameter.

## What works, and what did not

The audit separated five failure mechanisms:

* **History loss:** the originally selected reservoir has exact known/unknown
  collisions; the 16-state chains lose relevant earlier samples under jitter.
* **Initialization and unrelated history:** mixed leaks retain integer residuals;
  some CA and delay-feedback settings retain initial conditions. Finite input
  memory removes initial-state dependence after its buffer fills.
* **Retained but unusable information:** several candidates have nonzero
  cross-prefix distances yet fail trained decisions. More distance is not proof
  of a useful readout representation.
* **Unknown rejection:** `cycle3210` catches many known events while accepting
  about half the unknown ticks. Explicit unknown training alone does not fix it.
* **Perturbations and quantization:** narrow timing training misses wider jitter;
  coarse coefficient rounding or recurrent-state rounding can destroy behavior.

We implemented three different alternatives beyond ordinary ESN variants:
[online Boolean/CA dynamics](../boolean_ca/README.md),
[nonlinear scalar delay feedback](../delay_feedback/README.md), and
[polynomial delayed-input memory](../polynomial_memory/README.md).
We also tested [size, topology and multiple-reservoir controls](../modular_reservoirs/README.md):
8/16/32/64/128 states; sparse, ring, local, skip and directed connections;
parallel, stacked, coupled and input-specialized arrangements; three topology
seeds for the five leading arrangements; leak, nonlinearity and precision.
No multi-reservoir arrangement demonstrated a robust advantage here.

CA rules and scalar feedback failed the nominal decision requirements despite
some retained state distinctions. Those results and initialization/collision
measurements remain in the ledger. Larger sparse reservoirs were not a solution:
128 nodes reached only 67.0% original validation F1, versus 87.7% for a 32-node
ring. These bounded experiments do not rank entire research families generally.

The following ablations use development data, not confirmation data:

| Controlled change | Measured result | Interpretation |
| --- | --- | --- |
| 20-sample linear → quadratic features, same augmented training and selection policy | 63.2% → 89.9% F1 | Nonlinear interactions are the main measured gain |
| Original → broader timing training, same 20-sample quadratic model and selection policy | 86.2% → 89.0% F1 on a separate development check | Training coverage contributes; not a reservoir-only gain |
| Same augmented training/readout policy applied to legacy `cycle3210` | 78.2% F1, 67.9% unknown recall | Training/readout changes alone do not explain the new result |
| Explicit → implicit unknown training, 20-sample quadratic model | 89.9% → 90.2% F1 | Explicit unknown output is not necessary for most of this gain |
| Raw level → legacy level-minus-age input, same 20-sample quadratic model | 89.9% → 71.8% F1 | Input representation matters; the legacy feature is not automatically better |
| Float → 4 / 6 / 8-bit coefficients | 89.9% → 50.7 / 88.8 / 90.0% F1 | Four bits fail; eight bits preserve this fitted behavior |

Rows involving retraining use the same selection *policy*, not identical numeric
thresholds. The quantization comparison freezes weights before rounding and
rescales thresholds without retuning. Slight gains from rounding are not claimed
as a general advantage of quantization.

## Architecture and hardware implications

At tick `t`, store `[u(t), u(t-1), …, u(t-19)]` with signed binary samples. Compute
20 linear features plus 190 distinct pair products. Four fixed weighted sums
score known classes 0/1, background 2 and unknown 7. The saved integer score
floor is 154, margin is 26, scale is 256, and stabilization is M=2.
Only the readout is trained. No pulse parser, future sample, label, or hidden
pattern boundary is used during inference.

This fits the NGRC/NVAR convention in
[Gauthier et al.](https://www.nature.com/articles/s41467-021-25801-2).
The [critical distinction](https://www.nature.com/articles/s41467-021-27715-5)
matters: it is a nonlinear finite-memory filter, not a conventional recurrent
nonlinear reservoir. The contribution here is the task-specific implementation,
controlled experiments and evidence, not a new general RC algorithm.

The [resource accounting](../results/research-report/20261005T012524.648650Z/resources.json)
includes every development configuration and historical baseline. For the winner:

* 20 sample bits plus a conservative 20 startup-validity bits; 19 delay links.
* 190 pair operations, implementable with XNOR after startup. Pair features are
  combinational; they need not be additional persistent state.
* **844 signed 8-bit readout parameters = 6,752 bits**, including four biases.
  This dominates storage. By comparison, the historical three-prototype Hamming
  readout stores only 48 prototype bits with 96 reservoir-state bits.
* 840 coefficient contributions per tick. Binary features permit sign selection
  and addition, but this is still a large readout relative to the original model.
* The saved coefficient bound is 896 per score: 11 signed accumulator bits
  suffice for these weights; score subtraction needs another bit. This is
  arithmetic accounting, not an RTL proof or measured implementation.

Floating-point reservoir/control results are labeled separately. Python uses
wide integer containers for the quantized path; coefficient ranges, exact integer
scores, accumulator bounds and streaming behavior are checked. A fully parallel
or time-multiplexed implementation would have different area and latency costs.
There is no synthesis result, clock claim, or evidence that this readout fits
the tile budget. RTL, released specifications and gate status are unchanged.

## Remaining weaknesses

Mixed noise still misses 27.6% of known events. The 20-sample horizon also causes
exact collisions in 22 of 150 deterministic perturbed memory comparisons at one
or more decision offsets; see the
[post-selection boundary diagnostic](../results/research-report/20261005T012524.648650Z/boundary.json).
The acceptance rule requires collision-free nominal probes, not every perturbed
waveform. These failures were not hidden or used to change the frozen model.

Unknown rejection is **distribution-specific**, not an open-world guarantee.
A separately labeled, deterministic
[unseen-unknown limitation probe](../results/unseen-unknown-probe/20261005T012713.374377Z/probe.json)
used seven pulse pairs outside the confirmation family under two preceding idle
lengths. It got 83.9% unknown tick recall and emitted two false known events,
both for `(12,3)`. This was a post-selection diagnostic, not another confirmation
attempt or a source of tuning. Noise can also produce identical observations
from different intended classes, which no causal receiver can always undo.
Only the pulse-order task is confirmed; protocol coverage and generalization to
other loaded codes remain untested.

## Inspect and reproduce

[Runnable commands](README.md) · [Small reservoir implementation](../polynomial_memory/reservoir.py) ·
[Portable frozen configuration](../polynomial_memory/compact_20_q8.json) ·
[Shared readout/receiver](../shared/broad.py)

[Full confirmation traces](../results/broad-confirmation/20261005T012024.954575Z/traces.json.gz),
[inputs and labels](../results/broad-confirmation/20261005T012024.954575Z/test_streams.json.gz),
[representative trace](../results/research-report/20261005T012524.648650Z/representative_trace.json), and
[trace figure](../results/research-report/20261005T012524.648650Z/trace.png)
are saved. The plotted trace is the predetermined first mixed stream, not a
favorable example selected afterward.

All 96 candidate streams passed state/decision/event replay and JSON snapshot
restoration, including snapshots before the history buffer filled. A separate
[full replay](../results/confirmation-replay/20261005T012553.876841Z/verification.json)
reproduced all confirmation metrics exactly. Historical settings were refitted
on their original data; tiny BLAS coefficient roundoff was checked against the
original saved receivers. Their decisions/events agree, including all 96 streams
for the two strongest baselines. The
[preservation verification](../results/delivery-verification/20261005T012820.001570Z/verification.json)
checks historical source/results and every frozen source hash. Thirty study
tests and eleven model tests passed; template and whitespace checks passed.
