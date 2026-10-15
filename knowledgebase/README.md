# Knowledge base

This folder is the working set for agents. It does not replace the pitch documents.

Humans start at [tldr.md](tldr.md). It is the plain-language map of the reference chip and the build order. Agents doing experiments also read [experiments.md](experiments.md): its scope amendment permits alternative architectures within the project.

## Read order

1. [tldr.md](tldr.md) — plain-English topology, block walkthrough, build order, and the glossary.
2. [doctrine.md](doctrine.md) — what the chip is for, and the order we show it.
3. [authority.md](authority.md) — which document wins, and what may be said.
4. [experiments.md](experiments.md) — what agents may change in experiments, what stays in scope, and how a result is adopted.
5. [competition/README.md](competition/README.md) — the filed announcement: challenge, rules, area budget, logistics.
6. [v03-delta.md](v03-delta.md) — what v0.31 changed in the reference design.
7. [v02-delta.md](v02-delta.md) — what v0.3 removed from the reference design.
8. [architecture.md](architecture.md) — reference implementation contracts.
9. [phases.md](phases.md) — project gates and the artifact each one requires.
10. [versioning.md](versioning.md) — spec versioning and the git branch/tag scheme.
11. [placeholders/README.md](placeholders/README.md) — documents that are required and not here.
12. [protocols/README.md](protocols/README.md) — checked UART, I2C, USB low-speed, and 10 Mbit Ethernet behavior, source register, and model-assumption audit; read before implementing those protocols.

## Sources

- [Temporal Protocol Machine: Pitch and Architecture (v0.31)](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.31).md) — current amendment
- [Temporal Protocol Machine: Pitch and Architecture (v0.3)](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.3).md) — base document
- [Temporal Protocol Machine: Pitch and Architecture (v0.2)](../Temporal%20Protocol%20Machine_%20Pitch%20and%20Architecture%20(v0.2).md) — history only
- [competition/](competition/README.md) — filed announcement text

For the reference implementation, architecture pages restate v0.3 as amended by v0.31, and the specs win on mechanisms (v0.31 over v0.3). For experiments, [experiments.md](experiments.md) takes precedence over those mechanism restrictions. Contest rules: [competition/](competition/README.md) wins over v0.3 section 2. Goals and demo order: [doctrine.md](doctrine.md) wins over a bake-off framed in an older pitch. Experimental success does not automatically change the reference design or pass a project gate.

## Missing documents

Unresolved hardware, implementation, and verification evidence is tracked under [placeholders/](placeholders/). The user-authorized [protocol references](protocols/README.md) file checked external behavior for UART, I2C, USB low-speed, and 10 Mbit Ethernet. Their placeholders distinguish documentation acquired from implementation evidence still missing. Follow the source register's provenance and redistribution rules; do not infer hardware compliance or a passed gate from a source citation. Other gaps remain unresolved.
