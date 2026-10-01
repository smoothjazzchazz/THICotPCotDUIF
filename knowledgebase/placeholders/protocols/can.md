# CAN

status: missing

Blocks treating CAN as implemented on silicon. v0.3 uses the symbol layer for edge resync and dominant or recessive classes, and the core for stuffing, CRC15, arbitration read-back, and the sample point. An external transceiver is required. CAN is optional coverage, not the hero.

Required:

- The transceiver connection the demo will use, without naming a part that v0.3 does not name.
- The stuffing, CRC15, and sample-point behaviour the firmware will implement, from a source named in this file.

Do not add a bit rate here. The figure in v0.3 section 6.3 is an estimate. CRC15 is in scope for the 16-bit unit. The polynomial is not recorded in v0.3 and does not belong here until the named source states it.
