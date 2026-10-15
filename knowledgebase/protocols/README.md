# Protocol references

These notes explain what the protocols require, so that generators, receivers, controllers, and tests do not have to invent their behavior. Added 12 October 2026 at the user's request. They do not change the reference architecture or qualify an implementation.

| Read | Detailed scope | Source authority |
| --- | --- | --- |
| [UART](uart.md) | Logic-level asynchronous framing, 8N1 and 8E1 project profiles | TI peripheral documentation and protocol training; device-specific behavior is labeled |
| [I2C](i2c.md) | Standard/Fast-mode transactions; mode-specific timing | NXP UM10204 rev. 7.0 |
| [USB low-speed](usb-ls.md) | Low-speed device signaling, packets, control/interrupt transactions | USB 2.0 plus the reviewed errata/ECNs |
| [Ethernet](ethernet.md) | Basic MAC frames and 10BASE-T/Manchester analysis | IEEE 802.3-2012, with edition and retrieval limits stated |

Start with the overview in each guide, then use the cited sections for implementation. Source IDs refer to the [source register](sources/README.md); [manifest.json](sources/manifest.json) records exact retrieved bytes, dates, provenance, and retention decisions. [Model audit](model-audit.md) separates existing simulation assumptions from protocol requirements. [Validation](validation.md) records checks performed and remaining limits.

## How to use the evidence

- **Protocol requirement:** supported by a named source and section. A standard's electrical limits are requirements to meet, not measured properties of this chip.
- **Project choice:** an address, framing profile, application behavior, timeout, tick rate, or restricted feature set chosen for a particular experiment. Record it explicitly.
- **Verified implementation:** needs its own reproducible artifact and acceptance criteria. Reading a standard is not verification. Existing gate status remains in [phases](../phases.md).

Sources govern external protocol behavior; the released design documents govern the project's architecture. If those conflict, file the discrepancy rather than silently changing either. Follow [experimental scope](../experiments.md) for experiments and the versioning process for reference-design adoption.

## Maintenance rules

For these four protocols, checked external documentation and original, cited explanations are authorized. Prefer the publisher's specification; manufacturer manuals may explain implementations but do not redefine a standard. Identify edition, section/table, applicable corrections, and any unresolved access gap. Never substitute a search-result snippet for reading the relevant source.

Keep original source files only when redistribution is affirmatively permitted, with notices intact and a SHA-256 checksum. Otherwise provide official links and retrieval provenance. The retained IEEE correction sheet has separate noncommercial distribution restrictions; it is not covered by the repository's software license.

The protocol placeholders continue tracking missing implementation and hardware evidence. Historical studies keep their original source-status text; this directory is the later documentation update. Other protocol and hardware placeholders remain unresolved.
