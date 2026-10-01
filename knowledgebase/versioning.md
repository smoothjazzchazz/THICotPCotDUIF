# Versioning

How specs, branches, and the template are kept from breaking each other.

## Spec versions (files, append-only)

Specs are root-level files named `Temporal Protocol Machine_ Pitch and Architecture (vX.Y).md`.

- A released spec file is **never edited**. A design change is a **new delta document** (v0.31 amends v0.3) plus an update to the knowledgebase pages and a `vXY-delta.md` summary.
- Current chain: **v0.2** (history, do not build) → **v0.3** (base) → **v0.31** (current amendment). See [authority.md](authority.md) for precedence.
- The evolution trail (v0.2 → v0.3 → v0.31 and the delta pages) is kept deliberately: it is source material for the final writeup.

## Git layout

| Ref | Meaning | Rule |
| --- | --- | --- |
| tag `template-cmos5l` | Pristine CMOS5L Tiny Tapeout template (commit `9ac3df6`) | Never moves. The integrity check diffs against it |
| branch `cmos5l` | **Trunk.** CMOS5L template + specs + knowledgebase + work | All new branches are cut from here. All merges land here |
| branch `main`, `cmos51` | Generic Tiny Tapeout template (initial import; `cmos51` is a stale duplicate of `main`) | Do not commit to these. Not the competition template |
| branch `ttihp0p2` (remote) | TTIHP 0p2 shuttle template | Wrong shuttle for this competition. Do not branch from it |
| tags `spec-v0.2`, `spec-v0.3`, `spec-v0.31` | Commit where each spec version landed | Never move |

The competition requires the **CMOS5L** template, so `cmos5l` is the only valid base. A branch cut from `main`, `cmos51`, or `ttihp0p2` is on the wrong template and must be recreated, not merged.

## Branch naming

Short-lived branches off `cmos5l`, merged back when their artifact lands:

- `feat/<block>` — RTL (for example `feat/tx-table`)
- `model/<topic>`, `study/<topic>` — golden model and reservoir study
- `fw/<protocol>` — firmware and weight files
- `verif/<topic>` — tests, formal, lockstep
- `docs/<topic>` — datasheet, knowledgebase, specs

## Template integrity

Before merging to `cmos5l`, run from the repo root:

```text
python work/tools/check_template.py
```

It verifies, against tag `template-cmos5l` and the freeze rules:

1. `src/config.json` and `.github/workflows/` are byte-identical to the template.
2. `src/project.v` exists and contains a `tt_um_` module.
3. `test/Makefile` keeps `PROJECT_SOURCES` and the cocotb include.
4. `info.yaml` keeps `yaml_version: 6` and all 24 pins.
5. `info.yaml` `source_files` and `test/Makefile` `PROJECT_SOURCES` list the same files, and every one exists in `src/`.

The check failing means the template freeze was broken; fix the branch, do not adjust the check.
