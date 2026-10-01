# Start here

This is the plain-language map of the chip. Read it before the pitch documents. If this file and [architecture.md](architecture.md) disagree, the architecture page wins, and v0.31 wins over v0.3. Numbers in the specs marked **[EST]** are guesses. Items marked **[VERIFY]** are not checked yet. This page does not turn either into facts.

You do not need to have taped out a chip to start. You do need to be able to explain each block below in your own words before you merge code an agent wrote for that block.

## The picture, in plain English

Think of the chip as a building with one entrance, one exit, and a loading dock. Nothing else opens onto the street.

The street is the pins. Voltage on a wire is not a message. It is a wiggle: high, low, and edges, stretched out in time. UART, SPI, I2C, and a made-up pulse code are different names for different wiggles.

**The entrance turns wiggling into a note.** A note is not a voltage. A note says "pattern number 2 began at time 100." There are eight pattern numbers. Number 7 means "this does not match anything we loaded." Two listeners stand at the same window and each offer a number. One listener has a short memory of the recent shape of the wiggle (the reservoir). The other is a stopwatch: it measures gaps between edges and how long the line stayed the same (the ordinary classifier). We pick one offer. We can also write down when they disagree. A note is only passed inside after the same number has held still for a few samples, so the rest of the building does not see flicker.

**The office only handles notes.** A very small program waits for a note, updates a byte or a checksum, and writes a reply note: "please send pattern number 1." The program cannot look out the window and cannot touch a pin. That is deliberate. If it could, the novel entrance would be optional.

**The exit turns a note back into wiggling.** "Send pattern 1" looks up a short script: which pins to drive, whether to let go of the wire, and for how many samples. The script player is the only thing allowed to drive outputs.

**A shortcut hallway skips the office when the reply is already known.** Example: "if pattern 3 shows up, immediately play script 5." The program arms that rule beforehand. It does not have to wake up in time. The hallway still speaks notes, not pins.

**The loading dock fills the building after every power-up.** There is no flash. A host shifts in two loads over SPI: the office's program, and the settings (which pins to watch, the reservoir's numbers, the pattern examples, the exit scripts, the shortcut rules). Power off, and it is empty again.

**Boring mode is not a side door.** Settings can make the entrance say only "the pin just went high" and "the pin just went low." Same rooms, same hallway, dull notes. That is how we still bit-bang a simple protocol without giving the program a private wire.

One sample of the whole loop:

```text
pins in
  -> make the wiggle safe to sample
  -> every N clocks, write down up to 4 pins
  -> reservoir vote   AND   stopwatch vote
  -> keep the vote only if it holds
  -> queue of notes: {pattern number, time it started}
        -> program reads a note, writes a pattern number
        -> shortcut can write a pattern number immediately
  -> script table turns that number into pin levels
  -> pins out

host SPI -> program memory and the long settings chain
```

If you can redraw that from memory, you have the topology. The rest of this file is the same picture with the real block names.

## What success is

The chip is a waveform translator. A file loaded after fabrication decides what the pins mean, within the timing and the four-pin window. UART, SPI, and I2C have to work as more files, so the assignment is covered. They are stepping stones. The chip is not trying to be the best at them.

What the submission is trying to show, in this order: a temporal shape loaded and echoed, pattern 7 on a stranger, the node values moving while that happens, the two listeners disagreeing, a reflex that answers while the program counter waits, and only then UART, SPI, and I2C. The full statement is [doctrine.md](doctrine.md).

## What the competition actually wants

Jane Street asked for an open-source chip that can **pretend to be many serial protocols**, written in firmware, after the chip is already manufactured.

A normal chip would contain a UART block, an SPI block, and an I2C block. That fails the brief. The brief wants one small processor whose instructions are good at timing, plus enough flexibility that a protocol nobody coded into the silicon can still be added later by loading new data.

They also said they care about **unusual function** and **unusual ways of designing and checking the chip**, including formal proofs, random tests, and AI-written tests that a human still checks.

Constraints that are already decided:

