---
name: tpm-architecture
description: Applies the Temporal Protocol Machine v0.31 contracts when editing RTL, firmware, the golden model, or the reservoir study. Use when implementing the core, symbol layer, classifiers, FIFOs, TX table, reflex table, CRC unit, loader, or when a superseded feature (pin-level bypass, core-direct pin drive, barrel contexts, programmable reservoir connectivity, on-chip training, Ethernet on silicon) is about to be added.
---

# Architecture

Read `knowledgebase/architecture.md`, `knowledgebase/v03-delta.md`, and `knowledgebase/v02-delta.md` before editing.

## Build only this

- The core never touches a pin. All input is symbol events; all output is symbols through the TX table. "Raw GPIO" is the degenerate weight configuration, not a wire.
- Tier 1 first: one context, program RAM (128 words, 64 fallback), host SPI loader, symbol-layer datapath with the degenerate configuration, TX table.
- Tier 2 behind the symbol-event interface: `{class 3 bits, start-timestamp 12 bits}`, RX FIFO 8 deep, sticky overflow, TX FIFO 16 by 3 bits, reflex table (8 entries, armed by the core), dual classifiers (reservoir plus Δt/run-length), CRC/LFSR width ≤ 16.
- Reservoir update is the integer equation in the architecture note. 16 nodes, fixed sparse taps, weights `±2^s` or 0. It never drives a pin.

## Do not build

- A pin-level bypass, core-direct pin drive, a pin-ownership mux, or pin-level ISA ops (wait/set/branch on pin).
- Barrel contexts, a timed pin scheduler, or programmable reservoir fan-in.
- `RES_MATCH` / `RES_SYNC` as the matcher output.
- CRC32, an Ethernet PHY path, or on-chip training.
- A second pin interface for any G1 outcome. Both classifiers live behind the same event interface.

## Where files go

Synthesizable Verilog: new files in `src/`, listed in `info.yaml` and `test/Makefile` together. Do not rename `tt_um_example` or `project.v`.

Models and study code: `work/model/`, `work/study/`. Firmware: `work/fw/`.
