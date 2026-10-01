# Temporal Protocol Machine: Pitch and Architecture (v0.3)

**Status:** working draft for team review. **\[EST\]** = back-of-envelope, to be replaced by synthesis. **\[VERIFY\]** = assumption not yet checked against Tiny Tapeout / IHP docs. Today: 1 Oct 2026. Deadline: **18 Jan 2027** (about 15 weeks).

## 0. What changed since v0.2

| v0.2 | v0.3 | Why |
| --- | --- | --- |
| Reservoir = optional coprocessor (`RES_MATCH` flag) | Reservoir = the **receive-side symbol layer**; all line-coded RX goes through it | A judge could delete the v0.2 matcher and still see a PIO clone. Now the chip depends on it. |
| 2 to 4 barrel contexts + timed pin scheduler | **Single context**; autonomous RX/TX symbol engines provide the concurrency and exact pin timing | Barrel threading added area and blurred timing. Contexts become a Tier 3 stretch. |
| Reservoir with programmable connectivity, time-multiplexed | **Fixed sparse topology, programmable weights/leaks, fully parallel** | Programmable fan-in needs wide muxes (thousands of cells). Folding also needs muxes. Hardwired parallel is smaller **and** faster. |
| Template slots + `RES_MATCH`/`RES_SYNC` | Prototype classes (Hamming) → class events with timestamps in an RX FIFO | Determinism now comes from timestamped events and a FIFO overflow flag. |
| ALU-lite only | + **16-bit programmable CRC/LFSR unit**, shift-tap | USB, CAN need CRCs. v0.2 had a gap. |
| 10 Mbit Ethernet "stretch" | Re-scoped to simulation/analysis only (section 6.4) | Clock arithmetic and CRC32 rule it out for silicon. |
| 256-word program RAM default | **128 words default**, 64 fallback | Flop-based RAM is the likely area bottleneck. |

## 1. Refined pitch

**One-liner:** an open-source, post-fabrication-programmable protocol machine whose receive side is a *software-defined line-code decoder*: a small digital reservoir, with weights trained off-chip and loaded after fab, turns raw pin waveforms into timestamped symbols that a deterministic PIO-class core consumes. A mirrored transmit table turns symbols back into pin waveforms. New line codes need new weights and tables, not new silicon.

**Why it fits the brief.** The brief asks for a tiny CPU whose ISA reads pins, writes pins, counts cycles and hits timing precisely, with protocols implemented in firmware and flexibility beyond a UART block plus an SPI block. Our core does that. The symbol layer is our answer to "consider what you'd do differently from PIO/PRU": PIO gives programmable pin timing, but it has no programmable waveform *interpretation*, so noisy, jittery or line-coded inputs are hand-decoded in instructions.

**Why it plausibly wins on novelty.** The challenge text says Jane Street will pay to tape out "the most novel designs", and the announcement post says they are particularly interested in unique functionality and novel design/verification approaches. Our differentiators, ordered by defensibility:

1. A **reservoir-based symbol layer** whose behaviour is changed by loading weights (measured against a conventional decoder).
2. A **symmetric TX waveform table**, so line coding is data, not logic.
3. **Bit-exact verification** of an integer reservoir (golden model, lockstep, formal properties on the symbol interface).
4. A published **reservoir vs conventional front-end** comparison at matched cell count, whichever way it comes out.

## 2. Compliance matrix (challenge rules and outline)

