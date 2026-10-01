<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

An open-source waveform translator. After fabrication, a host loads weights and tables and the same pins speak that file, within the chip's timing and pin limits. UART, SPI, and I2C are further files: they have to work, and the chip is not built to be the best decoder of them. On receive, a small digital reservoir, with weights trained off-chip, sits beside an edge-and-run-length listener. Both emit timestamped symbols. A deterministic core consumes those symbols. A transmit table and a reflex table turn symbols back into pin waveforms. Pattern 7 means the wiggle matched nothing that was loaded. Node state can be read while a shape arrives.

The core never touches a pin. All input arrives as symbol events and all output leaves as symbols through the transmit table; the instruction set has no pin-level operations. There is no pin-level bypass: a degenerate symbol-layer configuration — pass-through taps, zeroed recurrence, level and edge prototypes — makes the layer act as a synchronizer plus edge detector, so plain GPIO behaviour is itself a loadable configuration through the same silicon. The reservoir never drives pins. It emits symbols only, and the core and the reflex table decide. There is no analyzer feature and no general neural-network claim.

Tier 1 is mandatory: a single-context core, timestamps and timeouts, program RAM, a host loader, the symbol-layer datapath in its degenerate configuration, and the transmit table. It delivers UART, SPI, and I2C as weight files plus firmware. Tier 2 is the novelty and is integral: trained reservoir configurations, dual-classifier operation, the reflex table, the RX and TX FIFOs at full depth, a CRC16 unit, and byte-streaming modes. Tier 3 is cut first: a second context, on-chip snapshot teaching, 2-bit state quantization, a linear readout, 256-word RAM, and a ring buffer.

The core uses 16-bit fixed instructions, 128 words by default (64 as fallback), and a single context. Operations wait on a class event, on cycles, or on a timeout; shift in and out; move; branch on a class, a counter, the shift count, FIFO status, or CRC state; jump or call-lite; and arm or disarm reflex-table entries. A per-instruction delay field spaces instruction sequences by an exact cycle count. The ALU adds, subtracts, and combines with and, or, and xor; it compares and provides loop counters. A 16-bit free-running timestamp captures on a class event. Symbol-layer operations are `RXSYM` (pop an event, optional timeout), `TXSYM`, `TXBYTE` (bit-stream mode), CRC operations, and tick-divider or config select. Open-drain is expressed as transmit-table symbols with per-symbol output-enable masks: drive 0, or release, with an external pull-up. Pad behaviour for I2C is not yet verified.

The receive symbol layer conditions all 16 inputs with 2-FF synchronizers and a programmable glitch filter. A tick generator divides the clock by a programmable `N` (`N` ≥ 1). Each tick, four selectable pins contribute level and edge, plus a log-quantized ticks-since-last-edge value (3 bits). The reservoir has 16 nodes, 6-bit signed state, and a fixed random sparse topology: 3 recurrent taps and 2 feature taps per node, chosen once by a seeded generator. Each tap weight is `±2^s` or 0. Each node has a leak shift. The update is `s' = sat(s − (s >> k) + Σ w·x)`, fully parallel, one update per tick. Integer arithmetic only. The baseline readout quantizes state to 1 bit per node and compares Hamming distance to 8 prototype vectors in parallel (XOR and popcount), then takes argmax with a margin. Class 7 is reserved as no match / unknown. Prototypes are loaded from the host. A stabilizer emits an event when the winning class has changed and held for `M` ticks (1 to 7). An event is `{class (3 bits), start-timestamp (12 bits)}`, pushed to an RX FIFO 8 deep. Overflow sets a sticky flag and never drops silently. Classification latency is deterministic (about 4 pipeline ticks plus `M`), and the timestamp records the start of the run. A conventional windowed-timing classifier sits beside the reservoir behind the same interface; a configuration selection chooses which one feeds the stabilizer, and a debug mode captures disagreements between them.

The transmit side has a TX table of 8 symbols, each up to 8 ticks by 2 output pins, plus a per-symbol output-enable mask and length. A TX FIFO (16 by 3 bits) feeds the engine and has an underrun flag. Bit-stream mode pulls bytes and maps a bit value to a symbol. A reflex table maps a received class directly to a transmitted symbol with no core instructions in the loop; the core arms and disarms its entries, and responses that must beat classification latency use it. The TX engine always owns the output pins; a reflex emission and a core-queued symbol are serialized, and a conflict sets a flag rather than dropping silently.

A 16-bit programmable LFSR covers CRC5, CRC15 (CAN), CRC16 (USB), parity, and PRBS. Polynomial, initial value, and width up to 16 are programmable, bit-serial. Shift operations can tap it. CRC32 is not supported.

The host link is an SPI slave: `ui[2:0]` are SCK, CS, and MOSI, and `uo[0]` is MISO, sampled through synchronizers in the `clk` domain. Program RAM is volatile and is reloaded after reset. Config registers form a shift chain loaded serially.

The checked-in top module is still the Tiny Tapeout template adder. Tier 1 replaces it.

## How to test

The Python golden model of the core and the symbol layer is the single ISA reference. RTL lockstep compares the model and the RTL on pins, FIFO events, and reservoir state. Directed protocol tests run against independent reference models. Constrained-random programs and traces include fault injection.

Formal checks, with SymbiYosys or Hardcaml tooling on generated RTL: program-counter bounds; `WAIT N` is exact; reflex and core transmissions are serialized with no silent drop; FIFOs never silently drop (the flag is set); reservoir saturation bounds; a bounded fading-memory property; and an equivalence check that the degenerate pass-through configuration matches a reference synchronizer-plus-edge-detector state machine. A gate-level run uses the template gate-level test. FPGA bring-up uses the template ice40up5k flow. Tests or properties that are AI-generated are logged with how each was validated.

Intended demonstrations, in this order. UART transmit out of a pin is the first engineering milestone, not the first scene:

1. A temporal line code loaded as weights plus a transmit table, decoded and re-emitted.
2. Pattern 7 on a wiggle outside the loaded set.
3. Reservoir node state read out while that shape arrives.
4. A sticky disagreement between the reservoir and the edge listener.
5. A reflex exchange (an I2C ACK or an SPI slave response) with the program counter unchanged during the reply.
6. UART, then SPI, then I2C, each as another loaded file.
7. The boring settings file checked against a small edge detector.
8. A USB low-speed exchange in simulation, and on silicon only if the electrical checks pass. An on-chip prototype snapshot only if area remains.

These checks are the method. They are not results. The template adder is what is in the repository until Tier 1 lands.

## External hardware

A host SPI master loads program RAM and the config shift chain. The chip is the SPI slave (`ui[2]` SCK, `ui[1]` CS, `ui[0]` MOSI, `uo[0]` MISO).

Open-drain use needs an external pull-up. Pad behaviour for that mode is not yet verified.

CAN needs an external transceiver.

USB levels and pull-ups are not yet verified, so no USB part is listed. Ethernet is analysis and simulation only, so no Ethernet PHY, transformer, or driver is part of the chip.
