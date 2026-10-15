# Eight gates versus eight slow states

This targeted comparison holds the original24-node sparse layer,16-node fast ring, input routing and event interface fixed. It compares a24-node slow ring, a16-node slow ring, and that same reduced backbone with eight conditional first-layer gates. The retained-parent construction preserves all surviving edges and closes the shortened slow ring. Each gate reads the fast-ring quarters, slow inlet and its own prior state. Gate indices are0,3,6,9,12,15,18,21.

All three use the same independent native-v6 training schedule,120 epochs,512-tick windows and seeds11,29,47 for each UART profile. The declared continuation retains an expanded-development pass or gives an unresolved fit60 lower-rate epochs from its own best checkpoint. This is a three-seed diagnostic; it cannot satisfy the six-seed qualification requirement.

| Shape | Units / states | MACs/sample | Parameters |
| --- | ---: | ---: | ---: |
| 64 states | 64 / 64 | 840 | 910 |
| 56 states | 56 / 56 | 768 | 830 |
| 56 states + 8 gates | 64 / 56 | 816 | 886 |

## Matched native120

| Shape | Profile / seed | Completed | Selected exact messages | Boundary errors | Full development pass |
| --- | --- | ---: | ---: | ---: | --- |
| 64 states | uart_n/11 | 120 | 7440/8864 | 4176 | no |
| 64 states | uart_n/29 | 120 | 3252/8864 | 40023 | no |
| 64 states | uart_n/47 | 120 | 8780/8864 | 172 | no |
| 64 states | uart_e/11 | 120 | 6682/8864 | 20717 | no |
| 64 states | uart_e/29 | 120 | 8781/8864 | 569 | no |
| 64 states | uart_e/47 | 120 | 4114/8864 | 31064 | no |
| 56 states | uart_n/11 | 120 | 8727/8864 | 2931 | no |
| 56 states | uart_n/29 | 120 | 8861/8864 | 6 | no |
| 56 states | uart_n/47 | 120 | 8846/8864 | 15 | no |
| 56 states | uart_e/11 | 120 | 3622/8864 | 38165 | no |
| 56 states | uart_e/29 | 120 | 2874/8864 | 68669 | no |
| 56 states | uart_e/47 | 120 | 117/8864 | 309337 | no |
| 56 states + 8 gates | uart_n/11 | 120 | 8167/8864 | 9371 | no |
| 56 states + 8 gates | uart_n/29 | 120 | 8246/8864 | 4892 | no |
| 56 states + 8 gates | uart_n/47 | 120 | 8775/8864 | 1417 | no |
| 56 states + 8 gates | uart_e/11 | 120 | 2231/8864 | 120689 | no |
| 56 states + 8 gates | uart_e/29 | 120 | 7367/8864 | 23927 | no |
| 56 states + 8 gates | uart_e/47 | 120 | 4002/8864 | 46369 | no |

![Training curves](runs/connectivity01/figures/phase_native_v6_allocation_curves.png)

## Declared lower-rate continuation

| Shape | Profile / seed | Completed | Selected exact messages | Boundary errors | Full development pass |
| --- | --- | ---: | ---: | ---: | --- |
| 64 states | uart_n/11 | 60 | 8680/8864 | 1591 | no |
| 64 states | uart_n/29 | 60 | 8797/8864 | 182 | no |
| 64 states | uart_n/47 | 60 | 8864/8864 | 3 | no |
| 64 states | uart_e/11 | 60 | 8755/8864 | 228 | no |
| 64 states | uart_e/29 | 60 | 8854/8864 | 42 | no |
| 64 states | uart_e/47 | 60 | 8864/8864 | 60 | no |
| 56 states | uart_n/11 | 60 | 8834/8864 | 625 | no |
| 56 states | uart_n/29 | 60 | 8864/8864 | 0 | yes |
| 56 states | uart_n/47 | 60 | 8857/8864 | 559 | no |
| 56 states | uart_e/11 | 60 | 8535/8864 | 3289 | no |
| 56 states | uart_e/29 | 60 | 7413/8864 | 9836 | no |
| 56 states | uart_e/47 | 60 | 148/8864 | 325287 | no |
| 56 states + 8 gates | uart_n/11 | 60 | 8863/8864 | 44 | no |
| 56 states + 8 gates | uart_n/29 | 60 | 8777/8864 | 1862 | no |
| 56 states + 8 gates | uart_n/47 | 60 | 8856/8864 | 28 | no |
| 56 states + 8 gates | uart_e/11 | 60 | 8150/8864 | 3534 | no |
| 56 states + 8 gates | uart_e/29 | 60 | 8546/8864 | 4858 | no |
| 56 states + 8 gates | uart_e/47 | 60 | 7367/8864 | 19651 | no |

![Training curves](runs/connectivity01/figures/phase_native_refine_v6_allocation_curves.png)

Completed final continuations: 18/18. Whole expanded-development passes: 1/18.

The prespecified meaningful threshold remains a replicated20-percentage-point improvement on unresolved exact messages with no material regression, or comparable>=95% recovery with>=15% lower MACs and parameters. Eight sparse gates have not established that result in the completed comparisons. Extra slow states are not uniformly helpful either: the ungated56-state control has a passing no-parity fit while the64-state controls still make boundary errors. This does not establish a general ranking or prove any shape incapable.

The successful16-gate candidate uses a different16/16/16 allocation and gate coverage. Its result cannot be attributed solely to replacing eight slow states by eight gates. Native high-rate collapse, later recovery, incomplete convergence and boundary failures remain visible in these curves. Full-profile qualification is reported separately in QUALIFIED_SHAPES.md.

[All completed fit records](runs/connectivity01/gate_eight_comparison.csv); [per-condition development metrics](runs/connectivity01/gate_eight_conditions.json). Job lists, immutable source snapshots and all checkpoints remain under the original native/refinement wave labels. Numeric costs exclude unmeasured routing/area; common feature, assembly and activation-table costs are detailed in ARCHITECTURE_COMPARISON.md.
