# Board clock

status: missing

Blocks any claimed clock frequency, and blocks treating a 48 MHz USB bit grid as available. v0.3 section 6.2 marks the actual board clock **[VERIFY]**. Section 11 asks whether the board can supply 48 MHz or another integer-friendly clock. The template `CLOCK_PERIOD` of 20 ns is a flow setting, not a measurement.

Required:

- The clock the board actually supplies.
- Whether 48 MHz, or another clock that divides the USB low-speed bit time, is available.

Do not record 50 MHz as the board clock in this file.