- Process: IHP 130 nm CMOS5L, through Tiny Tapeout.
- Start from the CMOS5L Verilog template. Do not replace it.
- Tile size in `info.yaml` is `6x4` (24 tiles). Design for that. Do not depend on a possible later 8×4.
- Open source the whole time.
- Submit by 18 January 2027. Stop adding features on 4 January 2027.
- First real milestone the announcement names: get a UART transmitter out of a pin, then make that transmitter programmable.

The template's GitHub actions already know how to simulate the design, build the chip layout (GDS), and try an FPGA build. Your job is to put a correct design in `src/` that those actions can run. You are not drawing transistors.

## The idea, in one sitting

Picture a logic analyzer and a bit-bang driver, except the "what bit did I just see?" step is programmable.

Wires do not speak UART. They wiggle. A UART start bit, an I2C START, a USB J/K pair, and a made-up infrared-style pulse train are all just patterns of highs, lows, and edges in time. A PIO or PRU (the RP2040 and TI parts the announcement mentions) can be programmed to **wiggle pins on an exact cycle**. It cannot be reprogrammed to **recognize a new wiggle** except by writing new instructions that stare at the pin.

This chip splits that job:

1. A **symbol layer** watches a few pins and says "I think this wiggle is class 2, and it started at time T."
2. A **tiny CPU** never sees the pin. It only sees those messages, and it only replies by naming a symbol to send.
3. A **transmit table** turns "send symbol 1" into the actual pin wiggle (for example Manchester 0 is high-then-low).
4. The behavior of the recognizer is **weights loaded after fabrication**, the same way firmware is loaded. A new line code is a new file, not a new chip.

The recognizer we want to be proud of is a small **liquid state machine** (a digital reservoir): a handful of integer nodes with fading memory. It is good at "this pattern, even if the edges are a little early or late." Next to it, on the same chip, sits an ordinary edge-and-run-length classifier, so we can show both answers on the same wires.

There is **no secret path around the recognizer**. Even "just read the pin level" is a boring settings file for the same hardware. That is the point. If the novel block can be switched off and the chip still speaks UART, a judge will say the novel block was optional. Here it is the only way in and the only way out.

## How a byte would move, end to end

Receive:

1. A pin wiggles.
2. Synchronizers clean up the wiggle so it is safe to sample on our clock.
3. Once every N clocks (a "tick"), the front end writes down level, edge, and "how long since the last edge" for up to four chosen pins.
4. The reservoir updates. The ordinary classifier updates. One of them is selected to vote.
5. If the vote stays the same for M ticks, a **symbol event** is pushed into a small queue: class number (3 bits, so 8 possible classes) and the time the run **started** (12 bits). Class 7 means "I don't recognize this."
6. The CPU pops that event with `RXSYM` and decides what it means (start bit, address bit, ACK, unknown).

Transmit:

1. The CPU says `TXSYM 1`, or a **reflex** says it automatically because class 3 just arrived.
2. The transmit engine looks up symbol 1 in the TX table: a short script of pin levels, output-enables, and how many ticks long it is.
3. The engine plays that script on the output pins. The CPU does not touch the pin.

Host, which is how you get the program onto the chip:

- After reset, the on-chip program memory is empty. It is ordinary registers, not flash.
- A laptop (or dev-board microcontroller) bit-bangs SPI into `ui[2]` SCK, `ui[1]` CS, `ui[0]` MOSI, and reads `uo[0]` MISO.
- That loads the program, the weights, the prototypes, the TX table, and the reflex table.
- Every power cycle, load again. That is normal for this chip.

## Each block, alone

### Symbol event

The sentence the blocks speak to each other. One event is "class C began at time T."

Why it exists: the CPU must stay deterministic. It should not guess about analog-ish wiggling. Time is attached to the **start** of the pattern, so the CPU can still schedule an exact reply even though classification takes a few ticks.

Eight classes. Class 7 is reserved for "no match." The queue (RX FIFO) holds 8 events. If it overflows, a sticky flag sets. The hardware is not allowed to throw an event away quietly.

### Input conditioning

