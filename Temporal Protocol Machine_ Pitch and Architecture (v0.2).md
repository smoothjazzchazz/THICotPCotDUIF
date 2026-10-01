# Temporal Protocol Machine: Pitch and Architecture (v0.2)

**Status:** working draft for team review. Numbers marked **\[EST\]** are back-of-envelope and must be replaced by synthesis results. Items marked **\[VERIFY\]** are assumptions about Tiny Tapeout / IHP that nobody has yet confirmed against current docs.

**Competition deadline:** 18 Jan 2027. **Target:** IHP CMOS5L via Tiny Tapeout, March 2027 shuttle, 6x4 tiles (8x4 may become available).

---

## 1. One-paragraph pitch

An open-source, post-fabrication-programmable protocol machine in the PIO/PRU lineage. UART, SPI and I2C run as firmware on one small deterministic core, with no protocol-specific hardware. Beyond what PIO offers, it adds (a) a cycle-accurate timestamp and timeout facility, (b) a small number of hardware contexts so independent protocols run concurrently, and (c) a compact **temporal matcher**: a tiny digital liquid-state reservoir with on-chip "teach by example" snapshots and tolerance-based matching, queried by the program through ordinary branch instructions. The matcher is evaluated against a cheaper windowed-template baseline, and we report the result honestly whichever way it goes.

## 2. Fit with the competition brief

| Brief requirement | How we meet it |
| --- | --- |
| Tiny CPU with ISA for pins, timing, counting | Core is the foundation (Tier 1). Reservoir is an optional-to-use coprocessor (Tier 2). |
| No fixed UART/SPI/I2C blocks | Silicon knows pins, edges, time, bits, registers. Protocols are programs. |
| Reprogrammable after fabrication | Program RAM loaded over a host link; reservoir weights and templates are loadable. |
| "Consider what you'd do differently" from PIO/PRU | Timestamps, timeouts, contexts, ALU-lite, temporal matcher (section 5). |
| "Show us something we haven't thought of" | On-chip teach-and-match of jittered waveforms, with a measured comparison against a conventional baseline. |
| Open source | Apache-2.0 (template LICENSE), RTL generator, assembler, models, tests, all public. |
| Verification emphasis | Golden model, RTL-vs-model lockstep, constrained-random, formal properties (section 8). |
| Start with UART, SPI, I2C; stretch goals | Section 9. |

**Judging risk to manage:** a judge must see "programmable protocol machine" first and "interesting extra" second. Never lead a demo or README with the reservoir.

## 3. Scope guardrails

In scope: the core, timing, GPIO, program memory, host loader, reservoir/matcher, assembler, models, verification.

Out of scope as primary goals: general neural compute, logic-analyzer features, large trace storage, autonomous protocol discovery, USB/Ethernet PHY. A small pre-trigger ring buffer is a **Tier 3 optional** feature, cut first if area is tight.

**Rule:** the reservoir never drives pins. It only produces flags and a score that the program may branch on, so pin behaviour stays deterministic.

## 4. Physical and flow constraints (from the project template)

- Top module must be named `tt_um_<unique>`. Ports: `ui_in[7:0]` (inputs), `uo_out[7:0]` (outputs), `uio_in/out/oe[7:0]` (bidirectional with output-enable), `ena`, `clk`, `rst_n`. That is **24 usable IOs**, 8 of them bidirectional.
- `info.yaml`: set tiles to `6x4` as the challenge instructs. **\[VERIFY\]** The template's comment lists valid sizes only up to `8x2` and cites \~167x108 µm per tile, while the challenge says 6x4 and \~200x150 µm per tile (\~0.7 mm² nominal). Confirm with the organisers or Tiny Tapeout docs that `6x4` validates in the CMOS5L flow.
- Default `src/config.json`: `CLOCK_PERIOD` = 20 ns (50 MHz), placement density 60%. The file says not to edit below the marked line. Treat 50 MHz as a ceiling for timing closure, not a given. Do not claim a clock frequency until post-route STA passes.
- CI already in the template: cocotb tests on Icarus (`cocotb==2.0.1`), GDS build with LibreLane, precheck, **gate-level test**, and an optional ice40up5k FPGA workflow. Our tests must pass in this CI, so every design decision must survive gate-level simulation.
- PDK: `ihp-sg13cmos5l`.
- Hardcaml: `info.yaml` has a `language` field. The flow consumes Verilog in `src/`, so commit the **generated** Verilog and the generator source, and document the regeneration command.
- **\[VERIFY\]** Pad electrical behaviour: IO voltage, drive strength, whether internal pull-ups exist, and whether `uio_oe` toggling gives usable open-drain behaviour. I2C needs external pull-ups. Do not promise I2C electrical compliance until confirmed.
- **\[VERIFY\]** Which SRAM/latch-memory macros or examples exist for CMOS5L at Tiny Tapeout, their sizes and timing, and whether they fit our tile geometry.

