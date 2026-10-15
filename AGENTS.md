# Agent notes

v0.3 as amended by v0.31 is the reference design. v0.2 is history. In the reference design, the core never touches a pin; there is no pin-level bypass. Goals and demo order are `knowledgebase/doctrine.md`: familiar protocols must work and are not the thing to optimize. Read `knowledgebase/README.md` before changing RTL, firmware, models, the study, or the datasheet.

## Experiments

[knowledgebase/experiments.md](knowledgebase/experiments.md) governs experimental work in this fork and takes precedence over reference-design mechanism restrictions there. Agents may change the reservoir, preprocessing, readout, interfaces, controller, and total system architecture within an assigned experiment. No approval is needed solely because an experiment departs from v0.31 or the existing emulator. Keep the work tied to configurable waveform recognition and response, with explicit assumptions and measured timing, rejection, and resource costs. Adopting a result into the reference design is a separate decision.

## Frozen template

Do not rename or restructure `src/project.v`, the `tt_um_example` module, `test/Makefile` `PROJECT_SOURCES`, `.github/workflows/`, or `src/config.json`. New Verilog is a new file under `src/`, added to `info.yaml` `source_files` and to `PROJECT_SOURCES` in the same change.

Models, the reservoir study, firmware, and formal notes live under `work/`. Synthesizable RTL does not.

## Evidence

Items marked **[EST]** or **[VERIFY]**, and v0.3 section 11, are not specifications. Checked external sources for UART, I2C, USB low-speed, and 10 Mbit Ethernet are authorized under `knowledgebase/protocols/README.md`; read those guides and their source register before implementing protocol behavior. Source facts, project choices, and measured implementation evidence must remain distinct. Retain original documents only with affirmative redistribution permission and checksums. Other external hardware/protocol acquisition remains outside this authorization. Unresolved implementation and hardware gaps stay in `knowledgebase/placeholders/` with `status: missing`; acquiring documentation does not pass a gate.

`clock_hz` stays 0 until post-route STA passes. Do not claim I2C or USB electrical compliance, on-chip training, Ethernet on silicon, or "formally verified" anything before the proof artifact is filed.

Spec files are append-only: never edit a released version, add a delta document. Branch and tag rules are in `knowledgebase/versioning.md`; new branches come off `cmos5l-v0.31`.

## Gates

A phase is done only when `knowledgebase/phases.md` has a recorded artifact. Do not describe a gate as passed without that file or log.
