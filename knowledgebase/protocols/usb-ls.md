# USB low-speed: packets inside host-controlled transactions

## Overview and scope

USB is a host-scheduled bus. A line-code decoder is only the first layer: a device also needs packet validation, endpoint state, handshakes, retries, control requests, and descriptors. This reference covers conventional low-speed device behavior, not USB-C/Power Delivery, a hub implementation, or high-speed signaling. [B1 chapters 5, 7–9; source links](sources/README.md#usb)

Low-speed devices use control and interrupt transfers, not bulk or isochronous transfers. Low-speed control endpoints use an 8-byte maximum payload; interrupt endpoints may specify up to 8 bytes. A larger transfer is split into packets. Full-speed and high-speed have different timing, sizes, and features; they cannot be implemented by simply changing the clock of this profile. [B1 §5.4, §5.5.3, §5.6, §5.7.3, §5.8, §7.1.11]

For orientation, USB 2.0 defines low-speed at 1.5 Mbit/s, full-speed at 12 Mbit/s, and high-speed at 480 Mbit/s. Only the first is detailed here. “Interrupt” still means host polling: a low-speed interrupt endpoint requests a period in the 10–255 ms range. The host may service it more frequently, and bus errors or the absence of a pending host request affect delivery; this is not a device-generated interrupt wire. [B1 §5.7.4, §7.1.11]

## Line states, encoding, and packet boundaries

At low speed, J is D− high/D+ low and K is the opposite. Idle is J. SE0 has both lines low; SE1 has both high and is not a valid data state. The low-speed attachment pull-up is on D−. These logical descriptions do not establish pad voltage, impedance, or pull-up compliance. [B1 §7.1.5–7.1.7, Table 7-2; B4 resistor ECN]

NRZI sends a zero by changing J/K and a one by retaining the previous state. The low/full-speed SYNC pattern is `K J K J K J K K`. Insert a zero after each run of six ones before NRZI encoding, starting with SYNC: its final one contributes to the run. Stuffing continues across field boundaries and through the last CRC bit, including a required stuffed zero immediately before EOP. Receive in reverse order: line states → NRZI bits → unstuffed bits → fields. [B1 §7.1.8–7.1.10]

Low/full-speed EOP is SE0 for two bit times followed by J for one bit time, then release. Do not interpret sustained SE0 as repeated packets: reset uses extended SE0. Receiver acceptance must account for the dribble allowance immediately before EOP, not reject every elongated final bit. [B1 §7.1.7.4.1, §7.1.7.5, §7.1.9.1]

## Fields and CRC conventions

After SYNC, each packet starts with an 8-bit PID: four identifying bits and their complement. Validate both halves. An IN/OUT/SETUP token carries PID, 7-bit address, 4-bit endpoint, and CRC5. A data packet carries PID, payload, and CRC16. A handshake contains PID and no CRC. EOP ends each packet. Address, endpoint, and payload bits travel least-significant bit first; CRC serialization requires the convention below. [B1 §8.1–8.4]

| CRC | Protected bits | Polynomial, top term omitted | Initial state | Final XOR |
| --- | --- | --- | --- | --- |
| Token CRC5 | Address then endpoint, 11 bits | `0x05`: x⁵+x²+1 | `0x1F` | `0x1F` |
| Data CRC16 | Payload only, including zero-length payload | `0x8005`: x¹⁶+x¹⁵+x²+1 | `0xFFFF` | `0xFFFF` |

**Specification convention:** feed protected bits in wire order into a left-shifting register, XOR the incoming bit with the old top bit, shift, and conditionally XOR the polynomial. Complement the final register and send its most-significant bit first. No extra reflection is applied in this convention. The raw post-CRC receiver residues are `0x0C` and `0x800D`. CRC excludes SYNC, PID, stuffed bits, and EOP. [B1 §8.3.5–8.3.5.2, p. 198]

**Equivalent software convention, derived:** right-shift using reflected polynomials `0x14` and `0xA001`, with the same initial/final XOR values; emit the complemented result least-significant bit first. For CRC16, this means low byte first, each byte LSB first. Do not reflect a result again or mix the two conventions. The accompanying [example checker](verify.py) compares both methods and verifies the specification residues.

## Transactions, retries, and device state

OUT is host token → host data → device handshake. IN is host token → device data or NAK/STALL → host ACK after valid data. NAK means temporarily unable to transfer; STALL denotes a halted/error condition; corrupted packets generally receive no acceptance handshake. DATA0/DATA1 sequencing prevents a lost ACK from delivering the same data twice: retry the same payload and PID, recognize and ACK a valid duplicate, and do not deliver it again. Advance state only at the correct successful-transaction boundary. [B1 §8.4.5–8.6.4; B2 correction to Figs. 8-31/8-32]

A control transfer starts with SETUP and an eight-byte DATA0 request, may have a data stage, and ends with an opposite-direction status stage using DATA1. SETUP initializes the control transfer's sequence. Enumeration requires reset/default-address handling, endpoint zero, descriptors, SET_ADDRESS, and SET_CONFIGURATION; SET_ADDRESS takes effect after its status stage, not on receipt of SETUP. Descriptor contents remain a project/device-class choice. [B1 §8.5.3, §8.6.1, §9.1–9.4, especially §9.4.6]

Keep-alive, suspend/resume, and host/hub handling of low-speed traffic are separate from payload decoding. A full-speed PRE packet enables downstream low-speed forwarding through a full-/low-speed hub; it is not a prefix generated by the low-speed function. Low-speed links receive keep-alive signaling rather than ordinary SOF packets. [B1 §7.1.7.6, §7.1.12, §8.6.5]

## Timing requirements

- Nominal low-speed rate: 1.5 Mbit/s. The ±1.5% transmit-rate allowance applies to a low-speed function; host/hub clock requirements differ. [B1 §7.1.11]
- Interpacket delay is measured from EOP's SE0-to-J transition to the next packet's J-to-K transition. Minimum: 2 bit times. Device response maxima depend on the measurement point: 6.5 bit times at a detachable-cable device's B receptacle, or less than 7.5 at a captive cable's A plug. Host response maximum: 7.5 at its port pins. These are not arbitrary firmware delays. [B1 §7.1.18.1]
- Reset is extended SE0, at least 10 ms; root-port reset must span at least 50 ms under the continuity rules in §7.1.7.5. The 10 ms reset recovery requirement is distinct from device reset-detection time. [B1 §7.1.7.5]

For electrical design, use the full chapter 7 tables and applicable ECNs. This note does not select supply levels, power limits, or pull-up tolerances. The [source register](sources/README.md#usb) records the corrections checked, including descriptor-version clarification and later electrical changes.

## Worked examples and implementation checklist

Derived example: request the first eight device-descriptor bytes at default address zero:

```text
SETUP token: PID 0x2D, address 0, endpoint 0, CRC5 wire bits 01000
DATA0: PID 0xC3, payload 80 06 00 01 00 00 08 00, CRC bytes EB 94
device ACK: PID 0xD2
IN token -> device DATA1 containing requested descriptor bytes -> host ACK
OUT token -> host DATA1 with empty payload (CRC bytes 00 00) -> device ACK
```

Each line's packet still needs SYNC, stuffing, NRZI, and EOP. Descriptor response bytes are deliberately not invented. For a bitstream fragment `111111`, stuffing yields `1111110`; with prior state J, the encoded fragment is `J J J J J J K`. For real packets, carry the run count across boundaries, including the final SYNC one.

- Verify complemented PID, token/address matching, CRCs, stuffing violations, malformed/truncated EOP, and no side effects from invalid packets.
- Exercise NAK, STALL, lost ACK, duplicate DATA PID, SETUP restart, reset, enumeration, and suspend/resume with an independent peer.
- Measure response timing and specify endpoint/class descriptors before naming a simulation a USB exchange.
- The existing module is still a diagnostic; filing sources does not enable its packet path or pass UART/I2C prerequisites. See [audit](model-audit.md) and [remaining evidence](../placeholders/protocols/usb-ls.md).
