# Knowledge base

This folder is the working set for agents. It does not replace the pitch documents.

Humans start at [tldr.md](tldr.md). It is the plain-language map of the chip and the build order. The pages below are the contracts.

## Read order

1. [tldr.md](tldr.md) — plain-English topology, block walkthrough, build order, and the glossary.
2. [doctrine.md](doctrine.md) — what the chip is for, and the order we show it.
3. [authority.md](authority.md) — which document wins, and what may be said.
4. [competition/README.md](competition/README.md) — the filed announcement: challenge, rules, area budget, logistics.
5. [v03-delta.md](v03-delta.md) — what v0.31 changed. No pin-level bypass exists.
6. [v02-delta.md](v02-delta.md) — what v0.3 removed. Do not implement v0.2.
7. [architecture.md](architecture.md) — contracts to build against.
8. [phases.md](phases.md) — gates and the artifact each one requires.
9. [versioning.md](versioning.md) — spec versioning and the git branch/tag scheme.
10. [placeholders/README.md](placeholders/README.md) — documents that are required and not here.

## Sources

- [Temporal Protocol Machine: Pitch and Architecture (v0.31)](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.31).md) — current amendment
- [Temporal Protocol Machine: Pitch and Architecture (v0.3)](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.3).md) — base document
- [Temporal Protocol Machine: Pitch and Architecture (v0.2)](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.2).md) — history only
- [competition/](competition/README.md) — filed announcement text

Architecture pages in this folder restate v0.3 as amended by v0.31. If a page and the specs disagree on a mechanism, the specs win (v0.31 over v0.3). Contest rules: [competition/](competition/README.md) wins over v0.3 section 2. Goals and demo order: [doctrine.md](doctrine.md) wins over a bake-off framed in an older pitch.

## Missing documents

Hardware and protocol implementation notes that the design still needs are stubs under [placeholders/](placeholders/). Leave a stub at `status: missing` until the team files a checked source. Do not search the web and commit a datasheet, a standard, or a tutorial in its place.
