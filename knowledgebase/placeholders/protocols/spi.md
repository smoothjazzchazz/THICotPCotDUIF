# SPI

status: missing

Blocks SPI master and SPI slave firmware being treated as tested (Tier 1), and blocks the demos that use them. Under v0.31 there is no bypass: SPI runs through the degenerate symbol-layer configuration, and the slave's first-response path is a reflex-table entry. The spec does not fix mode, bit order, or a clock divider.

Required:

- The SPI mode, bit order, and chip-select polarity the firmware will implement.
- Separate notes for master and slave, including the reflex entry the slave response uses.

Do not add an SCK frequency here. Rates in v0.3 section 6.3 are estimates, and v0.31 section 8 expects the slave maximum to drop; state it only after STA.
