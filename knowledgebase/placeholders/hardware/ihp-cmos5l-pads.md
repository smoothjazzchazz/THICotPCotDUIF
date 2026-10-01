# IHP CMOS5L pads

status: missing

Blocks G0. v0.3 risk 4 and the open-drain note in section 5.1: I2C and USB electrical behaviour must not be promised until pad behaviour is checked. Also blocks any I2C or USB compliance sentence at the 4 Jan freeze.

Required:

- Whether a CMOS5L pad can drive 0 and release (output enable low) for open-drain with an external pull-up.
- What the pad does and does not support for I2C and for USB low-speed levels and pull-ups.

No pad voltage, drive strength, or leakage number belongs here until it is copied from a source the team names in this file.
