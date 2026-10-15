# I2C: shared clock and data

## Overview

I2C carries addressed, byte-oriented transactions on SCL and SDA. A controller starts a transfer and generates clocks; the current transmitter supplies data and the current receiver supplies ACK/NACK. A target can be a receiver or transmitter within the same combined transaction. Primary authority: [I1, NXP UM10204 rev. 7.0](sources/README.md#i2c), especially §3.1 and §6.

This guide details the Standard/Fast/Fast-mode Plus signaling family. High-speed and Ultra Fast-mode have distinct rules; do not apply this guide's bidirectional open-drain assumptions indiscriminately to them. See I1 §3.2, §5.3, and §5.4 for those variants.

## Signals, bytes, and ownership

For the shared-bus, stretch-capable profile used here, SDA and SCL use open-drain/open-collector behavior with pull-ups: drive low or release, never actively drive the bus high. I1 §3.1.1 permits a push-pull controller SCL in a single-controller application only when no device can stretch; that exception is not the project's stretching profile. A released signal is only high once the actual bus rises. Data remains stable while SCL is high, except for START/STOP conditions. START is SDA falling while SCL is high; STOP is SDA rising while SCL is high. A repeated START begins another addressed phase without releasing bus ownership through STOP. [I1 §3.1.1–3.1.4]

Each byte has eight data bits, most-significant bit first, followed by a ninth clock for ACK/NACK. The transmitter releases SDA for that ninth clock. The receiver drives low for ACK or leaves SDA released for NACK; the controller still generates the clock. On a read, the controller is the data receiver and NACKs the final byte before STOP or repeated START. NACK can indicate no matching target, refusal/not-ready, capacity exhaustion, or normal end of a read; it is not always a fault. [I1 §3.1.5–3.1.6]

For 7-bit addressing, the first byte is `(address << 1) | R/W`, with 0 meaning controller writes and 1 meaning controller reads. Reserved addresses and 10-bit addressing need separate handling; an 8-bit address byte is not the same value as the 7-bit target address. [I1 §3.1.10–3.1.12]

## Stretching, arbitration, and recovery

A target may hold SCL low to delay progress. The controller must observe released SCL becoming high before treating a clock as high. A fixed wait followed by assumed-high sampling is insufficient. In a multi-controller bus, clock synchronization and arbitration also depend on actual line levels. A transmitter intending a high SDA but observing low during arbitration loses and stops driving data without corrupting the winner. Arbitration is not byte-level ACK handling. [I1 §3.1.7–3.1.9]

A project timeout is a local recovery policy, not a general I2C maximum stretch time. For stuck SDA, I1 recommends nine recovery clocks; if SDA does not release, reset or power-cycle the affected devices. If SCL is stuck low, use hardware reset or power cycling. Do not claim a clock sequence repairs every stuck bus. [I1 §3.1.9, §3.1.16]

## Timing and electrical requirements

Selected limits from I1 §6.1, Table 11 (pp. 44–45); these are source requirements, not achieved board timings:

| Parameter | Standard | Fast | Fast-mode Plus |
| --- | --- | --- | --- |
| Maximum SCL frequency | 100 kHz | 400 kHz | 1000 kHz |
| Minimum SCL low | 4.7 µs | 1.3 µs | 0.5 µs |
| Minimum SCL high | 4.0 µs | 0.6 µs | 0.26 µs |
| Minimum data setup | 250 ns | 100 ns | 50 ns |
| Maximum rise time | 1000 ns | 300 ns | 120 ns |
| Minimum STOP-to-START bus-free time | 4.7 µs | 1.3 µs | 0.5 µs |

Frequency alone is insufficient: meet START/STOP setup and hold, data/ACK valid delays, fall time, bus capacitance, thresholds, and all applicable Table 10/11 footnotes. In particular, Table 11's zero minimum data-hold entry does not permit changing SDA before SCL has crossed its low threshold. Pull-ups depend on capacitance, rise time, supply, and sink capability; no resistor value is selected here. [I1 §6.1, §7.1]

## Worked combined transaction

Project example: a target at 7-bit address `0x32` stores `0xA5` and returns it on a read. Storage/echo semantics are an application choice, not defined by I2C. Chronological bytes and ninth-clock owners:

```text
START
controller -> 0x64 (01100100) ; target ACK
controller -> 0xA5 (10100101) ; target ACK
repeated START
controller -> 0x65 (01100101) ; target ACK
target     -> 0xA5 (10100101) ; controller NACK
STOP
```

For a stretch during the write ACK, the target holds SCL low, establishes ACK on SDA while SCL is low, then releases SCL when ready. The controller waits for actual SCL high. Releasing ACK must respect the ninth clock's falling edge. [I1 §3.1.6, §3.1.9, Fig. 6]

## Implementation checklist and project implications

- Verify byte order, 7-bit/address-byte distinction, ninth-clock ownership, read-final NACK, repeated START, unmatched address, and early STOP.
- Test stretch at variable durations and verify the controller observes the resolved bus; label any timeout and single-controller restriction.
- For multi-controller claims, add arbitration and synchronization tests; for electrical claims, verify pads, pull-ups, thresholds, rise/fall, and loading independently.
- Treat setup violations, partial bytes, unknown traffic, and stuck-bus recovery separately from successful payload transfer.

The study's `0x32`, store/read behavior, tick durations, and 64-tick peer timeout are project assumptions. Digital wired-AND resolution is not an analog pad model. See the [audit](model-audit.md) and [remaining I2C evidence](../placeholders/protocols/i2c.md).
