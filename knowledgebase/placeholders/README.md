# Placeholders

These files track hardware/protocol documents and implementation evidence the design still needs. `status: missing` means some required deliverable remains unresolved; it does not necessarily mean no protocol reference is available.

For UART, I2C, USB low-speed, and 10 Mbit Ethernet, the user's 12 October 2026 source-filing request supersedes the former prohibition on external protocol research. Checked documentation is in [protocols](../protocols/README.md), with source revisions, section citations, redistribution decisions, and a model audit. Each corresponding stub identifies the acquired references and still-missing implementation, simulation, or hardware evidence. Standards describe external requirements; they do not prove that this chip meets them. Other protocol and hardware gaps remain unresolved.

The specs already state the architectural role of each protocol (which tier; trained configuration, degenerate configuration, or reflex). That role is in [architecture.md](../architecture.md) and the pitch. It is not an implementation specification.

The contest announcement is filed in [../competition/](../competition/README.md). [competition-rules.md](competition-rules.md) only points there. Do not reconstruct the rules from v0.3 section 2.
