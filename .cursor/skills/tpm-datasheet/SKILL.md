---
name: tpm-datasheet
description: Edits Tiny Tapeout info.yaml and docs/info.md for the Temporal Protocol Machine using only v0.3 facts as amended by v0.31. Use when changing the project title, description, tiles, pinout, clock_hz, docs/info.md, or any datasheet sentence about how the chip works, how to test it, or external hardware.
---

# Datasheet

Read `knowledgebase/authority.md` and `knowledgebase/doctrine.md` before editing `info.yaml` or `docs/info.md`.

## Allowed

- Title, the v0.3 one-liner, and `tiles: "6x4"`.
- Pin names from v0.3 section 5.5 only. Host pins are `ui[2]` SCK, `ui[1]` CS, `ui[0]` MOSI, `uo[0]` MISO. Other pins keep the group role already written. Do not assign a protocol to a specific `uio` bit.
- Test text that describes the method (golden model, lockstep, the named formal properties) and the demonstration order in `knowledgebase/doctrine.md`. Say the checked-in top is still the template adder until Tier 1 replaces it. Do not present UART accuracy as the point of the chip.
- External hardware that v0.3 names: host SPI master, external pull-up for open-drain, CAN transceiver. State that pad behaviour is not verified.

## Not allowed

- Any mention of a pin-level bypass: under v0.31 the symbol layer is the only pin interface, and "raw GPIO" is a loadable configuration.
- `clock_hz` other than 0, until post-route STA has passed and the claim rule allows a frequency. Same for reflex and SPI-slave rates.
- "Formally verified" wording before the proof artifact is filed.
- Author or Discord, unless the user supplies them. v0.3 names neither.
- Area, cell counts, or clock rates from the **[EST]** / **[VERIFY]** sections.
- A USB part, an Ethernet PHY, or a compliance claim.
- Renaming `tt_um_example` or `project.v` in a datasheet-only edit.

Leave the template tile-size comment in place. `6x4` is set anyway.
