# Find two reservoir shapes that reliably receive multiple protocols

## 1. Objective and fixed-hardware contract

Find **two tested reservoir shapes**, each capable of receiving complete UART, I2C, and SPI messages using separately trained configurations.

The agreed scope is:

- **Floating-point proof first.** Fixed-point performance and hardware cost are reported separately.
- **Known nominal speed**, using a shared programmable sampling divider.
- **Programmable weights and timescales**, trained or selected off chip.
- **SPI modes 0–3**, one receive direction at a time.
- Normally **20–64 total reservoir nodes**, including every branch, layer, and combining reservoir.

Each candidate freezes its physical connections, node equations, activation, input interface, readout structure, and update schedule. Protocol configurations may change weights, supported leak settings, lane mapping, sampling divider, and message-assembly rules. They cannot introduce connections or additional processing hardware.

The trained weights are **evidence that the shape can learn each protocol**, not proposed final production weights.

## 2. Begin with brainstorming and research

Before implementing candidates, produce a short requirements-and-hypotheses document covering:

| Required ability | Why it matters |
|---|---|
| Preserve recent transitions precisely | SPI sampling and I2C clock/data relationships |
| Maintain timing without new edges | UART repeated bits and stop timing |
| Retain context across interruptions | I2C stretching, gaps, and repeated START |
| Separate fast detail from longer context | Avoid losing individual bits while remembering frame position |
| Recover after invalid input or startup | Continuous operation cannot depend on resets between examples |
| Preserve distinguishable states | A readout cannot recover information the reservoir has erased |

