# Architecture contract

Restated from v0.3 sections 4 and 5, as amended by v0.31. Area totals, cell counts, and clock rates in v0.3 section 6 and v0.31 section 8 are **[EST]** or **[VERIFY]** and are not repeated here. See [authority.md](authority.md).

**The core never touches a pin.** All input reaches the core as symbol events. All output leaves as symbols through the TX table. There is no pin-level bypass wire; "raw GPIO" is a degenerate symbol-layer configuration (a weight file), not a path around the symbol layer.

## Tiers

- **Tier 1 (mandatory):** single-context core, program RAM, host loader, **the symbol-layer datapath in degenerate (pass-through) configuration**, TX table. UART, SPI, and I2C are weight files plus firmware. No protocol-specific hardware.
- **Tier 2 (integral):** trained reservoir configurations, dual-classifier operation, reflex table, CRC16 unit, byte-streaming modes, RX/TX FIFO depths as specified.
- **Tier 3 (cut first):** second context, on-chip snapshot teaching, 2-bit state quantization, linear readout, 256-word RAM, ring buffer.

The design must fit 6×4 tiles. It must not depend on 8×4. If 8×4 becomes available, spend it on RAM size or contexts, not on new core features.

## Guardrails

- The reservoir never drives pins. It emits symbols only. The core and the reflex table decide.
- **A formally verified pass-through configuration always exists.** The symbol layer is the only pin interface.
- The reflex table is configuration, not a learned structure. Reflexes are armed and disarmed by the core.
- No analyzer features. No general neural-network claims.
- The symbol-event interface is the contract. Both classifiers sit behind it (v0.31 section 6).

## Symbol event

An event is `{class (3 bits), start-timestamp (12 bits)}`.

- Eight classes. Class 7 is reserved as no match / unknown.
- The stabilizer emits when the winning class has changed and held for `M` ticks, `M` from 1 to 7.
- The timestamp is the start of that run, not the emit time.
- Latency is deterministic: about 4 pipeline ticks plus `M`. The "about 4" figure is the v0.3 pipeline rule, not a measured STA result.
- RX FIFO is 8 deep. Overflow sets a sticky flag. Events are never dropped silently.

## Core (Tier 1)

- 16-bit fixed instructions. Program RAM is 128 words default, 64 fallback. One context.
- **No pin-level I/O ops.** Wait-on-pin, set/clear-pin, direction, and branch-on-pin are removed (v0.31 section 3).
- Operations: wait on class event, cycles, or timeout; shift in and out; mov; branch on class, counter, shift count, FIFO status, or CRC state; jmp and call-lite; `ARM`/`DISARM` for reflex-table entries.
- Per-instruction delay field for exact cycle spacing.
- ALU: add, sub, and, or, xor, compare, loop counters.
- 16-bit free-running timestamp. Capture on class event.
- Symbol-layer operations: `RXSYM` (pop event, optional timeout), `TXSYM`, `TXBYTE` (bit-stream mode), CRC operations, tick-divider and config select.
- Open-drain is expressed as TX-table symbols with per-symbol OE masks: drive 0, or release, with an external pull-up. Whether the pad does this is **[VERIFY]**. Do not promise I2C electrical compliance.

## Receive path (Tier 2)

1. 2-FF synchronizers on all 16 inputs. Programmable glitch filter.
2. Tick generator: one tick per `N` clocks, `N` ≥ 1.
3. Features per tick: 4 selectable pins, each contributing level and edge, plus a log-quantized ticks-since-last-edge (3 bits). The counter carries exact timing. The reservoir does not count it.
   **Open (v0.31 section 4):** with the bypass gone this window is the chip's only receive aperture. Default answer is per-lane pin selects; literal level/edge classes are the alternative. Decide in the golden model before G1. Firmware plans assume per-lane selects until then.
4. Reservoir: 16 nodes, 6-bit signed state. Fixed random sparse topology, chosen once by a seeded generator and tuned in the Python study: 3 recurrent taps and 2 feature taps per node. Per-tap weight `±2^s` or 0. Per-node leak shift. Update, fully parallel, one update per tick:

   `s' = sat(s − (s >> k) + Σ w·x)`

   Integer only, so the RTL is bit-exact with the model. Contractive by construction (fading memory).
