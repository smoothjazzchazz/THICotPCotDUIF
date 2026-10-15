# Reducing nonlinear readout connections

This comparison removes 256 actual physical edges from the dense 64-unit receiver: each of its 16 nonlinear readout units receives 32 backbone states instead of 48. The backbone, node count, state count, current-sample head, six event outputs and generic input features remain fixed. All fast-ring states remain accessible to every hidden readout unit; alternating halves of the first layer and slow ring provide the other 16 inputs.

| Graph | Recurrent / inter-layer / input / final-output edges | MACs/sample | Parameters | All modeled multiplies/sample | Numeric storage |
| --- | ---: | ---: | ---: | ---: | ---: |
| dense | 96 / 840 / 144 / 384 | 1464 | 1534 | 1560 | 11550 bytes |
| fanin32_fast | 96 / 584 / 144 / 384 | 1208 | 1278 | 1304 | 11038 bytes |

The reduction is 17.49% in MACs and 16.69% in parameters, or 16.41% including the 96 common leak-blend multiplies. Both have 48 stored states, 64 nonlinear units and activation depth 2. Storage decreases only 4.43% because the shared activation table dominates this subtotal. Routing, physical area and frequency are unmeasured; see ARCHITECTURE_COMPARISON.md for common costs and exclusions.

![Shared backbone with actual directed ring closures](runs/connectivity01/figures/readout_shared_backbone.png)

The backbone drawing omits the extra head. Its two ring branches both receive the sparse-layer ports; neither ring feeds the other. The following incidence matrices show every added backbone-to-head connection. Both graphs then connect all 64 outputs to all six event logits.

![Every backbone-to-head connection](runs/connectivity01/figures/readout_parent_masks.png)

## Controlled training and interpretation

Each same-seed pair starts from the same learned dense backbone and sees the same independent training waveforms. The first step fits each hidden preactivation on the full training covariance; the intact control exactly represents its source. This is a transfer/pruning study, not evidence of easier learning from random initialization. Failed seed 47 stays in every six-seed comparison.

Both graphs then receive the same per-seed supervised bank and conditional optimization rule: retain a whole-development pass with zero bank errors, otherwise allow eight blocks of up to 80 L-BFGS iterations. Only existing head weights/biases and six output rows change. Actual optimization exposure differs under this declared rule and is recorded in the CSV; it is not described as identical iteration counts. Projection scans every training tick, while supervised fitting uses recorded representative states.

The first 32-parent layout retained all first-layer states and half of each ring. It failed to preserve UART recovery after projection. The equal-edge alternative retaining all fast-ring states lowered training projection residual in all three pilot seeds and recovered several full development fits. Supervised head fitting then repaired the remaining required no-parity seeds and all clocked profiles. This supports the value of routing the complete fast phase representation to the nonlinear head for these weights; it is not a proof that the first layout cannot learn.

Parity seed 101 still had a cold-start boundary error. Balanced startup-grid coverage repaired the reduced graph without changing any recurrent or hidden-head weights. Its selected checkpoint passes all 57,344 grid cases with zero canonical/pulse/boundary errors, all 190,592 retained bank states, all 8,864 development groups and the 320 older startup training cases. The dense control selection also passes the grid and development, but its earlier development-selected checkpoint retains 13 canonical bank-label errors; later fits and this discrepancy remain recorded. Training-label equality is not substituted for fresh message qualification.

Seed 47 remains unsuccessful for UART in both graphs. Some supervised iterations collapse and then recover; the source checkpoint is retained when it scores better. These are unresolved training/representation cases, not demonstrated impossibility. No confirmation waveform is used for fitting or checkpoint selection.

## Completed development stages

| Stage | Graph | UART-N | UART-E | I2C | SPI0 | SPI1 | SPI2 | SPI3 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First-layer-complete projection | dense | 2/3 | 2/3 | — | — | — | — | — |
| First-layer-complete projection | fanin32 | 0/3 | 0/3 | — | — | — | — | — |
| Fast-ring-complete projection | dense | 5/6 | 5/6 | — | — | — | — | — |
| Fast-ring-complete projection | fanin32_fast | 2/6 | 3/6 | — | — | — | — | — |
| Supervised UART head fitting | dense | 5/6 | 5/6 | — | — | — | — | — |
| Supervised UART head fitting | fanin32_fast | 5/6 | 4/6 | — | — | — | — | — |
| Clocked projection | dense | — | — | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| Clocked projection | fanin32_fast | — | — | 3/6 | 6/6 | 5/6 | 5/6 | 5/6 |
| Supervised clocked head fitting | dense | — | — | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| Supervised clocked head fitting | fanin32_fast | — | — | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| Balanced startup-grid output fitting | dense | — | 1/1 | — | — | — | — | — |
| Balanced startup-grid output fitting | fanin32_fast | — | 1/1 | — | — | — | — | — |
| Expanded continuous-pause output fitting | dense | — | — | — | — | 6/6 | 6/6 | — |
| Expanded continuous-pause output fitting | fanin32_fast | — | — | — | — | 6/6 | 6/6 | — |

These are whole-development passes, including boundaries and rejection. Stage sample counts differ explicitly; only frozen six-seed confirmation can qualify a graph.

![All supervised UART evaluations](runs/connectivity01/figures/readout_head_v16_curves.png)

## Fresh confirmation

The unchanged practical threshold was declared before evaluation: within 1 percentage point per condition with at least 95% recovery, no worse boundaries/rejection, and at least 15% fewer MACs and parameters, replicated in at least five paired seeds. Full qualification remains stricter: exact complete messages and boundaries, no accepted invalid/background messages, and the same five of six passing seeds in every profile across fresh and prior regression suites.

Both selected portfolios were frozen before family 531000000 was generated (`readout_cost_full_v3a`). The reduced graph failed mandatory SPI1 seed replication on pause traffic. CLOCKED_PAUSE_V20.md preserves those failures, causal traces and the independent full-pool coverage repair. The second freeze (`readout_cost_full_v3b`, family541000000) changes only six existing output-row configurations; all recurrent/hidden parameters and physical masks remain fixed. It adds A to the mandatory regression suites alongside full_shape_v2a and dense_full_v3a. Float and Q3.12 are separate. See QUALIFIED_SHAPES.md and the frozen joint qualification files for completed results; development counts above are not confirmation.

[Every completed stage and its exposure](runs/connectivity01/readout_routing_trials.csv); [per-condition development results](runs/connectivity01/readout_routing_conditions.json); [exact resource definitions](runs/connectivity01/readout_routing_resources.json). Checkpoints, raw learning curves, projections, covariance matrices, bank identities and source snapshots remain under their original v14–v19 labels. REPRODUCE.md gives immutable replay/resume commands.
