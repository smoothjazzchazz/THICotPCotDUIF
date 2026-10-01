# I2C

status: missing

Blocks I2C firmware being treated as tested, and blocks any electrical-compliance sentence. v0.3 allows START, STOP, and bit classes from the symbol layer, with address, ACK, and clock stretch on the core. Pad behaviour is **[VERIFY]**. See [../hardware/ihp-cmos5l-pads.md](../hardware/ihp-cmos5l-pads.md).

Required:

- The address, ACK, and clock-stretch behaviour the firmware will implement, and whether the ACK uses a reflex-table entry (v0.31) or core sequencing.
- Confirmation, in the pad placeholder, of open-drain release with an external pull-up, before compliance is claimed.

Do not add a bus speed or a pull-up value here.