## 5. Architecture

### 5.1 Block diagram

```
 Host SPI link ──► Loader ──► Program RAM ─┐
                              Config RAM ──┼─► (weights, templates, pin map)
                                           ▼
        ┌─────────────── Core (N contexts, barrel-scheduled) ───────────────┐
        │  fetch/decode · ALU-lite · shift regs · counters · timestamp      │
        └───────┬──────────────────┬───────────────────────┬────────────────┘
                │                  │                       │
          Pin scheduler       Edge/timestamp          Event FIFO
        (timed drive/OE)      capture + sync              │
                │                  │                       ▼
                ▼                  │              Reservoir + matcher
        Pad control (uio) ◄────────┘             (flags/score back to core)
```

### 5.2 Core (Tier 1, mandatory)

Proposal **\[EST\]**:

- **16-bit fixed-width instructions**, 128 to 256 words of program RAM shared across contexts.
- **Contexts:** 2 to 4, barrel-scheduled, each with its own PC, a couple of shift registers, 2 counters and a status flags set. Tradeoff to document: with N contexts, each context issues once per N clocks, so single-context timing resolution is N clock cycles unless a timed-output mechanism compensates (next bullet). **Decide N from synthesis and the fastest protocol we want.**
- **Timed pin scheduler:** an output op carries a cycle delay and is released by the scheduler on an exact clock edge, independent of instruction slot. This decouples pin timing resolution from instruction rate and is the main answer to "barrel threading blurs timing."
- **Input handling:** 2-FF synchronizers on every input, optional glitch filter (programmable N-cycle stability), per-pin edge detect.
- **Timestamp register:** free-running counter, readable by the program, plus latched capture on a chosen pin edge. **WAIT-with-timeout** (wait for pin condition or N cycles, branch on which fired). Both are cheap and PIO has neither.
- **Instruction groups:** WAIT (pin/cycles/timeout), SET/CLR pin, DIR/OE control, IN/OUT shift, MOV, small ALU (add, sub, and/or/xor, compare), conditional branch (pin, counter zero, shift-count, reservoir flag), JMP/CALL-lite, context sync/yield, reservoir ops.
- **Open-drain emulation:** drive 0 or release (OE low) with an external pull-up. Clock stretching needs "release then wait for pin high," covered by WAIT.

### 5.3 Temporal matcher (Tier 2, the differentiator)

**Event input.** On each qualifying edge, the capture logic emits `{pin_id (3b), edge (1b), Δt_class (3b)}` where Δt is log-quantized from the timestamp delta. The program may also inject software events, for example per-bit markers.

**Reservoir.** 16 nodes initially (scale to 24 or 32 only if synthesis allows), 6-bit signed state each, fan-in 3 with **ternary weights** (-1, 0, +1) plus a small input-injection map.

Node update, a **leaky saturating accumulator** (contractive, fading memory):

```
s' = sat( s - (s >> k) + Σ w_i · x_i )
```

Rationale: XOR/LFSR-style updates give hash-like avalanche behaviour, where a one-bit difference diverges forever. That is the opposite of what we need for jitter tolerance. A reservoir needs the echo-state property, meaning similar histories give similar states. Any XOR-style nonlinearity is limited to the readout or to a single sparse term.

**Execution.** Time-multiplexed through one small datapath, one node per cycle, so \~16 to 20 cycles per event update **\[EST\]**. It runs behind the core via the event FIFO. Because edges can arrive faster than updates, define overflow behaviour explicitly (saturating overflow flag, no silent drops).

**Readout (deterministic, no host training required):**

- Quantize each node to 1 bit (sign) to form a 16-bit state vector.
- 4 to 8 template slots, each holding a 16-bit vector (optionally with a care-mask).
- `RES_SNAP k`: copy the current state vector into slot k (teach by example).
- `RES_MATCH k, tol`: set a flag if Hamming distance to slot k is at most `tol`.
- `RES_RESET`: clear reservoir state.
- `RES_SYNC`: stall the context until the FIFO is drained, so a match result is aligned to a known point in the stream. **This is required for determinism**: the program must never read the flag while updates are still in flight unless it explicitly means to.

