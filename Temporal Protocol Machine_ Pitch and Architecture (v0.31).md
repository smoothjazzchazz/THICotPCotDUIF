# Temporal Protocol Machine: Pitch and Architecture (v0.31)

**Status:** working draft for team review. This document **amends v0.3**; it is not a rewrite. Where it is silent, v0.3 stands. Where they disagree, v0.31 wins. **\[EST\]** = back-of-envelope, to be replaced by synthesis. **\[VERIFY\]** = assumption not yet checked against Tiny Tapeout / IHP docs. Written 1 Oct 2026. Deadline unchanged: **18 Jan 2027**.

## 0. What changed since v0.3, and why

| v0.3 | v0.31 | Why |
| --- | --- | --- |
| Core reads and drives pins directly; a **bypass path always exists** | **The core never touches a pin.** All input reaches the core as symbol events; all output leaves as symbols through the TX table. There is no pin-level bypass wire | With a bypass, every protocol the challenge names as the starting bar (UART, SPI, I2C) works with the reservoir powered off, so the chip degrades to "PIO plus an extra." Removing the pin path makes the symbol layer indispensable by construction: the ISA has no other I/O |
| Bypass = dedicated silicon path | **Bypass = a weight file.** A degenerate symbol-layer configuration (pass-through feature taps, zeroed recurrence, maximal leak, level/edge prototypes) acts as a synchronizer plus edge detector with fixed small latency | The escape hatch still exists functionally, but it is *data* through the same silicon as the exotic line codes. Even the chip's most boring mode is post-fab programmable |
| Fallback classifier replaces the reservoir on a G1 no-go | **Both classifiers on die**, behind the same symbol-event interface: the reservoir and the windowed Δt / run-length classifier | The G1 hedge moves inside the symbol abstraction instead of bypassing it, and doubles as the comparison-in-silicon demo. A judge can watch the two front ends agree and disagree on real pins |
| Fast responses (SPI slave first MISO bit) use the bypass | **Reflex table:** RX class → TX symbol mappings fired by the symbol layer directly, no core instructions in the loop | Fast paths stay inside the symbol abstraction. A reflex latency is a constant that can be stated exactly |
| Pin ownership mux: each output pin owned by core-direct or TX engine | **TX engine always owns output pins.** Core-direct drive and the ownership mux are deleted | The "never both" formal property dissolves into a simpler arbitration property between core-queued symbols and reflexes |
| Tier 1 = core + bypass protocols | **Tier 1 = core + symbol layer in degenerate configuration** + UART/SPI/I2C as weight files plus firmware | The symbol-layer datapath moves onto the critical path of the first milestone. See section 7 |

Nothing else in v0.3 changes: the reservoir micro-architecture (16 nodes, 6-bit state, fixed sparse topology, `s' = sat(s − (s >> k) + Σ w·x)`), the readout, the stabilizer, the event format `{class 3b, start-timestamp 12b}`, the FIFOs, the CRC/LFSR unit, the loader and config shift chain, the schedule and gate dates, the claims policy (with the additions in section 9), and the Ethernet analysis-only scoping all stand.

## 1. Revised pitch

**One-liner:** an open-source, post-fabrication-programmable **symbol transducer**: every bit the chip hears or says — including its own plain-GPIO mode — passes through a loadable waveform interpreter. A small digital reservoir (weights trained off-chip) and a conventional classifier sit side by side behind one symbol-event interface; a deterministic core consumes and emits timestamped symbols; a mirrored TX table and a reflex table turn symbols back into waveforms. New line codes, and even "raw pin access," are data, not silicon.

**Why this answers "what would you do differently from PIO/PRU":** PIO programs pin *timing*; it has no programmable waveform *interpretation*, and its escape hatch is always a raw pin. Here there is no raw pin. The question "what happens if the novel part fails" is answered with a proof artifact (section 6), not with a parallel copy of a conventional design.

## 2. Guardrails (replaces the v0.3 section 4 guardrail list)

- The reservoir never drives pins. It emits symbols only; the core and the reflex table decide.
- **A formally verified pass-through configuration always exists.** The symbol layer is the only pin interface. (Replaces "a bypass path always exists.")
- The reflex table is configuration, not a learned structure. Reflexes are armed and disarmed by the core.
- No analyzer features, no general NN claims. The symbol-event interface remains the architectural contract; classifiers behind it are swappable and, in v0.31, both present.

## 3. ISA changes (amends v0.3 section 5.1)

Removed: wait-on-pin, set/clear-pin, pin direction and OE ops, and the branch-on-pin condition. The core has no pin-level I/O.

Changed or added:

