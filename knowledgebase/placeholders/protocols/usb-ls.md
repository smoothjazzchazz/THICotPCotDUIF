# USB low-speed

status: missing

documentation_status: acquired_for_low_speed_reference
implementation_evidence_status: missing
electrical_evidence_status: missing

Checked reference: [USB low-speed guide](../../protocols/usb-ls.md), USB 2.0 chapters 5, 7–9 and reviewed errata/ECNs; [source register B1–B8](../../protocols/sources/README.md#usb). Source filing dated 12 October 2026 supplies packet fields and CRC conventions. Full applicable supplement review remains necessary for electrical qualification or expanded USB scope.

Blocks the USB low-speed exchange being treated as electrically real, and blocks any compliance sentence. If simulated, the symbol layer names J, K, and SE0 and the program does NRZI, unstuffing, and CRC. USB low-speed is a simulation unless pad checks pass. It is not the hero. The hero is a loaded temporal line code. Pad levels and pull-ups are **[VERIFY]**. The board clock is a separate placeholder.

Required:

- Implement and independently verify a declared simulated exchange against the named source, including endpoint profile, fields, CRC, handshake timing, retry and reset/device-state behavior. The current NRZI diagnostic is not that implementation.
- Pad and clock placeholders resolved before any on-silicon claim.

CRC5 and CRC16 are in scope for the 16-bit unit. Polynomials, initialization, finalization, and wire order are now sourced in the guide from USB 2.0 §8.3.5. Their presence does not establish a working CRC unit or USB packet implementation. Existing study gates remain unchanged.