All arithmetic is fixed-point integer, so the RTL is bit-exact against the golden model.

**Programmability.** Weights, connectivity and injection map live in a small config RAM loaded alongside the program, about 300 to 500 bits **\[EST\]** (16 nodes x 3 taps x \~6 bits plus injection map). Templates are runtime data, set either by `RES_SNAP` or by host load.

### 5.4 Host link and boot

Program RAM is volatile, so the host loads it after every reset. Proposal: a small SPI-slave loader on the dedicated input/output pins (SCK, CS, MOSI on `ui`, MISO on `uo`), with the loader clocked synchronously: sample SCK through a synchronizer in the `clk` domain rather than using it as a clock. The loader also provides read-back of status, timestamps and optional captured data.

### 5.5 Pin budget (proposal)

| Pins | Use |
| --- | --- |
| `ui[2:0]`, `uo[0]` | Host link: SCK, CS, MOSI / MISO |
| `uio[7:0]` | Protocol pins needing bidirectional control (I2C SDA/SCL, SPI, UART, 1-Wire) |
| `ui[7:3]`, `uo[7:1]` | Additional protocol inputs and outputs, status/debug |

Pin-to-context mapping is configurable in the config RAM. Verify no pin is driven by two contexts at once (formal property, section 8).

## 6. Area plan

Challenge guidance: about 1K logic cells per tile, so **\~24K cells** for 6x4. All numbers below are **\[EST\]**, to be replaced after the first synthesis run.

| Block | Rough size | Notes |
| --- | --- | --- |
| Program RAM, 256 x 16 bit | 4,096 bits | Flop-based is likely the largest single block. Evaluate latch-based or macro SRAM **\[VERIFY\]**. Fall back to 128 words. |
| Core + N contexts + ALU | low thousands of cells | Scales with context count. |
| Pin scheduler, sync, capture | \~1K |  |
| Reservoir + matcher | low thousands of cells | State \~100 bits, templates \~64 to 128 bits, config \~400 bits. |
| Loader, config RAM, misc | \~1K |  |
| Clock tree, routing slack | reserve ≥25% | Post-route congestion is a real risk. |

**Fallback order if over budget:** (1) drop ring buffer, (2) shrink reservoir to 12 to 16 nodes, (3) reduce contexts to 2, (4) shrink program RAM to 128 words, (5) trim ISA. Never cut the core's generality to save a secondary feature.

**First action:** synthesize core-only, then each candidate memory, then the reservoir, before committing sizes.

## 7. Research claim and baseline study

**Hypothesis (not a claim):** a small contractive reservoir gives better jitter-tolerant temporal matching per unit area than simpler alternatives.

**Baseline to beat:** a **windowed template matcher**, a shift register of the last K quantized Δt values with masked/tolerant compare. It is far cheaper than a reservoir, and a skeptical judge will ask for it.

**Also compare:** n-gram hash against a small seen-sequence table (novelty-style detection).

**Method:**

1. Python golden models of the reservoir and the baselines.
2. Trace generator: clean pulse-coded waveforms (IR remote style, 1-Wire/DHT-style, Manchester) plus jitter, edge noise, missing/extra edges, and unrelated traffic.
3. At matched cell budget, report detection rate, false-positive rate, latency, jitter tolerance and synthesized cells.

**Decision rule:** if the reservoir loses, ship the windowed matcher in its place (or alongside) and publish the comparison. If it wins, keep it. Both outcomes are legitimate deliverables, and the architecture is designed so the matcher block is swappable.

**Honest framing:** a reservoir is poor at exact counting ("exactly 8 clocks"), which is the core's job. The matcher targets fuzzy, timing-tolerant recognition. "Learning" here means on-chip snapshot of a template, not on-chip gradient training.

## 8. Verification plan

