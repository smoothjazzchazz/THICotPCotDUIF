# UART

status: missing

Blocks a UART program being treated as tested, and blocks demos 1, 2, and 3 at the freeze. v0.3 assigns UART receive to the symbol layer and UART transmit to the TX table. Framing and parity are core work. The study condition already stated in v0.3 is ±3% baud error. That condition is not a framing specification.

Required:

- The frame the firmware will send and check (fields and parity), from a source named in this file.
- The independent reference the directed test will compare against.

Do not add bit timings or electrical levels here. They are not in v0.3 as a specification.
