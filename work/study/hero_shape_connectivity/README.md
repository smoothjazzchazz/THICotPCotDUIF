# Physical connectivity continuation

Start with [RESULT.md](RESULT.md) for the two confirmed shapes, diagrams, costs
and main findings. [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md) contains the exact
qualification counts and demonstration weights; [CURRENT_FINDINGS.md](CURRENT_FINDINGS.md)
retains the development ledger. [ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md) explains
the leading graphs and costs. [READOUT_ROUTING_COMPARISON.md](READOUT_ROUTING_COMPARISON.md) records the paired 256-edge reduction, training curves and coverage repair. [PAIRED_READOUT_RESULT.md](PAIRED_READOUT_RESULT.md) applies the fixed practical threshold. [GATE_ALLOCATION_COMPARISON.md](GATE_ALLOCATION_COMPARISON.md) records the completed eight-gate allocation comparison. Older development distributions remain separate.

This separate study continues `../protocol_hero_search/PLAN.md` and preserves its
qualification gates. It changes no historical trial, reference design, or gate.
The first question is whether actual directed rings improve the 24→20→20 stack
after correcting training coverage. Learned configurations are demonstration
weights, trained off chip, with one physical mask across all seven profiles.

The vendored waveform oracle, assembler, nine generic features, recurrent
equation, and scalar kernel are exact copies of the prior study at launch.
Inference sees only generic lane levels, signed edges, capped ages, and its own
continuous state. No waveform parser, teacher state, hidden bit counter, or
generator boundary enters inference. Float and integer replay stay separate.

Physical shape is distinct from a demonstration configuration. Different leak
coefficients, weight seeds, optimizer recipes or protected training masks alone
do not create a second shape: the modeled hardware retains programmable weight
and leak slots. `runs/connectivity01/physical_topologies.json` groups identical
literal connection masks/equations while retaining every configuration alias.
Different fingerprints are not by themselves a graph-nonisomorphism proof.
In particular, the48-state plain controls with first-layer leak1 or0.5 are two
configurations of one physical mask. First-layer gates, last-layer gates and
nonlinear current-sample readout are actual different hardware arrangements.

## Comparisons registered before results

First compare SSS, SRR, SSR, SRS, RSR, where S is the previous sparse graph
(self plus three other inputs per node) and R is one directed closed ring,
without trainable self edges or skips. Every layer retains the same leak
capability; leak carry is explicitly state, not a ring edge. Compare registered
and current-sample inter-layer schedules separately. Preserve all unchanged
baseline edges exactly; route randomness must not depend on recurrent choices.

| Hypothesis | Supporting observation | Failure suggests next comparison |
| --- | --- | --- |
| SRR reduces feedback interference and hardware | Better tight-setup recovery or matched recovery with fewer operations/parameters | Separate ring gain, self edges, and skip edges; inspect layer contributions |
| SSR retains sparse feature extraction with simpler long context | Better recovery than SRS at equal edges | Ring earlier, or reduce smoothing in the last layer |
| SRS simplifies the intermediate representation | Better late-data recovery than SSR | Direct input injection or current-sample routing |
| RSR gives ordered early memory and contextual middle | Better UART boundaries/repeated bits than SRR | Ring direction relative to routes, ring skips, or allocation |
| Current-sample propagation removes routing delay | Better exact boundaries than registered with identical masks | Shared early readout or input injection is sufficient; examine costs |

The first matched recipe uses 30-epoch blocks, 512-tick BPTT, seeds 11/29/47,
all seven profiles, identical per-epoch streams and exposure across candidates.
Data rotates through independently seeded corpora with every mandatory timing
condition, tight setup, patterns, malformed transfers, recovery and long idle.
Development contains each condition independently. Confirmation seeds are
disjoint and generated only after a frozen selection. Checkpoints retain Adam
state, RNG/data schedule, state/exposure, learning curves and per-condition scores.

**Meaningful improvement, fixed before evaluation:** at least +20 percentage
points exact complete-message recovery on a previously unresolved condition,
with the gain in at least five of six paired seeds and on fresh data; no >2 point
regression in another condition. Alternatively, within 1 point on every valid
condition (at least 95% on the claimed conditions), no worse rejection/boundary
counts, and at least 15% lower MAC and parameter totals. This is a scoped research
result, not full qualification. Screening at three seeds is only prioritization.
Use paired message bootstrap intervals and seed replication; do not count long
message bits as independent messages. Report every failed condition.

Qualification remains all messages and exact boundaries, no extra accepted
invalid/background traffic, >=1,000 messages per valid timing condition,
all byte values and up to 1,024 bytes, cold/midstream/idle/recovery tests,
and >=5/6 seeds for **each** UART 8N1/8E1, I2C and SPI 0–3 profile. Freeze
finalists before independent fresh confirmation. Fewer than two pass means
fewer than two qualify. A recipe plateau is never a capacity proof.

## Targeted follow-ups

Edge-matched controls replace rings by one-input random permutations or give
rings self/skip edges to match sparse fan-in. Reverse ring direction only while
holding inter-layer routes fixed (otherwise a ring relabeling is isomorphic).
Then compare inter-layer route fan-in/alignment, input to all layers, readout
access, and node allocation as evidence warrants, declaring each threshold
before evaluating. Retrained no-recurrence and post-fit ablations are distinct.
UART traces must separate missed timer-like events, bit values, boundary state,
error recovery and credit-assignment effects. A fixed generic ring is permitted;
programmed protocol-specific counters or waveforms are not.

Sources motivating the hypotheses, checked 2026-10-13:
[Gallicchio and Micheli](https://arxiv.org/abs/1909.11022) studies structured deep
reservoirs; this does not prove small protocol receivers. The sampled SPI mode
conventions follow [Analog Devices](https://www.analog.com/en/resources/analog-dialogue/articles/2018/08/13/15/31/introduction-to-spi-interface.html).
UART/I2C source registers and timing assumptions remain those in the previous
study's `PROFILES.md` and `knowledgebase/protocols/`.