- **Golden model** of core and matcher (Python, or OCaml/Hardcaml-based if the team prefers). Single source of truth for the ISA.
- **Lockstep RTL vs model:** same program and input trace, compare pin outputs cycle by cycle and reservoir state per event.
- **Directed protocol tests:** UART, SPI (all four modes), I2C (start/stop, ACK/NACK, clock stretch) against independent reference models.
- **Constrained-random:** random valid programs and random input traces, with fault injection (glitches, jitter, truncated frames).
- **Formal (SymbiYosys or Hardcaml's formal/SAT tooling on emitted RTL):**
  - PC always within program range; no illegal-opcode lockup.
  - `WAIT N` releases after exactly N cycles.
  - No pin driven by two contexts simultaneously.
  - FIFO never silently drops; overflow flag is set.
  - Reservoir saturation bounds hold; state depends only on the last N events with the chosen leak (fading-memory property, at least for bounded checks).
- **Gate-level:** run the template's GL test on the hardened netlist. Include a reset-and-load sequence.
- **FPGA:** ice40up5k workflow exists in the template. Check LUT/BRAM fit early, since memory inference may differ from the ASIC.
- **AI-assisted verification:** log which tests/properties were AI-generated and how each was validated. The brief explicitly asks for this.

## 9. Demonstration plan

**Required (Tier 1):**

1. UART TX and RX at programmable baud (programs, not hardware).
2. SPI master and slave, modes 0 to 3.
3. I2C master with ACK/NACK; clock stretching if pad behaviour allows.
4. Two protocols running concurrently on different contexts.

**Differentiator demo (Tier 2):** teach the chip a pulse-coded waveform (IR remote button or 1-Wire/DHT-style frame) with `RES_SNAP`, then recognize noisy and jittered repeats with a branch on `RES_MATCH`, and have the program respond or re-emit the frame. Run the same task with the windowed baseline and show the numbers.

**Stretch (only if the same ISA expresses them without hardware additions):** JTAG, SWD, PS/2, then CAN. Low-speed USB and 10 Mbit Ethernet are likely beyond the clock/IO budget and should be framed as analysis, not promises.

## 10. Toolchain deliverables

- Assembler for the 16-bit ISA (macro support, labels, delay annotations).
- Python simulator that is also the golden model.
- Optional thin protocol DSL compiling to assembly. Defer until the assembler and example programs are stable.
- Host loader script (SPI over a Raspberry Pi/RP2040/FT232 on the Tiny Tapeout board).
- Reservoir config tool: given template waveforms, generate weights and quantization parameters.

## 11. Schedule (backwards from 18 Jan 2027)

| Weeks | Milestone |
| --- | --- |
| 1 to 2 | Resolve all \[VERIFY\] items. Choose language/toolchain (Hardcaml vs Verilog). Draft ISA v0. |
| 2 to 5 | Golden model + assembler. Core RTL. UART/SPI/I2C as programs in simulation. |
| 3 to 6 | Reservoir/baseline study in Python. First synthesis of core and memory options. |
| 6 to 9 | Matcher RTL. Lockstep and constrained-random harness. Formal properties. |
| 9 to 12 | Full LibreLane run, timing/area closure, gate-level sim, FPGA bring-up. |
| 12 to 14 | Demos, docs (`docs/info.md`, README), pinout in `info.yaml`. |
| 14 to 15 | Freeze, buffer for failed precheck or timing. Submit before 18 Jan. |

Fall back to the baseline matcher at week 9 if the reservoir is not clearly winning by then.

## 12. Top risks

1. **Program memory area** may consume most of the die. Mitigation: early synthesis, 128-word fallback, memory macro/latch investigation.
2. **Timing closure** at the chosen clock after place and route. Mitigation: choose a conservative clock, keep critical paths short, pipeline the reservoir.
3. **Barrel threading vs timing resolution.** Mitigation: timed pin scheduler; allow N = 1 or 2 if protocols demand.
4. **Pad electrical limits** may rule out true I2C. Mitigation: verify early, document exactly what is and isn't supported.
5. **Reservoir loses to the baseline.** Mitigation: swappable block, publish the result.
6. **Judge perception** of drift toward analyzer/AI chip. Mitigation: core-first messaging, section 3 guardrails.
7. **Gate-level or precheck failures** found late. Mitigation: run the full CI flow from the first week on a skeleton design.

## 13. Open questions for the team

1. Hardcaml or Verilog as the primary source? Anyone with Hardcaml experience?
2. Do we have an FPGA board (ice40up5k flow or other) and a Tiny Tapeout dev board?
3. Which single non-trivial protocol do we want as the "hero" stretch demo?
4. What is the fastest protocol clock we commit to supporting, which drives context count and scheduler design?
5. Who owns: ISA/golden model, RTL, verification, toolchain, baseline study?

## 14. Claims policy

**We can say:** a general-purpose, firmware-programmable protocol machine; an on-chip teachable temporal matcher with deterministic, bit-exact behaviour; a measured comparison against a conventional baseline.

**We must not say:** the chip "understands" or "learns" arbitrary protocols; the reservoir beats FSMs on UART/SPI/I2C; any frequency, I2C compliance, USB or Ethernet support before it is demonstrated.