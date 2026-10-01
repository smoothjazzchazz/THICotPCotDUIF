# Ethernet (analysis only)

status: missing

Does not block a silicon gate. v0.3 section 6.4 removes 10 Mbit Ethernet from the chip. The missing deliverable is a written analysis plus a simulation, not a PHY design.

v0.3 section 6.4 already gives the reasons it stays off silicon: a non-integer number of clocks per half-bit at the assumed flow period, a PHY, transformer, and driver outside the chip, no CRC32 in the 16-bit unit, and the clock accuracy stated there. The assumed flow clock is **[VERIFY]**. Do not extend those reasons with a collected datasheet.

Required, and not yet written:

- A TX-table and byte-streaming simulation of a Manchester frame at a 40 MHz simulation clock, with the FCS supplied by the host.
- A short analysis of what silicon would need.

No Ethernet part, pin, or silicon promise is added when this file is filled.
