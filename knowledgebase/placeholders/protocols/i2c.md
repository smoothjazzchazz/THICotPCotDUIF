# I2C

status: missing

documentation_status: acquired
implementation_evidence_status: missing
electrical_evidence_status: missing

Checked reference: [I2C guide](../../protocols/i2c.md), NXP UM10204 rev. 7.0 §3.1 and §6.1/Tables 10–11; [source register I1](../../protocols/sources/README.md#i2c). Source filing dated 12 October 2026 supplies protocol rules and timing requirements, not evidence that project pads or firmware meet them.

Blocks I2C firmware being treated as tested, and blocks any electrical-compliance sentence. v0.3 allows START, STOP, and bit classes from the symbol layer, with address, ACK, and clock stretch on the core. Pad behaviour is **[VERIFY]**. See [../hardware/ihp-cmos5l-pads.md](../hardware/ihp-cmos5l-pads.md).

Required:

- The address, ACK, and clock-stretch behaviour the firmware will implement, and whether the ACK uses a reflex-table entry (v0.31) or core sequencing.
- Confirmation, in the pad placeholder, of open-drain release with an external pull-up, before compliance is claimed.

Source speed/timing requirements are in the guide. No operating bus speed or pull-up component value has been selected or verified for the reference hardware.
