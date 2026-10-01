# Doctrine

How this project decides what to build and what to show. Mechanisms stay in [architecture.md](architecture.md). This page wins on goals, success, and the order we present the chip.

## What it is for

A waveform translator. After fabrication, a host loads weights and tables and the same pins speak whatever that file describes, inside the chip's timing and pin limits. The announcement's UART, SPI, and I2C are stepping stones: they have to work, through that same load path, so the chip covers the assignment. The chip is not designed to be the best decoder of those protocols.

The point of the work is the behavior a fixed UART block plus an SPI block does not have:

- A line code chosen because it is a shape in time, loaded after the silicon exists, decoded and sent back.
- Pattern 7 when the wiggle matches nothing that was loaded.
- The reservoir's node values readable while a shape arrives, over the host link or the debug pins.
- Two listeners on the same wire, and a sticky bit when they disagree. That bit is a feature. It is not a scoreboard, and a loss to the edge listener on UART is not a failure.
- A reflex that answers while the program counter stays still.
- A Python twin of the reservoir that matches the silicon bit for bit, from a published seed, plus a check that the boring settings file behaves like a small edge detector.

## What we do not optimize

- Being the fastest or most accurate UART, SPI, or I2C.
- A writeup whose thesis is "compared with the usual decoder."
- A private pin path added so the familiar protocols look normal.
- Speed, a second context, or Ethernet, bought by giving up the translator.

## How a demo is ordered

Weird behavior first, coverage after. UART transmit out of a pin remains the first engineering milestone. It is not the first scene of the submission.

1. Load a temporal line code. Decode it and re-emit it.
2. Pattern 7 on a stranger wiggle.
3. Node state visible during that shape.
4. The two listeners disagree.
5. A reflex reply with the program counter still.
6. UART, then SPI, then I2C, each as another loaded file. They work. They are not the act.
7. The boring settings file, checked against a small edge detector, as part of the verification story.
8. USB low-speed only as a simulation unless pad behavior has been checked. On-chip snapshot of a prototype only if area remains after the pipe and the hero. It is the Tier 3 item to keep if anything in Tier 3 is kept.

## Study

G1 asks whether at least one temporal shape sticks in the nodes well enough to be the hero, and whether the boring file is good enough that the stepping-stone protocols can be firmware plus that file. Record both listeners. Do not set the pass mark as "better than a normal decoder."