Two flip-flops per input pin (a standard synchronizer) plus a glitch filter you can program.

Why: pins are asynchronous to `clk`. Without synchronizers, the chip can go metastable. This is the one piece of "normal digital design" that sits in front of everything else. It does not interpret protocols.

### Tick generator

Divides `clk` by N, N at least 1. The reservoir updates once per tick, not necessarily once per clock.

Why: protocols are slow compared with a chip clock. UART at 115200 baud is thousands of clocks per bit if the flow is anywhere near the template's 20 ns period setting. The tick is how we choose "how fast the recognizer thinks" without changing the CPU clock. The template period is a **flow setting**, not a measured board clock. Do not tell anyone a frequency until static timing passes after place-and-route.

### Features

Each tick, up to four pins contribute: level, edge, and a coarse "ticks since last edge."

Why: the reservoir should not spend its memory counting long strings of identical bits. A counter does that better. The reservoir spends its memory on the shape of the recent past.

Open decision, due before the G1 gate: those four pins may need to be chosen independently (chip-select while also watching data). Default plan is one mux per pin lane. Do not invent a second answer in RTL before the Python model tries it.

### Reservoir (the liquid state machine)

Sixteen nodes. Each node holds a 6-bit signed integer. The wiring between nodes is **fixed** (chosen once by a random seed, then tuned in Python). What you load later is the **weights** and the **leak**.

Each tick, every node does the same update, all at once:

`new = saturate(old - (old shifted down by k) + sum of weight times input)`

Weights are only `+2^s`, `-2^s`, or 0, so the hardware is shifts and adds, not multipliers. The leak term `old >> k` pulls the node back toward zero, which is the "fading memory." Integer only, on purpose: the Python model and the Verilog must match bit for bit.

Why it is here: a fixed state machine knows the codes you designed it for. This block can be aimed at a new code by loading numbers. It is also the part a judge cannot delete without deleting the chip's only ears.

What it does **not** do: it does not drive pins, it does not train itself, and it does not "understand protocols." Training happens on a computer. The chip only stores the result.

### Readout

Squash each node to 1 bit. Compare that 16-bit pattern to 8 stored prototype patterns (XOR, then count the differing bits). Closest prototype wins, if it wins by enough margin. Class 7 if nothing is close enough.

Why: the reservoir state is a smear of recent history. The readout turns the smear into a label the CPU can branch on. Prototypes are loaded from the host.

### Conventional classifier

A normal "measure the gap between edges / measure the run length" decoder, sitting beside the reservoir.

Why: the chip can say two things about one wire, and raise a sticky bit when those things differ. That is a feature of this machine. It is not a contest against a normal UART. If the edge listener is righter on UART, that is fine. UART was never the shape the nodes were built to own.

### Stabilizer

Waits until the winning class has held for M ticks (M is 1 to 7) before emitting the event.

Why: a classifier flickers. The CPU should see a decision, not every intermediate vote.

### Core

A very small CPU. One context (one program counter). Instructions are 16 bits. Program RAM defaults to 128 words, with 64 as the fallback if area hurts.

If you are in the CPU class: this is a toy pipeline-or-not-yet of fetch / decode / execute, an ALU (add, sub, and, or, xor, compare), a loop counter, and a program counter that must stay inside the RAM. It is **not** a general-purpose CPU. It has no load/store to a big memory. Its whole job is "when this symbol shows up, do the next protocol step, and emit the next symbol on an exact delay."

Instructions you will actually use:

- Wait for a class, or for a number of cycles, or until a timeout.
- Shift bits in and out (this is how a byte gets assembled).
- Branch on class, counter, shift count, FIFO status, or CRC.
- `RXSYM` pop an event. `TXSYM` send a symbol. `TXBYTE` send a whole byte as bits mapped to symbols.
- `ARM` / `DISARM` a reflex.
- A delay field on the instruction, so bit-banged **timing** is still exact. The CPU still owns time. It just does not own the pin.

There is no "read pin" and no "set pin" instruction. That absence is the design.

### TX table and TX engine

