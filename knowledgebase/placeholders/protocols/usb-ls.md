# USB low-speed

status: missing

Blocks the USB low-speed demo being treated as electrically real, and blocks any compliance sentence. v0.3 targets device-side USB low-speed on silicon (Tier 2): symbol layer for J, K, SE0, sync, and EOP; core for NRZI, unstuffing, CRC5 and CRC16, and handshake. Simulation of token-in and handshake-out is the demo even if electrical checks fail. Section 11 leaves USB low-speed versus CAN as the hero stretch. Pad levels and pull-ups are **[VERIFY]**. The board clock is a separate placeholder.

Required:

- The packet fields the simulated exchange will check, from a source named in this file.
- Pad and clock placeholders resolved before any on-silicon claim.

CRC5 and CRC16 are in scope for the 16-bit unit. Polynomials are not recorded in v0.3 and do not belong here until the named source states them. Do not add bit timings beyond the study conditions already in v0.3 section 7.