| Requirement from the challenge | Our response |
| --- | --- |
| IHP CMOS5L via Tiny Tapeout, start from the CMOS5L Verilog template | Use template unchanged: `tt_um_<name>` top, `ui/uo/uio` ports, LibreLane flow, CI (GDS, precheck, gate-level). |
| `info.yaml` tile size 6x4 | Set `tiles: "6x4"`. **\[VERIFY\]** template comment lists sizes only up to 8x2 and \~167x108 µm/tile, challenge says \~200x150 µm. |
| \~24 tiles, \~0.7 mm², \~1K cells/tile; may become 8x4 | Design **must fit 6x4** and never depend on 8x4. If 8x4 arrives, spend it on RAM size / contexts, not on core features. |
| "Run synthesis early … leave room for clock tree and routing; run full P&R" | Gate G0 (week 2): skeleton through full CI plus core+RAM synthesis. Reserve ≥25% slack. |
| SRAM can beat flops for instruction memory | Evaluate TT SRAM/latch examples at G0. **\[VERIFY\]** availability for CMOS5L. |
| Open source | Apache-2.0 (template LICENSE). All RTL, generators, models, tools, tests public from day one. |
| Teams recommended | Section 11: owners per workstream. |
| Deadline 18 Jan 2027; March 2027 shuttle | Schedule in section 9, freeze 4 Jan, 2-week buffer. **\[VERIFY\]** whether a separate Tiny Tapeout submission step has its own deadline. |
| "Start with UART, SPI, I2C" | Tier 1, no protocol-specific hardware. First milestone is literally "UART TX out of a pin, then make it programmable." |
| Stretch: low-speed USB, 10 Mbit Ethernet | USB-LS: silicon target (Tier 2). Ethernet: simulation/analysis only (6.4). |
| Other protocols: JTAG, SWD, PS/2, CAN | JTAG/SWD/PS/2 expressible by core alone. CAN via core plus symbol-layer edge assist (6.3). |
| "Show us anything else your architecture makes possible" | Loading new line codes post-fab; unknown-waveform flag; on-chip teach-by-snapshot. |
| Verification: formal, constrained-random, AI-assisted, Hardcaml | Section 7. Reservoir topology is generated, which suits Hardcaml's parametric style. |
| FPGA recommended before ASIC | ice40up5k workflow in template; **\[EST\]** design fits (\~8-10K cells). |

## 3. Novelty: what we can and cannot claim

Two quick literature/web searches found conventional Manchester clock-data-recovery and decoder techniques in abundance, and **no** reservoir-based line-code decoding in programmable I/O. That is a weak negative: it is not a literature review. **Week 1-2 task:** a proper prior-art pass (reservoir computing + serial decoding; open-source PIO-like cores; Tiny Tapeout designs, which include ternary dot-product blocks, so ternary arithmetic alone is not novel).

**Claim:** a programmable, deterministic, reservoir-based symbol layer, with measured accuracy/jitter tolerance versus a conventional decoder. **Do not claim:** that it beats FSMs or DPLLs generally, that the chip "learns protocols", or that training happens on-chip (training is off-chip; only prototype snapshot may be on-chip).

## 4. Scope tiers and guardrails

- **Tier 1 (mandatory):** single-context core, pins, timestamps/timeouts, program RAM, host loader. Delivers UART/SPI/I2C as programs, bypass path only.
- **Tier 2 (the novelty, integral):** symbol layer (front end + reservoir + readout + stabilizer + RX FIFO), TX table + TX FIFO, CRC16 unit, byte-streaming modes.
- **Tier 3 (cut first):** second context, on-chip snapshot teaching, 2-bit state quantization, linear readout, 256-word RAM, ring buffer.

**Guardrails:** the reservoir never drives pins; it emits symbols only, and the core decides. A bypass path always exists. No analyzer features, no general NN claims. The **symbol-event interface** is the architectural contract, so the classifier is swappable (section 6.5).

## 5. Architecture

```
 Host SPI ─► Loader ─► Program RAM + Config shift-chain
                                   │
   16 input pins ─► sync + glitch filter ─┬──────────────► Core (1 ctx) ◄── RX FIFO
                                          │  (bypass)      │ PIO-style ops   ▲
                                          ▼                │ ALU, shift,     │ {class, ts}
                         pin-select (4 pins) + edge/since-edge features      │
                                          ▼                │ CRC16, timers   │
                                     Reservoir (16 nodes) ─► Readout ─► Stabilizer
                                                           │
   15 output pins ◄─ pin ownership mux ◄── TX engine ◄── TX table ◄── TX FIFO ◄─┘ (core / bit-stream)
                        ▲ (core direct drive + OE)
```

### 5.1 Core (Tier 1)