Eight symbols. Each symbol is a short waveform: up to 8 ticks, on up to 2 pins, plus "am I driving or releasing the pin" and a length.

Example you already know: UART can be "one tick = one bit, symbol 0 holds the line one way, symbol 1 holds it the other way." Manchester can be "symbol 0 is 10, symbol 1 is 01."

The TX FIFO holds 16 symbols waiting to play. If the engine runs out, an underrun flag sets.

The TX engine **always** owns the output pins. The CPU cannot also drive them. Two sources (a reflex and a `TXSYM`) get serialized. If they collide, a flag sets. Nothing is dropped quietly.

### Reflex table

Eight entries, each "if class X arrives and I am armed, immediately queue symbol Y." One-shot or repeating. The CPU arms them. The CPU is not in the loop when they fire.

Why: classification takes a few ticks. An SPI slave sometimes has to answer on the next edge. A reflex is the fast path that still speaks symbols. I2C ACK is the easy picture: "when you see the address-match class, emit the ACK waveform" without the CPU waking up in time.

This is configuration you load. It is not learning.

### CRC / LFSR

A 16-bit shift register with a programmable polynomial. USB, CAN, and parity need this. The shifter in the CPU can tap it so you do not spend an extra instruction per bit.

It does not do CRC32. That is one reason 10 Mbit Ethernet is a simulation writeup, not a pin on this chip.

### Loader and config chain

SPI slave, already described. Two memories from the host's point of view:

- Program RAM: the CPU instructions.
- Config chain: a long shift register of weights, leaks, prototypes, TX entries, reflex entries, and which pins the feature lanes watch. Serial on purpose, so we do not spend area on an address decoder.

## What we are refusing to build

- A UART block plus an SPI block plus an I2C block.
- A wire that lets the CPU touch pins directly.
- On-chip training, or any sentence that says the chip "learns" or "understands."
- Ethernet on the chip.
- A second CPU context, a bigger RAM, or a fancier readout, until the mandatory blocks fit. Those are Tier 3 and they get cut first.
- A claim that we are "formally verified," or a claim of any clock speed or SPI rate, before the report exists.

## What you have to understand yourself

An agent can draft a module. You still own the answers to these, out loud:

1. What goes in, what comes out, and what must never happen (silent drop, two drivers, reservoir driving a pin).
2. Whether the code matches the Python model on one example you computed by hand.
3. Which gate the change is for, and what file will prove the gate.
4. Which sentences we are not allowed to put in the README yet.

If you cannot point at the ports of a module and say what each one means, do not merge it.

## The order of work

Do not start by writing the reservoir in Verilog. The order is: **make the idea executable in Python, then make Verilog match Python, then let the template build a chip around that Verilog.**

### 1. Develop (now through 28 Oct 2026, gates G0 and G1)

G0, 14 Oct. Get the factory working and learn if the design fits.

- Keep the template actions green: test, docs, GDS, FPGA. Right now the chip is still the template's adder (`uo_out = ui_in + uio_in`). That is fine until we replace the insides.
- Read the template top: `ui_in`, `uo_out`, `uio_in`, `uio_out`, `uio_oe`, `ena`, `clk`, `rst_n`. `uio_oe` is "am I driving this bidirectional pin."
- First behavior: UART transmit **as a TX-table playback**, out of a pin. Then make which symbol plays depend on a loaded program. That is the announcement's "getting started," done our way.
- Run synthesis on the core plus program RAM at 64 words and at 128 words, and on a skeleton of the symbol layer. Write down which RAM we keep. Leave at least 25% slack for routing and the clock tree. Area guesses in the spec are not this result.
- A prior-art pass: has someone already shipped a reservoir as a serial decoder on a programmable-I/O chip? Ternary multiply-accumulate blocks already exist on Tiny Tapeout, so "small integer neural net" alone is not the story.

G1, 28 Oct. Find out if the reservoir is worth trusting.

