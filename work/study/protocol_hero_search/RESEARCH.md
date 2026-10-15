# Requirements and hypotheses, before implementation

Recorded 2026-10-12. The literature motivates comparisons, not protocol success.

| Ability | Test and failure implication |
| --- | --- |
| Preserve recent transitions | SPI mode edges and I2C SCL/SDA relationships; erased state cannot be repaired by readout fitting. |
| Time without transitions | UART 0x00/0xff and adjacent frames; insufficient training and absent memory are distinct hypotheses. |
| Retain interrupted context | Stretching, clock pauses, repeated START; a timeout is not a protocol limit. |
| Keep fast and slow information | Layers versus parallel timescales; excessive smoothing can lose timing. |
| Recover continuously | Cold/midstream starts, invalid input, long idle, then observable synchronization. |
| Preserve distinct states | State-distance and no-recurrence diagnostics, with no inference of capacity from loss alone. |

[Gallicchio et al., DeepESN survey](https://arxiv.org/abs/1712.04323) motivates
hierarchical recurrent state. [Gallicchio and Micheli, topology study](https://arxiv.org/html/1909.11022v1)
compares constrained ring, chain and permutation connectivity. Its experiments
used **500 total nodes**, not evidence for success within this experiment's 64.
[Carmichael et al.](https://arxiv.org/abs/1908.08380) motivates comparisons of
parallel and layered allocations under a fixed node budget.
[2024 timescale study](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1397915/full)
supports testing heterogeneous leaks; its benefit is task-dependent. These are
time-series studies, not demonstrations of complete UART/I2C/SPI receivers.
Sources read online on 2026-10-12; links only, no original papers retained.

Six families: flat sparse; ring with skips; two layers; three layers; parallel
fast/slow feeding a combiner; delay chain feeding a sparse reservoir. Compare
current-sample and registered inter-layer propagation for the two/three-layer and
parallel families as distinct shapes. All have 32/48/64-node versions. Three-layer
allocations are 12/10/10, 16/16/16, 24/20/20. Parallel allocations are 12/12/8,
16/16/16, 24/24/16. No family is a predetermined winner.

Masks use a topology seed independent of training seeds and profiles. Recurrent
nodes have sparse, explicitly enumerated fan-in. Readout sees all nodes. Input
goes to the first layer or both parallel branches. Tanh and per-node programmable
leaks are fixed hardware capabilities. Protocol profiles may choose weights and
leaks, but cannot change the masks or update ordering.

Train conventional fixed-reservoir/readout-only controls and fully trained sparse
recurrent networks, labeled separately. Start at 30 epochs/TBPTT 512 and continue
in blocks. Complete development messages precede boundary errors and false events
in checkpoint selection. Improving runs receive continuations; plateau requires
two non-improving blocks plus lower-rate and longer-window rescue. No discarded
trial is silently removed. Fresh confirmation is generated only after freezing.

Qualification remains the supplied plan: every mandatory profile and condition,
at least 1,000 complete messages per valid timing condition, exact messages and
boundaries, no extra accepted invalid/background messages, at least five of six
seeds. A failed early screen is not confirmation. USB/Ethernet follow qualification.
