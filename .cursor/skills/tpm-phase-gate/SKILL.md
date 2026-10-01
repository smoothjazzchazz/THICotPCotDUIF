---
name: tpm-phase-gate
description: Checks Temporal Protocol Machine work against the v0.3 gates G0, G1, G2, G3, the 4 Jan 2027 freeze, and the January submit buffer. Use when planning a milestone, claiming a gate has passed, or deciding reservoir go, partial, or no-go.
---

# Phase gate

Read `knowledgebase/phases.md`. A gate passes only when every artifact listed there exists and the check is true.

## When planning

State which gate the change serves. Do not start Tier 3, a second context, or Ethernet on silicon to make a gate look further along. Tier 3 is cut first. Ethernet is the analysis placeholder only.

## When claiming a pass

Point at the file or log:

- G0: CI status, RAM synthesis reports, symbol-layer skeleton synthesis, written RAM choice, slack, placeholder status.
- G1: study records in `work/study/`, the receive-aperture decision, and an explicit Go, Partial, or No-go. 99% and about 2K cells stay the proposed bar unless this repo has replaced them in `phases.md`. Every outcome ships the same silicon; only recommended weight files differ.
- G2: feature list, lockstep log (including the degenerate configuration), 6×4 synthesis report.
- G3: formal results (including reflex serialization and the pass-through equivalence proof), constrained-random log, LibreLane result, STA report, gate-level result, ice40up5k result.
- Freeze: each v0.31 section 10 demo marked pass, fail, or deferred.

If the artifact is absent, the gate is not passed. Do not describe it as passed.