- Write the **golden model** in `work/model/`: a Python program that is the instruction set and the symbol layer. If Verilog and Python disagree later, Python is the spec until we fix whichever one is wrong.
- Write a tiny assembler in the same area so programs are text, not hand-packed bits.
- Generate messy traces: UART with baud error, USB-like NRZI with jitter and bit-stuffing, PS/2, Manchester, plus glitches and junk traffic. Train readouts **off chip**. Record accuracy, false alarms, latency, and cell count against the ordinary decoder.
- In that same model, show the boring pass-through file acting like an edge detector, and decide the four-pin aperture question.
- Find one temporal shape the nodes can hold well enough to load, decode, and re-emit, and a stranger wiggle that becomes pattern 7. Record both listeners. A worse UART score than the edge listener is not a failed study. If 1-bit Hamming cannot hold the hero shape, try a richer readout before giving up on the shape.
- The boring file must be good enough that UART, SPI, and I2C can be firmware plus that file. Write the hero choice and the traces in `work/study/`. If no shape sticks, record **Thin** and keep the translator. Do not redesign around UART.

### 2. Build (29 Oct through 2 Dec 2026, gate G2)

New Verilog is a **new file in** `src/`. In the same commit, add it to `info.yaml` `source_files` and to `PROJECT_SOURCES` in `test/Makefile`. Do not rename `src/project.v` or the `tt_um_example` module until a change that does all the references together. Do not edit `src/config.json` or the GitHub workflows.

Sensible build order, each one simulated before the next starts:

1. SPI loader that can shift a program into RAM and read it back.
2. TX table plus TX engine. UART TX is a program that emits symbols.
3. Core: fetch, the ALU, wait-for-cycles, `TXSYM`. Still no pins on the core.
4. RX path in the boring configuration: synchronizers, features, pass-through weights, stabilizer, RX FIFO, `RXSYM`. You can now loop back a symbol you sent.
5. Reservoir update and Hamming readout, lockstepped against Python.
6. Ordinary classifier beside it, plus the disagree flag.
7. Reflex table. Then CRC. Then UART, SPI, and I2C as programs plus weight files.

On 2 Dec the feature list is frozen to whatever survived, Verilog matches Python on pins and on reservoir state (including the boring configuration), and synthesis fits in 6×4.

### 3. Test (3 Dec through 23 Dec 2026, gate G3)

Several different kinds of test, because each catches a different lie:

- **Directed tests.** One protocol scenario with a known answer. Cocotb, in `test/`, calling the golden model.
- **Lockstep.** Same inputs to Python and Verilog every cycle. Compare pins, FIFO events, reservoir state.
- **Constrained random.** Random but legal programs and waveforms, including injected faults (flip a weight, overflow a FIFO).
- **Formal.** A proof tool (SymbiYosys, unless we later choose something else) for: the program counter stays in range; waiting N cycles takes N cycles; a reflex and a `TXSYM` never both emit and never silently vanish; FIFOs set a flag instead of dropping; reservoir values stay inside their bit width; memory fades; the boring weight file matches a hand-written synchronizer-plus-edge state machine. A failed proof is still a result if we file the counterexample. We do not say "formally verified" until that file exists.
- **Gate level.** The template can simulate the **layout netlist**, not just the Verilog you typed. This catches things synthesis broke.
- **FPGA.** The template has an ice40 flow. Use it if a board exists. Whether a board exists is still an open question.
- **Static timing.** After place-and-route, the tool says whether the chosen clock period is fast enough. Only then may anyone name a frequency.
- **AI-written tests.** Allowed and encouraged. Each one gets a line in a log: what it claims, and how a human or a second tool checked it.

### 4. Demonstrate (by 4 Jan 2027, then fix bugs until 18 Jan)

Each item is pass, fail, or explicitly deferred. Show them in this order. UART transmit out of a pin is still the first thing you build. It is not the opening scene.