5. Baseline readout: quantize each node to 1 bit (2 bits is Tier 3). Hamming distance to 8 prototype vectors in parallel (XOR and popcount). Argmax with margin. Prototypes load from the host. On-chip snapshot capture is Tier 3. A ternary linear readout is a study option, adopted only if the accuracy gap justifies the area.
6. **Second classifier (v0.31):** a windowed Δt-template / run-length classifier sits beside the reservoir. A config selection chooses which front end feeds the stabilizer; a debug mode exposes both for disagreement capture (class 7 plus a sticky disagree flag).
7. Stabilizer and RX FIFO, as in the symbol-event contract.

A **degenerate configuration** (pass-through feature taps, zeroed recurrence, maximal leak, level/edge prototypes) makes the symbol layer act as a synchronizer plus edge detector with fixed small latency. That configuration is Tier 1 and gets a formal equivalence proof against a reference FSM. "Bypass" means loading it, nothing else.

Classes are programmer-defined. They may be line states (J, K, SE0, idle) or short multi-symbol markers (UART start bit, USB sync or EOP, break).

## Transmit path (TX table Tier 1; reflex and byte-stream Tier 2)

- TX table: 8 symbols. Each symbol is up to 8 ticks by 2 output pins, plus a per-symbol output-enable mask and a length.
- TX FIFO: 16 entries by 3 bits. Underrun flag.
- Bit-stream mode: the core pushes bytes. A bit value maps to a symbol.
- **Reflex table (v0.31 section 5):** 8 entries **[EST]**, each a match class, an emit symbol, an armed bit, and a one-shot/continuous bit. An armed entry fires on its stabilizer event and queues its symbol ahead of the core's TX stream, with no core instructions in the loop.
- **The TX engine always owns output pins.** Core-direct drive and the pin-ownership mux do not exist. Formal property: a reflex emission and a core `TXSYM` are serialized; no symbol drops silently (flag on conflict); reflex latency from stabilizer event to first output tick is a constant.

## CRC / LFSR (Tier 2)

16-bit programmable LFSR. Polynomial, initial value, width ≤ 16, bit-serial. Covers CRC5, CRC15 (CAN), CRC16 (USB), parity, and PRBS. Shift operations may tap it, with no extra instruction per bit. CRC32 is not supported. That is one reason Ethernet FCS is outside silicon scope.

## Host, config, pins

SPI-slave loader. Sampled through synchronizers in the `clk` domain. Program RAM is volatile. The host reloads it after reset. Config (reservoir, prototypes, TX table, pin map) is a shift chain: serial load, no address decode.

Pin assignment from v0.3 section 5.5, with `ui[2:0] = SCK/CS/MOSI` applied from the high index:

- `ui[2]` SCK, `ui[1]` CS, `ui[0]` MOSI, `uo[0]` MISO — host link
- `uio[7:0]` — bidirectional protocol pins (I2C, USB D±, CAN, 1-Wire). No bit in this range is assigned to a named protocol.
- `ui[7:3]`, `uo[7:1]` — extra protocol in, extra protocol out, and debug. No bit in these ranges is assigned further.

## G1 outcome handling (v0.31 section 6, replacing v0.3 section 6.5)

Both classifiers are on die regardless of G1. A G1 no-go means the conventional classifier becomes the primary front end and the reservoir ships as the research configuration, reported honestly. The silicon is the same either way; only the recommended weight files differ. Do not build a second pin interface under any outcome.

## Not decided

From v0.3 section 11 — do not encode an answer in the tree:

- Hardcaml or Verilog as the primary source
- which FPGA board and whether a Tiny Tapeout dev board is available
- whether the board can supply 48 MHz
- hero stretch demo beyond the line-code hero: USB low-speed or CAN
- named owners per workstream

From v0.31 — decided in the golden model before G1, not in RTL:

- receive aperture: per-lane pin selects (default) or literal level/edge classes
