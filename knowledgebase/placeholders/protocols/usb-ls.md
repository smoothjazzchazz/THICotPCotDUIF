# USB low-speed

status: missing

Blocks the USB low-speed exchange being treated as electrically real, and blocks any compliance sentence. If simulated, the symbol layer names J, K, and SE0 and the program does NRZI, unstuffing, and CRC. USB low-speed is a simulation unless pad checks pass. It is not the hero. The hero is a loaded temporal line code. Pad levels and pull-ups are **[VERIFY]**. The board clock is a separate placeholder.

Required:

- The packet fields the simulated exchange will check, from a source named in this file.
- Pad and clock placeholders resolved before any on-silicon claim.

CRC5 and CRC16 are in scope for the 16-bit unit. Polynomials are not recorded in v0.3 and do not belong here until the named source states them. Do not add bit timings beyond the study conditions already in v0.3 section 7.
