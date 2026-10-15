# Authority

**The reference design is v0.3 as amended by v0.31.** [v0.31](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.31).md) is a delta document: where it is silent, [v0.3](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.3).md) stands; where they disagree, v0.31 wins. [v0.2](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.2).md) is a superseded draft. Read [v03-delta.md](v03-delta.md) and [v02-delta.md](v02-delta.md) before using older text. Open questions in v0.3 section 11 are not decisions.

**Experimental scope** is [experiments.md](experiments.md). In this fork it takes precedence over reference-design mechanism restrictions, including those in the released pitch documents. Agents may test different reservoir and total system architectures without first amending the reference design. Evidence rules, project purpose, and frozen-template requirements still apply.

Spec files are append-only. Never edit a released version; a change is a new delta document (see [versioning.md](versioning.md)).

**External protocol behavior** for UART, I2C, USB low-speed, and 10 Mbit Ethernet is documented in [protocols](protocols/README.md), authorized by the user on 12 October 2026. Those named sources govern protocol requirements; they do not change reference-design mechanisms or establish measured conformance. Record a discrepancy explicitly if a model or design assumption conflicts with a source. Documentation availability and implementation/hardware qualification are separate statuses.

**Contest requirements** are the filed announcement in [competition/](competition/README.md): process, 6×4 tiles, deadline, open source, and the area budget stated there. v0.3 section 2 is a compliance matrix, not the announcement. If they disagree on a contest rule, the filed announcement wins.

**Goals, success, and demo order** are [doctrine.md](doctrine.md). Where an older pitch treats a bake-off against a normal decoder as the point of the chip, doctrine wins. Reference implementation mechanisms (no pin path, symbol events, reservoir, reflex, both listeners) stay v0.31 until a new design delta adopts a change. An experiment's question and success criteria follow [experiments.md](experiments.md), not the reference demo checklist.

## Tags

- **[EST]** — back-of-envelope. Not a specification. Replace with synthesis or measurement before treating it as a number.
- **[VERIFY]** — not checked against Tiny Tapeout or IHP documents. Not a specification.
- **Open question** — v0.3 section 11. Unassigned for the reference design. Experiments may test explicit assumptions; do not present them as settled implementation choices.

Do not promote a tagged or open item into `info.yaml`, `docs/info.md`, the README, or a comment that reads as fact.

## Claims (v0.3 section 12, extended by v0.31 section 9)

The lists below concern claims about the reference chip. Experiments may report a measured comparison or simulated mechanism outside that design, with its conditions and limits. A simulation of adaptation does not establish on-chip training; an estimated schedule does not establish a silicon clock rate.

We can say:

- a waveform translator: new line codes after fabrication are loaded files, inside the chip's timing and pin limits
- UART, SPI, and I2C work as further loaded files
- deterministic, bit-exact reservoir, with node state readable
- pattern 7 for an unrecognized wiggle, and a sticky disagreement between the two listeners
- open toolchain, lockstep, and the filed checks

We must not say:

- that the chip is the best, or even a competitive, UART, SPI, or I2C decoder
- that the project is a scoreboard against a normal decoder
- the chip understands or learns arbitrary protocols
- on-chip training
- it beats FSMs or DPLLs
- any clock frequency, reflex rate, or SPI-slave rate before post-route STA
- "formally verified pass-through" (or "formally verified" anything) before the proof artifact is filed
- that removing the bypass made the chip faster or smaller — it is a flexibility and defensibility trade, and the v0.31 numbers are estimates
- I2C or USB electrical compliance, or Ethernet on silicon, before they are demonstrated

Reference-design training is off-chip. An on-chip prototype snapshot is Tier 3, and it is not training.

## Clock

`info.yaml` `clock_hz` stays `0`. The template `src/config.json` period of 20 ns is a flow setting. v0.3 assumes 50 MHz for estimates and marks the board clock **[VERIFY]**. Do not state a frequency as achieved.
