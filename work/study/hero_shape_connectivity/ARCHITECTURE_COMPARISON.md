# Leading physical architectures

**Resource and mechanism comparison; consult QUALIFIED_SHAPES.md for frozen confirmation status.**

The 64-unit candidates use the same 48-state backbone: 16 sparse first-layer nodes and two actual 16-node directed closed rings. Their extra 16 nonlinear units either change when first-layer states update or add a nonlinear output transformation. The two readout graphs differ by 256 physical connections.

| Architecture | Stored states | Nonlinear units | MACs/tick | Leak-blend multiplies/tick | Parameters | Activation depth | Modeled numeric storage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Plain48 control | 48 | 48 | 600 | 96 | 654 | 1 | 9,790 bytes |
| First-layer gates | 48 | 64 | 696 | 96 | 766 | 1 | 9,982 bytes |
| Nonlinear readout | 48 | 64 | 1464 | 96 | 1534 | 2 | 11,550 bytes |
| Reduced nonlinear readout | 48 | 64 | 1208 | 96 | 1278 | 2 | 11,038 bytes |

The storage subtotal assumes16-bit packed weights/state values, two state banks, programmable leaks and one shared8,194-byte activation table. It explicitly excludes assembler buffers/control, preprocessing/divider registers, routing and executable software. Input conditioning uses three prior levels, three capped9-bit ages and the common programmable divider; the pulse interface holds a3-bit previous class. The event-only assembler has up to1,026 payload bytes plus ACK/boundary state. Divider width, implementation sharing, accumulator/register allocation, routed area and maximum clock are not established. These are exact model connection/operation counts and an explicit storage model, not a claim of silicon fit or throughput. `clock_hz=0`.

The original 24→20→20 sparse baseline costs 1,016 MACs/sample and 1,086 parameters; its clocked-qualified sparse→ring→ring aligned-route control costs 776/846. Those simpler graphs do not have the full UART qualification of the leading readout architecture. The reduced nonlinear-head receiver costs more than the original sparse baseline (1,208 versus 1,016 MACs). Its 17.49% saving is relative to the full dense-head receiver, not relative to that original baseline. The extra readout hardware remains visible in the total counts.

## Exact connections

First-layer nodes0–15 each receive all nine generic features and four fixed sparse recurrent sources, including self. Ring16–31 has exactly one local predecessor per node, including31→16. Ring32–47 likewise closes47→32. Both rings receive first-layer nodes0,4,8,12 only at their inlet (16 or32). Every first-layer node receives two registered return edges from each ring: its aligned node and the node four positions ahead. All backbone routes use previous-sample state.

The first-layer-gated shape adds one sigmoid gate to each node0–15. Each gate reads prior states16,20,24,28,32 and its own first-layer state. The proposal and gate are computed from current features/previous state, then blended with the old state. Six affine logits read all48 stored states. All16 sigmoid units and96 gate-input weights are counted.

The dense-readout shape adds nodes48–63. Each applies tanh to all48 current backbone outputs. These16 units have no recurrence, return edges or state carry. Six affine logits read the48 backbone outputs and16 new nonlinear outputs. This adds768 hidden input connections and96 final-readout connections; it requires a second activation stage in the same modeled sample.

The reduced-readout shape retains all 16 fast-ring parents (16–31) for each hidden unit. Hidden unit 48+j also reads first-layer nodes `(j+2k) mod 16` and slow-ring nodes `32+(j+2k) mod 16`, for k=0…7. It has 512 hidden input connections. The 256 removed edges have no parameter slots; they are not merely zero weights. The 48-state backbone and all 384 final-output edges are identical to the dense shape. This saves 17.49% of MACs, 16.69% of parameters, 16.41% of multiplies including leak blends, and 4.43% of the stated numeric storage subtotal.

The parameter column counts connection weights and biases. Both readout graphs additionally retain 48 programmable leak coefficients, already included in storage. Counting those gives 1,582 versus 1,326 coefficient slots, a 16.18% reduction. Lane mapping and the shared speed divider are also common settings. These common costs are not hidden in the savings claim.

For both readout graphs the backbone computes `h[t]` from generic input features at t and registered backbone state at t−1. The extra units compute `u[t] = tanh(W h[t] + b)` with no persistent hidden state. Six affine logits read `[h[t], u[t]]`; the common previous-class register emits causal event onsets. Thus the backbone is registered while the nonlinear head is current-sample. This schedule is part of the physical definition and is distinct from making inter-layer backbone routes current-sample.

Different learned leaks and weights are protocol configurations, not new physical shapes. Full masks, delays, gate edges, equations and literal hardware hashes are recorded in `runs/connectivity01/current_lead_resources.json` and the frozen confirmation topology files.

## What the interventions establish

Clamping all conditional gate inputs to zero, while retaining learned gate biases and converting them exactly to ordinary leaks, destroys complete-message recovery in five previously passing UART configurations. Both implementations were checked bitwise. This establishes dependence on conditional gates in those weights; it does not prove an ungated shape cannot learn.

The dense-readout parity seed101 had43 event-pulse errors in57,344 balanced startup training cases. Adjusting only its existing affine outputs repaired all of them while retaining full development recovery. The reduced graph later required the same coverage correction. This is evidence of a coverage/fitting gap for those learned representations. Fresh confirmation is scored separately.

![First-layer gated actual graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak0.5,1.0,0.125_both2_mixed_first.png)

![Dense nonlinear readout actual graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_dense.png)

![Reduced nonlinear readout actual graph](runs/connectivity01/figures/srr_registered_16-16-16_port_firstlast4_leak1.0,1.0,0.125_both2_readout16_fanin32_fast.png)

![Measured conditional gate trace](runs/connectivity01/figures/gate_trace_uart_e_29_v6.png)

See FOLLOWUPS.md for preregistered thresholds, NATIVE_COMPARISON.md for matched initial training, READOUT_ROUTING_COMPARISON.md for paired edge-removal and conditional head fitting, COVERAGE_V10.md for the balanced-grid intervention and REPRODUCE.md for frozen replay. Current development portfolios use different recorded continuations; they are not presented as an equal-exposure topology ranking.
