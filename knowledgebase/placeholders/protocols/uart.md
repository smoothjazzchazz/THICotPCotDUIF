# UART

status: missing

Blocks a UART program being treated as tested. UART is a stepping-stone protocol: transmit via the TX table, receive via the boring settings file plus firmware. It is not the hero demo. v0.3's ±3% baud-error trace is still a study input. It is not a framing specification, and it is not a score to win.

Required:

- The frame the firmware will send and check (fields and parity), from a source named in this file.
- The independent reference the directed test will compare against.

Do not add bit timings or electrical levels here. They are not in v0.3 as a specification.