- `WAIT` waits on a class event, a cycle count, or a timeout. Branch conditions: class, counter, shift-count, FIFO status, CRC state.
- `RXSYM`, `TXSYM`, `TXBYTE`, CRC ops, tick-divider/config select: unchanged from v0.3.
- **`ARM` / `DISARM`:** enable or disable a reflex-table entry.
- Per-instruction delay field, timestamps, capture-on-edge (the timestamp capture source is a class event, not a raw edge), ALU: unchanged.

Open-drain behaviour (drive 0 / release) is expressed as TX-table symbols with per-symbol OE masks, which v0.3 already specified. Pad behaviour remains **\[VERIFY\]**.

## 4. Receive aperture (amends v0.3 section 5.2 item 3)

With the bypass gone, the 4-pin feature window is the chip's only receive aperture, so it must cover concurrent slow signals (for example CS while watching MOSI). This is the one genuinely new design question v0.31 opens. Candidate answers, to be settled in the golden model and study **before G1**, not in RTL:

1. Per-feature-lane pin select (4 independent lane muxes instead of one 4-pin group select).
2. Literal classes: the conditioner emits level/edge of selected pins directly as reserved class codes, bypassing the classifier *stage* but not the symbol interface.
3. Both, if the config-bit and mux cost stays small **\[EST\]**.

Until settled, firmware plans assume option 1.

## 5. Transmit: reflex table, single owner (amends v0.3 section 5.3)

- TX table, TX FIFO, bit-stream mode: unchanged.
- **Reflex table: 8 entries \[EST\].** Each entry: match class (3b), emit symbol (3b), armed bit, and a one-shot/continuous bit — on the order of 8 bits per entry plus comparators, ~64 config bits **\[EST\]**. When an armed entry's class event is emitted by the stabilizer, the TX engine queues that symbol ahead of the core's TX FIFO stream.
- Core-direct drive and the pin-ownership mux are **deleted**. The TX engine always owns output pins.
- New formal property replacing "never both": **a reflex emission and a core `TXSYM` are serialized by the TX engine; no symbol is dropped silently (flag on conflict), and reflex latency from stabilizer event to first output tick is a constant.**

## 6. Dual classifier and the pass-through proof (replaces v0.3 section 6.5)

The windowed Δt-template / run-length classifier is built **next to** the reservoir, not kept as a contingency swap. Both sit behind the same symbol-event interface; a config bit (or per-class source mask **\[EST\]**) selects which front end feeds the stabilizer, and a debug mode exposes both for disagreement capture (class 7 and a sticky disagree flag).

Verification additions:

- **Pass-through equivalence proof:** with the degenerate weight file loaded, the symbol layer is cycle-equivalent to a reference synchronizer + edge-detector FSM. Target: SymbiYosys induction on the integer datapath with the weights fixed as constants. This proof is the replacement for the bypass: the chip can never do worse than a conventional edge detector, because that behaviour is a verified point in its configuration space.
- The G1 study and the matched-cell-count comparison proceed exactly as in v0.3 section 7; the conventional classifier being on die makes the comparison repeatable on silicon.
- Lockstep, directed tests, constrained-random, and the existing formal list all stand; the single-pin-owner property is replaced by the serialization property in section 5.

Claims discipline: "formally verified pass-through configuration" may not be said until the proof artifact is filed (see section 9).

## 7. Tiers and schedule impact (amends v0.3 sections 4 and 9)

- **Tier 1 (mandatory):** core, program RAM, loader, **symbol-layer datapath with the degenerate configuration**, TX table, and UART/SPI/I2C as weight files plus firmware. The symbol layer is no longer deferrable to Tier 2.
- **Tier 2 (the novelty, integral):** trained reservoir configurations, dual-classifier operation, reflex table, CRC16 unit, byte-streaming, RX/TX FIFO depth as specified.
- **Tier 3 (cut first):** unchanged list from v0.3, minus anything above.

Gate dates are unchanged (G0 14 Oct, G1 28 Oct, G2 2 Dec, G3 23 Dec, freeze 4 Jan). Two meanings shift:

- **G0** must now synthesize the symbol-layer datapath skeleton along with core + RAM, since it is Tier 1. Same ≥25% slack rule.
- **G1 no-go** no longer means "ship without a symbol layer." It means: the conventional classifier becomes the primary front end and the reservoir ships as the research configuration, reported honestly. The silicon is the same either way; only the recommended weight files differ.

Added RTL for weeks 5–8: reflex table and the second classifier. Both are small **\[EST\]** (section 8), but the aperture decision (section 4) must land at G1 or earlier to avoid a week-5 stall. Holiday-slack assumptions from v0.3 stand.

## 8. Feasibility deltas (all **\[EST\]**, G0 synthesis decides)

