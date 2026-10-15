# Ethernet (analysis only)

status: missing

documentation_status: acquired_with_edition_and_provenance_limits
simulation_evidence_status: missing

Checked reference: [Ethernet guide](../../protocols/ethernet.md), IEEE 802.3-2012 clauses 3, 4, 7 and 14; [source register E1–E3](../../protocols/sources/README.md#ethernet). Source filing dated 12 October 2026 uses an older, mirror-retrieved edition; official byte authentication and latest-edition review remain unverified. The guide includes a preliminary implementation-needs analysis, not the required system simulation.

Does not block a silicon gate. v0.3 section 6.4 removes 10 Mbit Ethernet from the chip. The missing deliverable is a written analysis plus a simulation, not a PHY design.

v0.3 section 6.4 already gives the reasons it stays off silicon: a non-integer number of clocks per half-bit at the assumed flow period, a PHY, transformer, and driver outside the chip, no CRC32 in the 16-bit unit, and the clock accuracy stated there. The assumed flow clock is **[VERIFY]**. The sourced guide explains external MAC/PHY requirements without changing this architectural decision.

Still required:

- A TX-table and byte-streaming simulation of a Manchester frame at a 40 MHz simulation clock, with the FCS supplied by the host.
- Complete the implementation-needs analysis with measured simulation timing and a resource/interface assessment; the guide's preliminary analysis supplies the protocol context.

No Ethernet part, pin, or silicon promise is added when this file is filled.
