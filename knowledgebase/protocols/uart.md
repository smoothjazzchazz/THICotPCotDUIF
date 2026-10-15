# UART: asynchronous characters

## Overview and source boundary

A UART turns characters into a timed serial stream and back. The two ends agree on baud, data width, parity, and stop format; no clock wire accompanies the data. UART framing alone does not define addresses, packet lengths, acknowledgments, or retransmission. Those belong to an application protocol. [U1 §2.4, §2.5; U2, protocol overview; source links](sources/README.md#uart)

UART is a peripheral/interface family, not one universal specification covering every implementation. This guide uses TI's documented conventional, non-inverted, least-significant-bit-first framing. TI-specific FIFO, oversampling, and break behavior are examples, not mandatory architecture for this project. Logic-level UART and an RS-232 line interface are different layers: voltage conversion requires an appropriate transceiver; do not connect a modeled 0/1 signal to a cable and infer electrical compatibility. [U1 §2.4; U2; U3 §2.3]

## Signaling and framing

For the selected convention, idle is high, the start bit is low, data follows least-significant bit first, optional parity follows data, and stop is high. Stop time is part of the frame; the next start may follow immediately. An all-zero character still needs its high stop interval. [U1 §2.4, Fig. 2-3; U2]

| Project profile | Start | Data | Parity | Stop | Total |
| --- | --- | --- | --- | --- | --- |
| 8N1 | 1 low bit | 8 bits | None | 1 high bit | 10 bit periods |
| 8E1 | 1 low bit | 8 bits | Even | 1 high bit | 11 bit periods |

These are the existing study's choices, not the only UART formats. U1 describes 5–8 data bits and selectable transmitted stop formats; its receiver checks one stop bit even when more are transmitted. Do not generalize that receiver behavior to every UART. [U1 §2.4–2.5.2]

Even parity makes the total count of ones across data and parity even. Odd parity makes it odd. Parity is not a CRC and does not detect every corruption. [U1 §3.6, Table 3-9; U2]

## Timing and errors

One bit period is `1 / baud`; ideal frame duration is the number of bit periods divided by baud. The receiver synchronizes from the start edge and samples inside later cells. TI's example receiver uses a 16× clock; oversampling is an implementation choice. Baud error accumulates across a character, and allowable mismatch depends on frame length, sampling, edge uncertainty, and clock errors. The study's ±3% stimulus is not a universal UART guarantee. [U1 §2.1, §2.5.2; U2, error sources]

Keep these outcomes separate: wrong parity; low stop sample/framing error; break; and overrun because software or a buffer could not accept another character. U1's break indication uses a low input longer than a whole character; its exact threshold and recovery are peripheral-specific. A framing error is not automatically a break. [U1 §3.8, Table 3-12]

## Worked character

Derived from Fig. 2-3, for `0x53` (four data ones), the chronological cells are:

```text
                    d0 d1 d2 d3 d4 d5 d6 d7
8N1: idle 1 | start 0 | 1  1  0  0  1  0  1  0 | stop 1
8E1: idle 1 | start 0 | 1  1  0  0  1  0  1  0 | parity 0 | stop 1
```

Changing the parity cell to 1 creates an even-parity error. Changing the stop cell to 0 creates a framing error at the stop sample. At a chosen simulation baud of 9600, these ideal frames take approximately 1.041667 ms and 1.145833 ms respectively; this is arithmetic, not a chip speed claim.

## Implementation checklist and project implications

- Declare baud, polarity, bit order, width, parity, stop duration, and break/recovery policy at both ends.
- Test all byte values, adjacent frames, idle gaps, parity errors, bad stops, truncated frames, prolonged low, and overflow. Measure mismatch tolerance with the actual sampling scheme.
- Score complete received characters independently from symbol recognition and verify transmitted waveforms independently from controller requests.
- Specify any message format, response latency, flow control, and retry behavior as an application contract.

The existing profiles match 8N1/8E1 in intent. Their 16 ticks per bit, queue size, and echo deadline remain project choices. See the [audit](model-audit.md) and [remaining UART evidence](../placeholders/protocols/uart.md).
