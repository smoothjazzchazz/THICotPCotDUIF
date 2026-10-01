# Phases and gates

From v0.3 section 9, as amended by v0.31 section 7. Deadline 18 Jan 2027. Feature freeze 4 Jan 2027. A gate is passed only when the artifact below exists and the check is true. A narrative is not a pass.

Thresholds v0.3 calls proposed stay proposed until the team writes a replacement in this file.

Holiday weeks are slack-prone. Assume reduced throughput from 24 Dec 2026.

## G0 — 14 Oct 2026

Work: resolve **[VERIFY]** items, prior-art pass, skeleton through full CI, UART TX out of a pin (through the TX table), synthesize core plus RAM variants (64 and 128 words; flops versus latch or macro) plus the symbol-layer datapath skeleton — it is Tier 1 under v0.31.

Pass only if all of these are true:

- Template CI is green: test, docs, GDS, and FPGA workflows.
- `info.yaml` `tiles` is `6x4`.
- Synthesis reports exist for core plus program RAM at 64 words and at 128 words, and for the symbol-layer datapath skeleton. A latch or SRAM macro variant is included only if [placeholders/hardware/tt-sram-or-latch-ram.md](placeholders/hardware/tt-sram-or-latch-ram.md) is no longer `missing`.
- A written RAM choice: depth and implementation.
- The synthesis used for that choice reserves at least 25% slack.
- Every **[VERIFY]** placeholder is either still `status: missing` or names the source that resolved it. A resolved stub is not a guess.

## G1 — 28 Oct 2026

Work: Python golden model, assembler, reservoir study. The study looks for a temporal shape the nodes can hold, and checks that the boring settings file can carry UART, SPI, and I2C as firmware. See [doctrine.md](doctrine.md).

Traces to generate:

- the candidate hero shape (a short pattern defined across time, not a clocked UART bit)
- UART at ±3% baud error, as a stepping-stone trace
- USB-LS-like NRZI at ±1.5%, edge jitter ±1/8 bit, 6-bit stuffed runs
- PS/2 and Manchester
- glitches, dropouts, unrelated traffic, and at least one stranger wiggle that should be pattern 7

Record, for both listeners, symbol accuracy, false positives, latency, and whether node state for the hero shape is visibly distinct. Also record cells. A gap versus the edge listener on UART is data for the disagreement bit, not a grade.

Open parameters, not yet fixed: nodes (12, 16, or 24), state bits, leak set, quantization (1 or 2 bits), `M`, topology seed. If 1-bit Hamming cannot hold the hero shape, try a richer readout before declaring the shape impossible. Area still has to fit at G0.

Also due at or before G1: the receive-aperture decision (per-lane pin selects or literal classes), made in the golden model and recorded here, and the boring pass-through file demonstrated in the model.

Decision:

- **Show** if at least one temporal shape is recognized well enough to demo load, decode, and re-emit, and pattern 7 rejects a stranger. The numeric bar for that shape is written in `work/study/` when the shape is chosen.
- **Cover** if the boring file is good enough that UART, SPI, and I2C can be firmware plus that file. This is required either way.
- **Thin** if the hero shape does not stick. The chip still ships both listeners and pattern 7. Do not add a pin path, and do not retune the project into a normal UART. Write what was tried.

Write the traces, the hero choice, and both listeners' numbers in `work/study/`.

## G2 — 2 Dec 2026

Work through weeks 5–8: core RTL, loader, symbol-layer RTL with both classifiers, reflex table, UART/SPI/I2C as weight files plus firmware. Week 9 is the gate.

Pass only if all of these are true:

- A feature list matches the tier that survived G1. No Tier 3 block is present unless this gate explicitly keeps it.
- A lockstep log shows RTL matches the golden model on pins, FIFO events, and reservoir state, including a run under the degenerate pass-through configuration.
- A synthesis report fits 6×4.

## G3 — 23 Dec 2026

Pass only if all of these are true:

- Formal results are filed for: program-counter bounds; `WAIT N` exact; reflex/`TXSYM` serialization with no silent drop and constant reflex latency (replaces single pin owner); a FIFO drop sets the flag; reservoir saturation bounds; bounded fading memory; and the **pass-through equivalence proof** (degenerate configuration cycle-equivalent to the reference synchronizer/edge FSM — induction preferred, bounded equivalence over exhaustive short traces as the recorded fallback). Each result is a proof or a counterexample.
- A constrained-random run is logged.
- LibreLane finishes.
- An STA report is filed. A passing setup check is required before any frequency is stated. Filing the report is not itself a frequency claim.
- The template gate-level test has been run, and the result is recorded.
- ice40up5k bring-up result is recorded.

AI-generated tests or properties are logged with how each was validated.

## Freeze — 4 Jan 2027

Each demonstration in [doctrine.md](doctrine.md) is marked pass, fail, or deferred:

1. A temporal line code loaded as weights plus a transmit table, decoded and re-emitted.
2. Pattern 7 on a wiggle outside the loaded set.
3. Reservoir node state readable during that shape.
4. Sticky disagreement between the two listeners.
5. A reflex reply (I2C ACK or SPI slave response) with the program counter unchanged during the reply.
6. UART, then SPI, then I2C, each as a further loaded file. They work. They are not scored against a normal decoder.
7. The boring settings file, checked against a small edge detector (proof or recorded bounded check).
8. USB low-speed in simulation only, unless pad checks have passed. On-chip prototype snapshot only if area remains.

`docs/info.md`, the README, and the `info.yaml` pinout match the RTL that was frozen. The submission narrative follows the order above, not UART-first.

## Submit buffer — 5–18 Jan 2027

Precheck and gate-level failures are fixed inside the frozen feature set. No new tier is added in the buffer.