Baseline from v0.3 section 6.1: ~4–5K combinational cells + ~3.3–3.6K flops ≈ 8–9K cells, against the announcement's nominal ~24K (24 tiles × ~1K cells/tile), with the real constraint expected to be flop area at 60% placement density.

| Change | Cells | Flops / config bits |
| --- | --- | --- |
| Delete core-direct drive paths + pin-ownership mux | −0.1 to −0.2K comb | −~16 config bits |
| Delete pin-level ISA ops (decode shrink) | small − | — |
| Reflex table (8 entries, comparators, arbitration) | +~0.1K | +~64 config bits, +~10 flops |
| Conventional classifier on die (Δt counters, run-length compare) | +0.3 to 0.5K | +~60–100 flops |
| Event source select + disagree capture | small + | +~20 bits |
| Aperture option 1 (per-lane pin select) | +small mux growth | +~12 config bits |
| **Net** | **+0.3 to +0.5K** | **+~100–150** |

Projected total ≈ 8.5–9.5K cells **\[EST\]** of ~24K nominal: the change fits inside the existing margin, and the mitigation ladder from v0.3 (latch/SRAM RAM, 64 words, drop Tier 3, shrink prototypes/FIFOs) is untouched. Config chain grows from ~900 to ~1,000 bits **\[EST\]** — serial load time rises accordingly, no mux cost.

Latency and rate consequences, stated plainly:

- Non-reflex reaction time is bounded below by classification latency (~4 pipeline ticks + `M`). At tick = clk and `M` = 1, ~5 clocks **\[EST\]**.
- **SPI slave:** first-response path must be a reflex. Maximum SCK drops versus v0.3's bypass figure; with a reflex it is bounded by classification + reflex constants, roughly SCK ≲ clk/10 to clk/25 **\[EST\]**, i.e. ~2–5 MHz at the assumed 50 MHz flow clock (**\[VERIFY\]** board clock). This trade is accepted: determinism and the symbol abstraction over raw speed.
- UART, I2C, PS/2, JTAG/SWD, CAN: hundreds to thousands of clocks per bit at their v0.3 target rates; classification latency is negligible there. I2C ACK within half an SCL period (≥2.5 µs at 100 kHz) is comfortably a reflex.
- USB low-speed: unchanged scoping (simulation demo; silicon only if electrical checks pass). The handshake turnaround budget must be re-checked against reflex constants in the golden model.

## 9. Claims policy additions (extends v0.3 section 12)

We can additionally say, once the artifacts exist: every pin-level behaviour of the chip, including plain GPIO, is a loadable configuration; the pass-through configuration is formally verified equivalent to a conventional synchronizer/edge front end; two front ends are measured on the same silicon.

We must not say: "formally verified" anything before the proof is filed; any reflex or SPI-slave rate before post-route STA; that removing the bypass makes the chip faster or smaller (it is a flexibility/defensibility trade and the numbers above are estimates).

## 10. Demonstrations (replaces the v0.3 section 8 order)

1. UART TX out of a pin as TX-table symbols, then made programmable (unchanged first milestone, now through the table).
2. **GPIO mode loaded as weights**, with the pass-through equivalence proof shown alongside.
3. **Hero: a line code the silicon was never designed for** (NEC-IR-like or 1-Wire-style frame), loaded post-fab as weights + TX table, decoded and re-emitted.
4. Reflex exchange: I2C ACK or SPI slave response with zero core instructions in the fast path.
5. Dual-front-end disagreement capture and the class-7 unknown-waveform flag on a waveform outside the loaded set.
6. UART/SPI/I2C as firmware + weight files (the challenge's starting bar), measured under baud error and jitter versus the on-die conventional classifier.
7. USB-LS device-side exchange in simulation; on silicon only if electrical checks pass. On-chip snapshot teaching only if Tier 3 survives.

## 11. Risks added or changed by v0.31

1. **Risk concentration:** no silicon path works if the symbol-layer datapath is broken. Mitigations: the pass-through proof (section 6), the dual classifier, and the symbol layer moving to Tier 1 so it gets the most CI time, FPGA time, and gate-level time.
2. **Receive aperture** (section 4) is new design work on the critical path. Mitigation: decide in the golden model before G1; option 1 is the default.
3. **SPI slave rate regression** versus v0.3. Accepted and documented; reflex constants stated after STA only.
4. **Proof effort:** induction on the datapath with constant weights is plausible but unproven effort **\[EST\]**; if it stalls, fall back to bounded equivalence over exhaustive short traces, and say so.
5. All v0.3 risks (flop area, reservoir phase memory, timing closure, scope creep, late CI surprises) stand unchanged.