Research will concentrate on **DeepESN layering, simple ring/chain topologies, parallel reservoirs, and leak-controlled timescales**. The literature supports testing these mechanisms; it does not establish that they work for these protocols within 64 nodes. In particular, the reviewed DeepESN topology study used 500 nodes. [DeepESN survey](https://arxiv.org/abs/1712.04323), [topology study](https://arxiv.org/abs/1909.11022), [parallel versus deep reservoirs](https://arxiv.org/abs/1908.08380), [timescale study](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2024.1397915/full).

The two leading **starting hypotheses**, not predetermined winners, are:

| Candidate | Initial arrangement | Hypothesis and principal risk |
|---|---|---|
| **Three-layer reservoir** | 48 nodes: **16 → 16 → 16**; 64 nodes: **24 → 20 → 20**. Readout sees every layer. | Early layers preserve transitions; deeper layers retain context. Excessive smoothing could erase precise timing. |
| **Parallel fast/slow reservoirs with a combining reservoir** | 48 nodes: **16 fast + 16 slow → 16 combining**; 64 nodes: **24 fast + 24 slow → 16 combining**. Readout sees all three. | Preserve fast detail and long memory separately, then learn their relationship. Branches could become redundant or consume too much connectivity. |

Compare these with four simpler families: a flat sparse reservoir, a ring with fixed skip connections, a two-layer stack, and a delay-chain-plus-sparse-reservoir hybrid.

For stacked candidates, explicitly compare current-sample layer propagation with registered inter-layer propagation. These are different shapes with different latency and scheduling costs.

## 3. Build one shared experiment

Create an isolated experiment under `work/study/protocol_hero_search/`, preserving historical models, results, and current unrelated changes.

**Receiver and interfaces**

- Use three generic sampled input lanes, sufficient for SPI clock/select/data and the two-lane protocols.
- Supply identical level, signed-edge, and capped elapsed-time features to every candidate. No protocol decoder, bit-position counter, or generator boundary enters the receiver.
- Provide a common streaming interface: samples and tick in; learned bit, boundary, and invalid events out. Represent event occurrence separately from bit value so repeated identical bits remain separate events.
- Assemble messages from learned events only. The assembler may count bits and check parity or packet fields, but cannot inspect waveforms or reconstruct missing samples.
- Keep state continuous across messages and training chunks. Record observation time and actual decision time separately.

**Required protocol coverage**

| Protocol | Required receive tests |
|---|---|
| UART | 8N1 and 8E1; every byte value; repeated bits; adjacent frames; parity/framing errors; break and recovery |
| I2C | Single-controller, 7-bit transactions; address/direction; ACK/NACK; reads/writes; repeated START; stretching; partial transfers |
| SPI | Modes 0–3; 8-bit words; variable transaction lengths; select boundaries; clock pauses; aborted transfers |

Use separate weights per declared profile, including SPI mode when needed. UART message grouping is an evaluation convention; no hidden packet boundary is supplied to inference.

Audit the existing generators and scorers before reuse. Add a sourced SPI profile using manufacturer documentation, and independently check generated waveforms. [SPI reference](https://www.analog.com/en/resources/analog-dialogue/articles/2018/08/13/15/31/introduction-to-spi-interface.html).

## 4. Search and train without confusing insufficient training with failure

**Screen broadly, then concentrate effort.**

1. Screen all six families at 32, 48, and 64 nodes using three initialization seeds and every mandatory protocol profile.
2. Keep connection masks fixed across protocols and weight seeds. Explore sparse connectivity and ring/chain arrangements as separately identified candidates.
3. Train both conventional readout-only ESN controls and networks with trainable input, recurrent, inter-layer, bias, and readout weights. Clearly label the latter as trained recurrent networks inspired by reservoir computing.
4. Advance the best four distinct shapes using their **weakest protocol performance**. Give improving candidates additional training before pruning them.
5. Train finalists with six seeds: `11, 29, 47, 71, 101, 131`. Test 20–24-node reductions of successful families.
6. Permit a 72-node comparison only when a promising 64-node family shows a specific memory limitation after training diagnostics; include a matched 64-node continuation.

Start with 30 epochs and a 512-tick backpropagation window. Preserve state across truncations. Audit gradients and extend the window when a diagnostic demonstrates that relevant credit assignment exceeds it.

Use a curriculum progressing from clean short frames to repeated bits, boundaries, continuous messages, timing variation, and malformed input. Every curriculum finishes on the full mixed training distribution.

Continue in 30-epoch blocks while development message accuracy improves, boundary accuracy improves by at least one percentage point, or loss falls by at least 2%. After two blocks without those improvements, run a lower-learning-rate continuation and a longer-window rescue before declaring a plateau. An interrupted improving run remains **training-limited**, not an architecture failure.

Select checkpoints by complete-message performance, then boundary errors and false events—not training loss alone. Preserve checkpoints, optimizer state, exposure counts, learning curves, and failed trials.

## 5. Qualification, extensions, and the final two

Freeze configurations and selection rules before generating fresh confirmation data.

**Mandatory confirmation**

- Every byte value, constant and alternating patterns, random payloads, and messages up to 1,024 bytes.
- At least 1,000 complete messages per declared valid timing condition.
- UART nominal timing, ±3% mismatch, one-tick jitter, and combined corners; SPI/I2C varied phase, duty cycle, pauses, and protocol-valid setup/hold conditions.
- Cold startup, mid-stream startup, long idle, malformed input, and recovery after an observable synchronization opportunity.
- Separate rejection results for inputs observably invalid under the loaded profile. Do not demand rejection of an “unknown” waveform indistinguishable from valid traffic.
- Causal-prefix checks, online/batch agreement, checkpoint replay, independent label audits, and no-recurrence controls.

A **qualified shape** must achieve exact messages and boundaries throughout the mandatory confirmation suite, with no extra accepted messages on the declared invalid/background suite. Require this across at least five of six training seeds for every mandatory profile. Report remaining seed failures explicitly.

Rank qualified shapes by worst-profile repeatability, then total storage/computation, then decision latency. Count preprocessing, readout, buffers, programmable settings, and scheduling alongside reservoir nodes. Run fixed-point replay on finalists, but retain the agreed floating-point qualification.

**USB and Ethernet**

After mandatory qualification, test both finalists with separately trained weights on USB low-speed packet reception and, secondarily, 10BASE-T Manchester/frame reception. Include packet boundaries, stuffing/line-code errors, and CRC/FCS checks. Full USB device operation and Ethernet electrical/link compliance remain outside this receive study.

For any deferred or unsuccessful extension, provide traces and a specific explanation: learning failure, insufficient retained information, timing/throughput cost, quantization, missing implementation, or untested scope. Do not report an unattempted extension as a failed architecture.

**Deliver the top two measured shapes**, with connection diagrams, exact configurations, example protocol weights, per-profile results, training adequacy, costs, and reproducible commands. If fewer than two qualify, identify the strongest two candidates and their unmet requirements plainly; do not manufacture two successful “hero” shapes.