- 16-bit fixed instructions, **128 words** (64 fallback), single context.
- PIO-style ops: wait on pin/cycles/**timeout**, set/clear/direction/OE, in/out shift, mov, branch on pin/counter/shift-count/FIFO/class, jmp/call-lite. Per-instruction **delay field** for exact cycle spacing of bit-banged code.
- ALU: add, sub, and/or/xor, compare, loop counters. 16-bit free-running **timestamp**, capture-on-edge.
- New ops for the symbol layer: `RXSYM` (pop event, optional timeout), `TXSYM`, `TXBYTE` (bit-stream mode), `CRC` ops, tick-divider/config select.
- Open-drain: drive 0 or release (OE low) with external pull-up. **\[VERIFY\]** pad behaviour before promising I2C compliance.

### 5.2 Symbol layer: receive (Tier 2)

1. **Input conditioning:** 2-FF synchronizers on all 16 inputs, programmable glitch filter.
2. **Tick generator:** programmable divider; one tick per `N` clocks (`N` ≥ 1).
3. **Features per tick:** 4 selectable pins × {level, edge} plus a log-quantized "ticks since last edge" (3 bits). The counter supplies exact timing so the reservoir doesn't have to count.
4. **Reservoir:** 16 nodes, 6-bit signed state, fixed random sparse topology (3 recurrent taps + 2 feature taps per node, chosen once by a seeded generator and tuned in the Python study). Programmable per-tap weight `±2^s` or 0, per-node leak shift (multi-timescale). Update: `s' = sat(s − (s >> k) + Σ w·x)`. **Fully parallel, one update per tick.** Contractive by construction, which gives fading memory and jitter tolerance. Integer arithmetic only, so it is bit-exact with the model.
5. **Readout (baseline):** quantize state to 1 bit/node (2 bits as a Tier 3 option), compare Hamming distance to **8 prototype vectors** in parallel (XOR + popcount), argmax with margin. Class 7 is reserved as "no match / unknown". Prototypes are loaded from the host **or** captured by an on-chip snapshot (Tier 3). A ternary linear readout is evaluated in the study and adopted only if the accuracy gap justifies the area.
6. **Stabilizer:** emit an event when the winning class has changed and held for `M` ticks (1 to 7). **Event = {class (3b), start-timestamp (12b)}** pushed to the **RX FIFO** (8 deep). Overflow sets a sticky flag; it never drops silently.
7. **Latency rule:** classification latency is deterministic (\~4 pipeline ticks + `M`), and timestamps record the *start* of the run, so the core can schedule exact responses. Anything that must react faster than this (for example an SPI slave's first MISO bit) uses the **bypass** path.

Classes are programmer-defined labels covering both line states (J, K, SE0, idle) and short multi-symbol markers (UART start bit, USB sync/EOP, break). Multi-symbol markers are where reservoir memory earns its place over run-length plus FSM.

### 5.3 Symbol layer: transmit (Tier 2)

- **TX table:** 8 symbols, each up to 8 ticks × 2 output pins plus per-symbol OE mask and length (\~21 bits/entry, \~170 config bits). Manchester: symbol 0 → "10", symbol 1 → "01" (half-bit per tick). UART: one tick per bit. USB: J/K/SE0 over D+/D−.
- **TX FIFO** (16 × 3b) feeds the engine; underrun flag. **Bit-stream mode** pulls bytes and maps bit value → symbol, so the core pushes bytes, not bits.
- **Pin ownership:** each output pin is owned by core-direct or TX engine (config bit). Formal property: never both.

### 5.4 CRC / LFSR unit (Tier 2)

16-bit programmable LFSR: polynomial, initial value, width ≤ 16, bit-serial. Covers CRC5, CRC15 (CAN), CRC16 (USB), parity, PRBS. Shift ops can **tap** into it automatically (no extra instruction per bit). **CRC32 is not supported**, which is one reason Ethernet FCS stays out of silicon scope.

### 5.5 Host link, config, pins

SPI-slave loader (`ui[2:0]` = SCK/CS/MOSI, `uo[0]` = MISO), sampled via synchronizers in the `clk` domain. Program RAM is volatile, so the host reloads after reset. Config registers (\~900 bits across reservoir, prototypes, TX table, pin map) form a **shift chain** loaded serially: no address decode, minimal muxes.

| Pins | Use |
| --- | --- |
| `ui[2:0]`, `uo[0]` | Host link |
| `uio[7:0]` | Bidirectional protocol pins (I2C, USB D±, CAN, 1-Wire) |
| `ui[7:3]`, `uo[7:1]` | Extra protocol in/out, debug |

## 6. Feasibility re-evaluation

### 6.1 Area (all **\[EST\]**)

| Block | Comb. cells | Flops |
| --- | --- | --- |
| Program RAM 128×16 | decode \~0.2K | **\~2,048** |
| Core + ALU + timers | 1.0-1.5K | \~150 |
| Pin sync / filter / mux | \~0.4K | \~100 |
| Reservoir (16 nodes, parallel) | 1.0-1.6K | \~100 state + \~430 config |
| Readout + stabilizer | \~0.7K | \~130-260 (prototypes) |
| RX FIFO + TX FIFO + TX table + engine | \~0.3K | \~330 |
| CRC16 | \~0.1K | \~48 |
| Loader | \~0.3K | \~50 |
| **Total** | **\~4-5K** | **\~3.3-3.6K** |

By cell count that is roughly 8-9K of the \~24K nominal budget, so cells are not the constraint. **Silicon area is**: a flop may cost several times a NAND2 **\[VERIFY from the liberty file\]**, and the template targets 60% placement density, so usable cell area may be only \~0.4 mm² of the \~0.7 mm² nominal. If flops dominate, RAM size matters most. Mitigations in order: latch/SRAM macro for program RAM; 64 words; drop Tier 3; shrink prototypes/FIFOs; the config shift chain already avoids mux overhead.

### 6.2 Timing (assumes 50 MHz, the template's default 20 ns period; actual board clock **\[VERIFY\]**)

Reservoir update is one cycle per tick; the readout is parallel and pipelined, so tick rate can approach `clk`. STA must confirm the 3-4 adder-deep path. Recommended ticks: `clk/2` to `clk/8`.

### 6.3 Protocol table

| Protocol | Path | Symbol-layer role | Core role | Clocks/bit @50 MHz | Tier / confidence |
| --- | --- | --- | --- | --- | --- |
| UART | RX via symbol layer, TX via table | Start-bit/bit-cell classification, baud-error tolerance | Framing, parity | 434 @115200; ≥16 @3M | T2 / high |
| SPI master | Bypass | none | Clock gen, shift, CS | SCK ≲10 MHz | T1 / high |
| SPI slave | Bypass | none (latency) | Edge wait, shift | SCK ≲8 MHz | T1 / medium |
| I2C | Mixed | START/STOP/bit classes (optional) | Address, ACK, stretch | 500 / 125 @100k/400k | T1-T2 / high (pads **\[VERIFY\]**) |
| JTAG / SWD | Bypass | none | TCK gen, shift | \~10-20 | T1 / high |
| PS/2 | Mixed | Optional glitch-robust edge classes | Frame, parity | \~3000 | T1-T2 / high |
| CAN | Mixed | Edge-based resync, dominant/recessive classes | Stuffing, CRC15, arbitration read-back, sample point | 50 @1M | T2 / medium (needs external transceiver) |
| USB low-speed | Symbol layer RX + TX table | J/K/SE0, sync, EOP markers | NRZI, unstuffing, CRC5/16, handshake | 33.3 @50 MHz (**32 exact @48 MHz**) | T2 / medium (levels, pull-ups **\[VERIFY\]**) |
| 10 Mbit Ethernet | Sim only | n/a | n/a | 5 | See 6.4 |

USB LS timing: 33 clocks/bit is +1.0% off nominal, inside the ±1.5% spec but tight; a 48 MHz clock gives an exact 32 clocks/bit **\[VERIFY whether the board can supply it\]**. USB budget check: one event per bit worst case leaves \~33 clocks per event at one instruction per clock; the golden model must show the receive loop (run-length, unstuff, CRC, push) fits, with the FIFO absorbing bursts.

### 6.4 Why Ethernet is analysis-only

10BASE-T has a 20 MHz half-bit rate, so 2.5 clocks per half-bit at 50 MHz, which is not an integer (40 MHz or 60 MHz would be). It also needs a PHY, transformer and driver outside the chip, a CRC32 FCS the 16-bit unit cannot compute, and ±100 ppm clock accuracy. The deliverable: a TX-table + byte-streaming simulation of a Manchester frame (host-supplied FCS) at a 40 MHz simulation clock, plus a written analysis of what silicon would need. We do not promise it on the chip.

### 6.5 Fallback that preserves the architecture

If the reservoir fails the go/no-go (G1), swap the classifier for a **windowed Δt-template / run-length classifier** behind the same symbol-event interface. The chip is still a software-defined symbol layer with a PIO-class core. Novelty drops but remains defensible, and the swap is a contained RTL change, which is why the interface comes first.

## 7. Study and verification

**Reservoir study (weeks 1-4, Python):** generate UART (±3% baud error), USB-LS-like NRZI (±1.5%, edge jitter ±1/8 bit, 6-bit stuffed runs), PS/2 and Manchester traces plus glitches, dropouts and unrelated traffic. Train readouts off-chip (prototype centroids, ridge/perceptron); quantize to hardware precision. Measure symbol accuracy, false positives, latency, and cells at matched budget against a conventional decoder (edge-timing DPLL/run-length). **Open parameters:** nodes (12/16/24), state bits, leak set, quantization (1 vs 2 bits), `M`, topology seed.

**Verification:**

- Python golden model of core and symbol layer is the single ISA reference; RTL lockstep with the model on pins, FIFO events, reservoir state.
- Directed protocol tests against independent reference models; constrained-random programs and traces with fault injection.
- **Formal** (SymbiYosys or Hardcaml tooling on the generated RTL): PC bounds; `WAIT N` exact; single pin owner; FIFOs never silently drop (flag set); reservoir saturation bounds; bounded fading-memory property.
- Gate-level run through the template's GL test; FPGA bring-up on ice40up5k.
- **AI-assisted verification:** log which tests/properties were AI-generated and how each was validated (the brief explicitly cares).
- Reservoir topology and widths come from a seeded generator, ideally in Hardcaml.

## 8. Demonstrations

1. **UART TX out of a pin, then programmable** (week 1-3), straight from the challenge's "getting started".
2. UART, SPI, I2C as firmware on the bypass path.
3. UART RX through the symbol layer under baud error and jitter, versus a conventional decoder.
4. USB-LS device-side exchange (token in, handshake out) in simulation; on silicon if electrical checks pass.
5. **New line code post-fab:** load weights for a code the silicon was never designed for (for example NEC IR or a 1-Wire-style frame) and decode/re-emit it.
6. Unknown-waveform flag (class 7) and, if Tier 3 survives, on-chip snapshot teaching.

## 9. Schedule and gates

| Weeks (dates) | Work | Gate |
| --- | --- | --- |
| 1-2 (1-14 Oct) | Resolve \[VERIFY\] items; prior-art pass; skeleton through full CI; UART TX out of a pin; synthesize core + RAM variants (64/128, flops vs latch/macro) | **G0 (14 Oct):** area/RAM decision, 6x4 confirmed, CI green |
| 2-4 (8-28 Oct) | Golden model, assembler; reservoir study in Python | **G1 (28 Oct): reservoir go/no-go** |
| 5-8 (29 Oct-25 Nov) | Core RTL, loader, bypass protocols; symbol layer RTL (or fallback classifier) |  |
| 9 (by 2 Dec) | **G2:** feature freeze, lockstep passing, synthesis within budget | **G2 (2 Dec)** |
| 10-12 (3-23 Dec) | Formal, random tests, full LibreLane, STA, gate-level sim, FPGA | **G3 (23 Dec):** timing/area closure |
| 13-14 (24 Dec-4 Jan) | Demos, docs (`docs/info.md`, README, pinout in `info.yaml`) | Freeze **4 Jan** |
| 15-16 (5-18 Jan) | Buffer for precheck/GL failures; submit well before 18 Jan |  |

**G1 criteria (set exact thresholds as a team in week 1):** *Go* if the 16-24 node reservoir meets the accuracy target (proposed ≥99% symbol accuracy at the stated jitter) on ≥2 of 3 target codes within \~2K cells. *Partial*: use the reservoir for passing codes, bypass for the rest. *No-go*: swap to the fallback classifier (6.5) and re-pitch as a software-defined symbol layer. Holiday weeks are slack-prone, so assume reduced throughput from 24 Dec.

## 10. Risks

1. **Flop-heavy area** (RAM + \~900 config bits). Mitigation: G0 decision, latch/macro RAM, 64 words.
2. **Reservoir phase memory** over long identical-bit runs. Mitigation: edge/"since-last-edge" counter input, G1 gate, fallback.
3. **Latency of the symbol layer** vs fast responses. Mitigation: timestamps, bypass for tight slaves.
4. **Pad electrical limits** (I2C pull-ups, USB levels). Mitigation: verify at G0, state exactly what is supported.
5. **Timing closure** at 50 MHz. Mitigation: pipeline readout, conservative tick dividers.
6. **Scope creep** back toward analyzer/AI chip. Mitigation: guardrails, tiers, cut order.
7. **Late CI surprises.** Mitigation: skeleton through full CI in week 1.

## 11. Open questions and owners

1. Hardcaml or Verilog as primary source? Anyone with Hardcaml experience?
2. FPGA board and Tiny Tapeout dev board available?
3. Can the board supply 48 MHz (or another integer-friendly clock)?
4. Hero stretch demo: USB-LS or CAN?
5. Owners to assign: ISA/golden model, core RTL, symbol layer + study, verification/formal, toolchain, area/PnR.

## 12. Claims policy

**We can say:** firmware-programmable protocol machine; deterministic, bit-exact, reservoir-based symbol layer loadable with new line codes after fabrication; measured comparison against a conventional front end; open toolchain and verification.

**We must not say:** the chip understands or learns arbitrary protocols; on-chip training; it beats FSMs/DPLLs; any clock frequency before post-route STA; I2C or USB electrical compliance, or Ethernet on silicon, before they are demonstrated.