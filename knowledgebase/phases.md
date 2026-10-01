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

Work: Python golden model, assembler, reservoir study.

The study must cover:

- UART at ±3% baud error
- USB-LS-like NRZI at ±1.5%, edge jitter ±1/8 bit, 6-bit stuffed runs
- PS/2 and Manchester
- glitches, dropouts, and unrelated traffic

Record, for the reservoir and for a conventional decoder (edge-timing DPLL or run-length) at matched cell count: symbol accuracy, false positives, latency, and cells.

Open parameters, not yet fixed: nodes (12, 16, or 24), state bits, leak set, quantization (1 or 2 bits), `M`, topology seed.

Also due at or before G1 (v0.31): the receive-aperture decision (per-lane pin selects or literal classes), made in the golden model and recorded here, and the degenerate pass-through configuration demonstrated in the model.

Decision, using the proposed bar:

- **Go** if a 16–24 node reservoir reaches at least 99% symbol accuracy at the stated jitter, on at least 2 of 3 target codes, within about 2K cells.
- **Partial** if the reservoir is the recommended front end only for the codes that pass, and the on-die conventional classifier (or the degenerate configuration) is recommended for the rest.
- **No-go** if the conventional classifier becomes the primary front end and the reservoir ships as the research configuration. The silicon is the same under every outcome (v0.31 section 6); only the recommended weight files differ.

Write the decision and the measurements in `work/study/`. "About 2K cells" and 99% are the proposed bar, not a measured result.

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

Each v0.31 section 10 demonstration is marked pass, fail, or deferred:

1. UART TX out of a pin as TX-table symbols, then programmable.
2. GPIO mode loaded as weights, shown with the pass-through equivalence proof.
3. Hero: a line code the silicon was never designed for (NEC-IR-like or 1-Wire-style), loaded post-fab, decoded and re-emitted.
4. Reflex exchange (I2C ACK or SPI slave response) with zero core instructions in the fast path.
5. Dual-front-end disagreement capture and the class-7 unknown-waveform flag.
6. UART, SPI, and I2C as firmware plus weight files, measured under baud error and jitter versus the on-die conventional classifier.
7. USB low-speed device-side exchange in simulation; on silicon only if electrical checks have passed. On-chip snapshot teaching only if Tier 3 survived.

`docs/info.md`, the README, and the `info.yaml` pinout match the RTL that was frozen.

## Submit buffer — 5–18 Jan 2027

Precheck and gate-level failures are fixed inside the frozen feature set. No new tier is added in the buffer.