1. A temporal line code loaded as weights plus a transmit table, decoded and re-emitted.
2. Pattern 7 on a wiggle that was not in the file.
3. Node state visible while that shape arrives.
4. The two listeners disagree, as a sticky bit.
5. A reflex reply with the program counter unchanged during the reply.
6. UART, then SPI, then I2C, each as another loaded file.
7. The boring settings file, checked against a small edge detector.
8. USB low-speed as a simulation. On the real chip only if pad electrical behavior has been checked, which it has not. Ethernet stays a written analysis plus a simulation. An on-chip snapshot of a prototype only if area remains.

From 5 Jan to 18 Jan, fix template precheck and gate-level failures. Do not add a new feature in that window.

## Where things live

- Specs at the repo root: v0.31 is the current amendment, v0.3 is the base, v0.2 is history.
- This folder: the working notes. [phases.md](phases.md) is the scoreboard.
- `src/`: Verilog the chip is built from. Template top stays put.
- `test/`: cocotb. This is the template's test entry point.
- `work/model/`: Python golden model. `work/study/`: the reservoir experiment. `work/fw/`: programs and weight files. `work/formal/`: proofs. `work/verification/`: logs.
- `knowledgebase/placeholders/`: a list of documents we still need (pad behavior, real board clock, protocol framing details). They stay empty until someone files a real source. Do not paste a random datasheet in to feel productive.

## Glossary

Each entry is what it is, how it works in one pass, why anyone uses it, and what it means on this chip. Electrical limits, polynomials, and clock rates that are not in the spec are not filled in here.

### The factory

