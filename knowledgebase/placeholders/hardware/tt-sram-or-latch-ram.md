# Program RAM: SRAM or latch macro

status: missing

Blocks the G0 RAM decision. v0.3 says to evaluate Tiny Tapeout SRAM or latch examples at G0, and marks availability on CMOS5L as **[VERIFY]**. Flop-based RAM is the likely area bottleneck. Mitigations in order start with a latch or SRAM macro, then 64 words.

Required:

- Whether a SRAM or latch-based memory macro is available to this CMOS5L Tiny Tapeout flow.
- If it is, the instance the synthesis variant should use. If it is not, say so and stop. Do not invent a macro.

Until this file changes, G0 may synthesize flop RAMs at 64 and 128 words only.
