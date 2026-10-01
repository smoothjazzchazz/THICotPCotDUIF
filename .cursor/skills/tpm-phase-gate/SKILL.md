---
name: tpm-phase-gate
description: Checks Temporal Protocol Machine work against the gates G0, G1, G2, G3, the 4 Jan 2027 freeze, and the January submit buffer. Use when planning a milestone, claiming a gate has passed, or deciding whether a hero waveform sticks in the reservoir.
---

# Phase gate

Read `knowledgebase/phases.md` and `knowledgebase/doctrine.md`. A gate passes only when every artifact listed there exists and the check is true.

## When planning

State which gate the change serves. Do not add a pin path so UART looks normal. Do not start Tier 3, a second context, or Ethernet on silicon to make a gate look further along. Tier 3 is cut first, except an on-chip prototype snapshot if area remains after the pipe and the hero. Ethernet is the analysis placeholder only.

## When claiming a pass

Point at the file or log:

- G0: CI status, RAM synthesis reports, symbol-layer skeleton synthesis, written RAM choice, slack, placeholder status.
- G1: study records in `work/study/`, the hero shape or a written Thin result, the receive-aperture decision, and the boring file checked in the model. A worse UART score than the edge listener is not a failed gate.
- G2: feature list, lockstep log (including the degenerate configuration and a node-state readback), 6×4 synthesis report.
- G3: formal results (including reflex serialization and the pass-through equivalence proof), constrained-random log, LibreLane result, STA report, gate-level result, ice40up5k result.
- Freeze: each demonstration in `knowledgebase/doctrine.md`, in that order, marked pass, fail, or deferred.

If the artifact is absent, the gate is not passed. Do not describe it as passed.
