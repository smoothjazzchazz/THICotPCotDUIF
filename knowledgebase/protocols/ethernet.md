# Ethernet: MAC frames and 10 Mbit signaling

## Overview and edition boundary

Ethernet separates the MAC, which handles frames and medium access, from the PHY, which handles the physical link. A correct Manchester waveform alone is not a working Ethernet link. The project still limits Ethernet to analysis and simulation. [E1 clauses 3, 4, 7, 14; source links](sources/README.md#ethernet)

The detailed reference is **IEEE 802.3-2012**, an older edition retrieved as a publisher-authored document from a third-party mirror after official automated access failed. Its title/copyright and relevant clauses were inspected; no publisher checksum was available to authenticate the mirror. This is not a claim to have checked the latest Ethernet standard. Official access and the inspected 2013 errata are recorded in the source register. Higher-speed PHYs and tagged/envelope frames are outside this guide's detailed profile.

Variant map: 10BASE-T is the selected twisted-pair case; 100BASE-TX and 1000BASE-T have their own PHY definitions (E1 clauses 24–25 and 40). Shared MAC framing does not make their waveforms scaled versions of 10BASE-T. Their detailed encoding, timing, and negotiation are not covered by this guide.

## Basic frame and bit order

For an untagged basic frame, the transmitted sequence is:

```text
preamble 7 bytes | SFD 1 | destination 6 | source 6 | length/type 2
                | payload + pad 46..1500 | FCS 4 | interpacket gap
```

Preamble is conventionally represented as seven `0x55` bytes, then SFD `0xD5`; their chronological bits differ from reading the hex digits MSB first. The MAC frame begins at destination address and ends with FCS: minimum 64 bytes, maximum 1518 for this basic profile. Preamble/SFD and the gap are not counted in that frame length. Short payloads need padding before the FCS is calculated. Tagged/envelope rules differ; 1518 is not a universal maximum for all Ethernet formats. [E1 §3.1–3.2.9, §4.2.5, Table 4-2]

Ordinary octets transmit LSB first. Length/type uses its high-order octet first: values ≤1500 indicate payload length; values ≥1536 indicate EtherType. Do not assign the intervening values either meaning. Destination/source addresses use six octets; the destination's first transmitted bit selects individual/group addressing. [E1 §3.2.3, §3.2.6, §3.3]

## FCS without bit-order ambiguity

FCS covers destination through payload **and padding**. It excludes preamble, SFD, FCS itself, and gap. The polynomial is x³²+x²⁶+x²³+x²²+x¹⁶+x¹²+x¹¹+x¹⁰+x⁸+x⁷+x⁵+x⁴+x²+x+1, represented without its leading term as `0x04C11DB7`. [E1 §3.2.9]

The specification complements the first 32 message bits, forms the polynomial remainder after multiplication by x³², complements the remainder, and transmits coefficients x³¹ through x⁰. Ordinary-byte LSB-first serialization must not be blindly applied to that mathematical remainder. [E1 §3.2.9, §3.3]

Equivalent derived software convention: reflected CRC-32, right-shift polynomial `0xEDB88320`, initial register `0xFFFFFFFF`, final XOR `0xFFFFFFFF`; process every protected octet LSB first and append the resulting integer low byte first. Those bytes each serialize LSB first. In common CRC parameter terminology this is `refin=true, refout=true`; do not add another reflection to a right-shift implementation. The [checker](verify.py) compares this representation with a direct polynomial division and Python's CRC32.

## 10BASE-T signaling and link behavior

The selected line code is Manchester: zero has a high-to-low midpoint transition, one low-to-high, with polarity interpreted at the stated differential interface. At 10 Mbit/s the nominal bit is 100 ns and half-bit 50 ns. A 40 MHz simulation has four ticks per bit and two per half-bit; that is a simulation choice, not an achieved chip frequency. [E1 §7.3.1.1, Fig. 7-10; clause 14]

10BASE-T uses separate transmit and receive twisted pairs. Its idle is not an endless stream of encoded zero or one bits. Without Auto-Negotiation, transmit idle includes silence and link-test pulses on a nominal 16 ms ±8 ms cadence. Link-integrity monitoring, start/end behavior, electrical drive, receive qualification, and isolation are PHY responsibilities. Auto-Negotiation uses the clause 28 pulse sequence instead. A GPIO Manchester trace does not provide these functions. [E1 §14.1.1.3, §14.2.1.1, §14.2.1.7–14.2.1.8, §14.3; E3 §5.3.1, §5.5.1.3]

## Medium access, timing, and errors

Transmit interpacket spacing is 96 bit times: 9.6 µs at 10 Mbit/s. Received spacing can shrink in a network; the transmitter requirement is not a universal receiver rejection threshold. [E1 Table 4-2 and note 1]

Half-duplex uses carrier sense, collision detection, jam, and randomized exponential backoff. For 10 Mbit/s, the slot is 512 bit times, jam size 32 bits, and attempt limit 16. Full-duplex does not use CSMA/CD collision/backoff. A valid received Ethernet frame does not generate an Ethernet data ACK analogous to I2C/USB; link-layer collision retry is distinct from higher-layer delivery acknowledgment. [E1 §4.1, §4.2.3.2, §4.2.3.4, Table 4-2]

Detect bad FCS, partial octets, inconsistent length, and undersized frames; do not confuse link presence with frame validity. Higher-level protocols and application processing determine the meaning of a payload. [E1 §3.4, §4.2.4]

## Worked frame and project checklist

Derived simulation fixture, not an assigned application protocol:

```text
DA       02 00 00 00 00 01
SA       02 00 00 00 00 02
Length   00 03
Data     41 42 43                 (three opaque MAC-client bytes)
Pad      43 zero bytes            (padding content chosen for this fixture)
FCS      2A 8A 5D CD              (reflected integer 0xCD5D8A2A)
```

This is 60 protected bytes and 64 bytes including FCS, plus eight preamble/SFD bytes on transmission. Minimum ideal transmit gap is 384 ticks at the chosen 40 MHz simulation clock. Changing a payload/pad bit without recomputing FCS must fail validation; preamble is outside FCS. No claim is made that the opaque three-byte payload implements an upper-layer protocol.

- Test padding boundaries, FCS/wire order, SFD detection, truncation, bad FCS, idle/gap handling, and variable payload lengths.
- State full/half-duplex assumptions; test collision/jam/backoff only if implementing half-duplex MAC behavior.
- Keep the planned TX-table/byte-streaming simulation and host-supplied FCS explicit. The reference 16-bit CRC unit does not implement this CRC32.
- A silicon proposal would separately need a qualified PHY/interface, link behavior, timing, I/O and isolation evidence, and a MAC/FCS resource plan. See [remaining Ethernet evidence](../placeholders/protocols/ethernet.md).