**Tiny Tapeout.** A service that packs many student designs onto one shared chip. You deliver Verilog and a project file. They (and the template's scripts) run the steps that turn Verilog into a layout. For us: we live inside their CMOS5L template. We do not invent a new chip flow. `info.yaml` says who we are, how big we are (`6x4`), and which pins are named what.

**Tile.** Their unit of area. A 6×4 design is 24 tiles. The announcement's rough budget is about 1K logic cells per tile and about 0.7 mm². That budget is their estimate, not a measurement of our routed chip. For us: every extra block has to pay rent. Program memory made of flip-flops is the likely rent hog. If a larger 8×4 ever appears, we spend it on memory, not on a second CPU.

**ASIC.** A chip whose wiring is fixed at the factory. After fabrication you cannot move gates around. You can only load bits into memory. For us: that is why protocols have to be firmware plus weight files. The silicon is frozen in January; the line codes are not.

**Standard cells.** A library of pre-drawn gates (NAND, flip-flop, and so on) for one process. Synthesis maps your Verilog onto those cells. For us: IHP's 130 nm CMOS5L library, reached only through the template. We do not draw transistors.

**Synthesis.** A tool reads Verilog and writes a gate netlist, then reports how many cells it used. For us: run it early (gate G0). A design that looks small in Verilog can still be huge in flip-flops. Leave slack for the clock tree and wires.

**Place and route.** The tool sets each cell on the floor and draws the wires. This is what can fail even when synthesis looked fine. For us: the template's GDS action does this. We treat a finished route as the real size check.

**Static timing analysis (STA).** After routing, a tool adds up delays and says whether signals arrive before the next clock edge. For us: nobody names a clock frequency, a reflex delay, or an SPI rate until this report passes. The template's 20 ns period is a setting we handed the tool, not a measured board clock.

**GDS.** The layout file the factory reads. You almost never edit it. For us: if the template's GDS action is green, the flow accepted the current Verilog. The current Verilog is still the example adder.

**FPGA.** A chip you can rewire in the lab by loading a bitstream. Same idea as an ASIC from the Verilog side, wrong idea physically. For us: the announcement asks us to try the design on an FPGA before trusting the ASIC flow. The template has an ice40 job. Whether we have a board is still unanswered.

**Verilog.** The language the template compiles. It describes registers and wires, not a program that "runs" on a PC. For us: new modules are new files in `src/`, listed in `info.yaml` and in `test/Makefile` together. The top module name stays `tt_um_example` until a single change renames every reference.

**Cocotb.** Python that drives a Verilog simulation: poke pins, wait clocks, check pins. For us: `test/test.py` is the template's test. Later tests compare the chip against the Python golden model.

### The idea, as technologies

**Bit-banging.** Toggling pins from software with counted delays, instead of a hardware UART/SPI/I2C block. For us: that is the whole product. The difference from a PIO is that we bit-bang **names of waveforms**, not the pins themselves.

**PIO and PRU.** Small programmable state machines on the RP2040 (PIO) and on TI Sitara chips (PRU). They are the announcement's reference design: instructions that wait, set pins, and shift bits, with exact timing. For us: we keep the exact-timing instruction idea and remove direct pin access. Recognition of a new waveform is loaded data, not a new program that stares at a pin.

**Line code.** The agreement for how bits become wiggles. UART is "one level per bit, with a start edge." Manchester is "high-then-low means 0, low-then-high means 1." USB uses J and K levels on a pair of wires. For us: the TX table stores the wiggle. The symbol layer's job is to recover the name of the wiggle on the way in. A new line code is a new table plus new weights.

**Symbol and class.** Our word for one named wiggle. Eight classes, 3 bits. Class 7 is "unknown." For us: this is the only message between the entrance, the program, and the exit.

**Liquid state machine / reservoir.** A pile of simple nodes with fading memory and mostly fixed random wiring. You do not train the wiring. You train only a small readout on top, usually off-chip. How: each tick every node mixes a decayed copy of itself with a few weighted inputs, using adds and shifts, then clips to its bit width. Why people use one: the recent past is smeared into the node values, so a simple comparison can recognize a shape even when edges move a little. For us: 16 nodes, 6-bit integers, fixed sparse wiring, weights loaded after fabrication. It never drives a pin. It is the entrance, not an optional coprocessor.

**Weight, leak, prototype.** A weight scales one input into a node (`+power of two`, `-power of two`, or zero). A leak is how fast the node forgets (a right shift). A prototype is one stored 16-bit example of "this is what class 2 looks like after the readout squishes the nodes." For us: all three are in the settings chain the host shifts in.

**Hamming distance.** Count of bits that differ between two patterns. How: XOR, then popcount. Why: it is a cheap "how close is this?" with no multipliers. For us: that is the baseline readout. Eight prototypes compared at once; closest wins if it wins by a margin.

**Degenerate configuration.** A legal weight file that makes the reservoir boring on purpose: pass the pin through, no recurrence, forget immediately, prototypes mean "level" and "edge." For us: this replaces a bypass wire. Plain GPIO is still the entrance, just badly aimed at being clever. We intend to prove it matches a hand-written edge detector. That proof does not exist yet, so we do not say "formally verified."

**Reflex.** A loaded rule: if this class arrives and the rule is armed, queue that TX symbol now. For us: the fast hallway. The program arms it. An I2C ACK or an SPI slave's first reply is the picture. Speed is whatever the later timing report says, not a number we advertise now.

**CRC and LFSR.** A checksum built by shifting bits through a XOR feedback polynomial. An LFSR is that shift register. How: one bit in, a few XORs, one bit out. Why: UART parity, USB, and CAN need it, and doing it in instructions is slow and easy to get wrong. For us: one programmable 16-bit unit the shifter can tap. It does not compute the 32-bit checksum Ethernet needs, so Ethernet stays off the chip.

**Open-drain.** A pin that can pull the wire down, or let go. A resistor outside the chip pulls it up. Two chips can share the wire without fighting. Why: I2C is built this way. For us: "let go" is an output-enable bit in a TX-table symbol, not a special CPU instruction. Whether these pads actually do that is **[VERIFY]**. Do not claim I2C electrical compliance.

**FIFO.** A small queue. First event in is first event out. For us: 8 receive events, 16 transmit symbols. Overflow or underrun sets a sticky flag. Quietly dropping data is a bug, and it is one of the things we want a proof for.

**Synchronizer.** Two flip-flops in a row on an input whose changes are not aligned to our clock. Why: a single sample of an async pin can hang a flip-flop halfway between 0 and 1 (metastability) and then confuse everything downstream. For us: every input pin gets this before anyone interprets it. It does not decode protocols.

**SPI, as the host link.** A clock, a chip-select, and data bits. The host is master; our chip is the slave. For us: this is the loading dock only (`ui[2]` SCK, `ui[1]` CS, `ui[0]` MOSI, `uo[0]` MISO). Using SPI as a protocol we emulate is a different thing: that one goes through symbols, like everything else.

**Config shift chain.** A long shift register of settings, loaded serially, no address bus. Why: an address decoder wide enough for every weight bit costs more area than shifting. For us: weights, prototypes, TX scripts, reflexes, and pin selects live here.

### Protocols the brief names

What they are, in one line, and how they sit on this chip. Framing details we have not filed stay in `knowledgebase/placeholders/protocols/`.

- **UART.** One wire each way, a start edge, then bits. Transmit is a TX table. Receive can use the boring file plus the program. This is a stepping-stone protocol, not the opening demo.
- **SPI.** A clock plus data plus chip-select, usually a shift register. Master and slave are both firmware plus the boring configuration. A slave that must answer immediately uses a reflex. We have not fixed mode or bit order yet.
- **I2C.** Two shared wires, open-drain, addresses, ACK bits. START/STOP can be classes. ACK can be a reflex. Pad behavior is not verified.
- **JTAG / SWD.** Debug shift protocols clocked by the master. Core-driven shift through the boring configuration. No need for the clever reservoir.
- **PS/2.** A keyboard-style frame with a clock and a parity bit. Optional help from the symbol layer for noisy edges. Frame and parity are the program's job.
- **CAN.** A differential bus that needs an external transceiver chip. Edge resync and dominant/recessive levels are symbol-layer classes. Stuffing and CRC15 are the program plus our CRC unit.
- **USB low-speed.** A 1.5 Mbit packet protocol on a wire pair (J, K, SE0). Symbol layer for those levels and for sync/end patterns; program for bit-unstuffing and CRC. Demo in simulation. On silicon only if pads and pull-ups check out, which they have not.
- **10 Mbit Ethernet.** Out of scope on silicon. The spec already lists why (clock math, a PHY we do not have, a CRC32 we do not compute). Deliverable is a simulation plus a writeup.

### How we check it

**Golden model.** A Python program that is the definition of the instruction set and the symbol layer. How: same inputs as the Verilog, plain integers, no hidden analog. Why: you can read it, and you can change the reservoir in an afternoon. For us: it lives in `work/model/`. If Verilog and Python disagree, that is a bug in one of them, not a mystery.

**Lockstep.** Run the model and the Verilog on the same stimulus and compare pins, queued events, and reservoir numbers. For us: this is the G2 test, including one run in the boring configuration.

**Constrained-random testing.** A generator builds legal but surprising programs and waveforms, and also injects faults (a flipped weight, a FIFO that should have flagged). Why: directed tests only cover the cases you thought of. For us: a logged run is part of gate G3.

**Formal verification.** A tool tries to prove a property for all cases, or hands you a counterexample. SymbiYosys is the default named in the spec; Hardcaml is an open question, not a decision. For us: program counter stays in range, a wait of N cycles takes N, reflexes and program sends do not collide silently, FIFOs flag instead of dropping, reservoir values stay in range, memory fades, and the boring configuration matches a reference edge detector. "Formally verified" is a sentence we earn when that file exists.

**Gate-level simulation.** Simulate the gates the tool produced, not the Verilog you typed. Why: synthesis can change behavior if the Verilog was sloppy. For us: the template already has this path.

**Gate (the schedule kind).** A date plus a checklist of files. G0 fit and factory. G1 reservoir experiment. G2 Verilog matches Python and still fits. G3 proofs, random tests, route, timing, FPGA note. Narrative is not a pass.

## A sane first week

1. Redraw the diagram in "The picture, in plain English" from memory, then check it.
2. Run the template's cocotb test so you see a simulation pass on the adder.
3. In Python, not Verilog, implement "TX table plays symbol 0 then symbol 1" and print the pin waveform.
4. Only then ask an agent for a Verilog TX engine, and check it against your printout before anything else lands in `src/`.

