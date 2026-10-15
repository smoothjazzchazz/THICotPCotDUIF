# UART

status: missing

documentation_status: acquired
implementation_evidence_status: missing

Checked references: [UART guide](../../protocols/uart.md), TI SPRUGP1 §2.4/Fig. 2-3 and §3.8/Table 3-12; [source register U1–U3](../../protocols/sources/README.md#uart). Source filing dated 12 October 2026 supplies framing/error behavior; it does not qualify firmware or historical experiments.

Blocks a UART program being treated as tested. UART is a stepping-stone protocol: transmit via the TX table, receive via the boring settings file plus firmware. It is not the hero demo. v0.3's ±3% baud-error trace is still a study input. It is not a framing specification, and it is not a score to win.

Required:

- Select and record the firmware's frame profile (fields, parity, baud, error/recovery policy) against the named source. The studies' 8N1/8E1 profiles are documented, not automatically adopted firmware.
- The independent reference the directed test will compare against.

Sourced protocol behavior belongs in the linked guide. A selected baud or electrical interface remains a project choice requiring independent verification.
