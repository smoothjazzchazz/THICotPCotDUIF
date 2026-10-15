# Two confirmed physical receiver shapes

**Two distinct physical shapes meet the original floating-point UART, I2C and all-mode SPI qualification gates.** The reduced graph also establishes the preregistered resource result against the dense graph on paired fresh data and retained regressions.

Both use 16 sparse recurrent nodes, two actual directed 16-node rings, and 16 current-sample nonlinear readout units: 64 nonlinear units and 48 stored recurrent states. The rings are parallel branches with registered returns to the sparse layer. Each protocol has separately learned weights on the same fixed physical graph. Input, recurrent and readout parameters were trained off chip; these are demonstration configurations.

| Shape | Inputs per nonlinear readout unit | MACs/sample | Weights and biases | Stored recurrent states |
| --- | ---: | ---: | ---: | ---: |
| Reduced nonlinear readout | 32 | 1,208 | 1,278 | 48 |
| Dense nonlinear readout | 48 | 1,464 | 1,534 | 48 |

Removing 256 actual connections saves 17.49% of MACs and 16.69% of weights/biases. Including programmable leaks gives 16.18% fewer coefficient slots; including leak-blend arithmetic gives 16.41% fewer multiplies. The stated numeric storage subtotal decreases 4.43%. These are model operation/storage counts, not routed silicon area or clock measurements.

The reduced graph costs more than the original 24→20→20 sparse baseline (1,208 versus 1,016 MACs/sample). The latter did not qualify on UART. The full-profile saving above is relative to the qualifying dense-readout graph. The earlier strictly matched clocked-only comparison independently established 23.62% fewer MACs and 22.10% fewer parameters for true rings with lighter routes; that result remains separately scoped in REPORT.md.

## Qualification evidence

| Shape / arithmetic | UART 8N1 | UART 8E1 | I2C | SPI0 | SPI1 | SPI2 | SPI3 | Qualified |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Reduced nonlinear readout / float | 5/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | yes |
| Reduced nonlinear readout / Q3.12 | 5/6 | 5/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | yes |
| Dense nonlinear readout / float | 5/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | yes |
| Dense nonlinear readout / Q3.12 | 5/6 | 4/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | no |

**Quantization limitation:** Dense nonlinear readout does not meet the final Q3.12 gates (uart_e: 4/6). Earlier passing quantized snapshots are retained but do not erase this newer failure. Its floating-point qualification remains separate.

Final paired confirmation: `readout_cost_full_v3b`, 307 fresh cases containing 40,448 valid complete-message groups before seed/arithmetic replay. Every declared valid timing condition has at least 1,000 messages. Tests include all byte values, patterns, 1,024-byte payloads, timing mismatch/jitter or duty/setup/pauses, cold/midstream startup, long idle, invalid/background rejection and recovery. The same at least five of six seeds per profile must pass all fresh and prior-regression conditions. All six seeds remain reported; no failing seed is replaced.

A passing configuration recovers every complete message and exact boundary with no extra accepted invalid/background traffic in the declared suite. UART seed 47 remains unsuccessful in both graphs. The raw per-condition failures, including all earlier frozen trials, are retained. Float is the original qualification target; quantized results are a separate column and never substitute for float.

The contract audit verified all 84 frozen configurations, exact physical identities, finite weights, causal prefix/chunk/online agreement, and 614 fresh waveform/metadata files generated after freeze. An independent waveform parser checks the declared valid payloads. These tests establish the stated generated distributions, not correctness on every possible waveform.

## What the structural search taught us

1. Actual rings can replace later sparse layers for clocked reception at lower cost. The initial five requested connectivity patterns and both inter-layer schedules were compared with matched allocations, seeds and corrected timing coverage. Self/skip variants, direction, routes, input access and allocations remain distinct recorded trials.
2. Tight setup exposed both data coverage and routing delay. Retraining the sparse baseline with tight setup repairs its earlier failure; restricting a registered receiver to late-layer readout can erase the timely information needed for one-tick setup.
3. UART required more than falling loss or retained memory. The final graphs combine fast/slow recurrent state with a nonlinear current-sample readout. At the same 32-parent head budget, retaining every fast-ring state worked better in the tested projection than retaining every first-layer state. This does not prove the discarded layout cannot learn.
4. Several rare failures were coverage/fitting gaps. Balanced startup training repaired UART parity using fixed recurrent/hidden states. Independent continuous-pause data reproduced later SPI failures; changing only existing output rows repaired them. Frozen causal traces show identical backbones but different readout decisions at those errors.
5. Lower-cost gate variants did not meet the float parity gates, and some fits collapsed or remained unresolved. Their checkpoints, learning curves, unsuccessful confirmation suites and rejected hypotheses are preserved. A plateau or a bounded fitting failure is not classified as a whole-architecture impossibility.

The final pruning experiment uses same-seed learned backbones, identical waveform pools and the same conditional fitting rule. Actual additional optimization exposure differs and is recorded. It establishes a replicated physical cost/recovery result; it does not establish easier from-scratch training. Successful profiles were retained rather than repeatedly optimized toward smaller loss.

A clean rerun of the reduced SPI1 seed 47 pause-fitting job reproduced its weights and leaks bit-for-bit, its selected epoch, and its complete development scores. Frozen-source replay, checkpoint hashes and per-case traces are retained alongside that actual training reproduction.

## Connections and deliverables

![Actual shared recurrent connections](runs/connectivity01/figures/readout_shared_backbone.png)

![Every readout parent connection](runs/connectivity01/figures/readout_parent_masks.png)

- [Fixed topologies, demonstration weights and all-seed qualification](QUALIFIED_SHAPES.md).
- [Paired fresh/regression cost criterion and message bootstrap results](PAIRED_READOUT_RESULT.md).
- [Physical equations, total counted resources and excluded implementation costs](ARCHITECTURE_COMPARISON.md).
- [Readout routing comparisons and learning curves](READOUT_ROUTING_COMPARISON.md); [pause failures and coverage repair](CLOCKED_PAUSE_V20.md).
- [Reproducible training/resume, frozen replay and raw-waveform inference commands](REPRODUCE.md).
- [Every training trial](runs/connectivity01/training_trials.csv), [every confirmation condition](runs/connectivity01/qualified_per_condition_v3.csv), and [every failed qualification condition](runs/connectivity01/qualification_failures_v3.csv).

This remains receive-model evidence at known nominal speed with a common programmable divider. No RTL, electrical-compliance, routed timing/area, on-chip-training or full waveform-response gate is claimed; clock_hz remains 0. USB low-speed and Ethernet packet extensions are untested: this shared experiment has no complete qualified training/evaluation implementation for them, so no architectural conclusion is drawn about either extension. Historical trials and released reference files remain unchanged.
