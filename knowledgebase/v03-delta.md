# What changed from v0.3 to v0.31

Source: v0.31 section 0. Build the v0.31 column. The v0.3 bypass is not in scope.

- **Pin access.** v0.3: the core reads and drives pins directly, and a bypass path always exists. v0.31: the core never touches a pin. All input arrives as symbol events, all output leaves as symbols through the TX table. The ISA has no pin-level I/O.
- **Bypass.** v0.3: a silicon path around the symbol layer. v0.31: a **weight file** — a degenerate symbol-layer configuration that acts as a synchronizer plus edge detector. The escape hatch is data through the same silicon, and it gets a formal equivalence proof against a reference FSM.
- **Fallback classifier.** v0.3: swapped in on a G1 no-go, replacing the reservoir. v0.31: built **next to** the reservoir on die, both behind the same symbol-event interface. A G1 no-go now means the conventional front end becomes primary and the reservoir ships as the research configuration — same silicon either way.
- **Fast responses.** v0.3: bypass. v0.31: **reflex table** — armed RX-class → TX-symbol mappings fired without core instructions. `ARM`/`DISARM` ops added. SPI-slave maximum rate drops; that trade is accepted and documented.
- **Pin ownership.** v0.3: per-pin mux, core-direct or TX engine, with a "never both" formal property. v0.31: TX engine always owns output pins; the property becomes reflex/`TXSYM` serialization with no silent drop.
- **Tier 1.** v0.3: core plus bypass protocols. v0.31: core plus the symbol-layer datapath in degenerate configuration plus the TX table. The symbol layer is on the first milestone's critical path.
- **New open design question.** The 4-pin receive aperture must cover concurrent slow signals (CS while watching MOSI). Default answer: per-lane pin selects. Decide in the golden model before G1. See v0.31 section 4.

Unchanged: reservoir micro-architecture, readout, stabilizer, event format, FIFOs, CRC/LFSR, loader and config chain, gate dates, Ethernet analysis-only scope, and the claims policy baseline.
