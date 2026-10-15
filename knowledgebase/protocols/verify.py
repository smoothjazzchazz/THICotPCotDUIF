"""Check documentation examples and local provenance, not protocol implementations.

Run with Python's standard library from any directory. No network or file writes.
CRC checks compare the specification's serial convention with reflected software
and, for Ethernet, direct polynomial division and the standard library.
"""

import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote
import zlib


ROOT = Path(__file__).resolve().parent


def wire_bits(data):
    return [(octet >> bit) & 1 for octet in data for bit in range(8)]


def serial_register(bits, width, polynomial):
    mask = (1 << width) - 1
    register = mask
    for bit in bits:
        feedback = (register >> (width - 1)) ^ bit
        register = (register << 1) & mask
        if feedback:
            register ^= polynomial
    return register


def reflected_crc(bits, width, polynomial):
    mask = (1 << width) - 1
    register = mask
    for bit in bits:
        feedback = (register & 1) ^ bit
        register >>= 1
        if feedback:
            register ^= polynomial
    return register ^ mask


def check_usb(bits, width, polynomial, reflected, expected, residue):
    value = serial_register(bits, width, polynomial) ^ ((1 << width) - 1)
    emitted = [(value >> bit) & 1 for bit in reversed(range(width))]
    software = reflected_crc(bits, width, reflected)
    assert software == expected
    assert emitted == [(software >> bit) & 1 for bit in range(width)]
    assert serial_register(bits + emitted, width, polynomial) == residue
    return emitted


def check_examples():
    # Fixed expected values are the worked examples printed in the guides.
    bits = wire_bits(b"S")
    assert bits == [1, 1, 0, 0, 1, 0, 1, 0]
    assert sum(bits) % 2 == 0
    assert len([0] + bits + [1]) == 10
    assert len([0] + bits + [0, 1]) == 11
    assert sum(bits + [1]) % 2 == 1  # deliberately wrong even parity
    assert round(10 / 9600 * 1000, 6) == 1.041667
    assert round(11 / 9600 * 1000, 6) == 1.145833

    assert (0x32 << 1, (0x32 << 1) | 1) == (0x64, 0x65)
    assert f"{0x64:08b}" == "01100100"
    assert f"{0x65:08b}" == "01100101"
    assert f"{0xA5:08b}" == "10100101"

    token_crc = check_usb([0] * 11, 5, 0x05, 0x14, 0x02, 0x0C)
    assert token_crc == [0, 1, 0, 0, 0]
    setup = bytes.fromhex("80 06 00 01 00 00 08 00")
    check_usb(wire_bits(setup), 16, 0x8005, 0xA001, 0x94EB, 0x800D)
    check_usb([], 16, 0x8005, 0xA001, 0, 0x800D)
    check_usb(wire_bits(b"123456789"), 16, 0x8005, 0xA001, 0xB4C8, 0x800D)
    for pid in (0x2D, 0xC3, 0xD2):
        assert ((pid >> 4) ^ (pid & 15)) == 15
    assert (0x94EB).to_bytes(2, "little").hex() == "eb94"
    # Six ones retain J; the required stuffed zero changes it to K.
    state = 0
    symbols = []
    for bit in [1] * 6 + [0]:
        state ^= 1 - bit
        symbols.append("JK"[state])
    assert symbols == list("JJJJJJK")

    protected = bytes.fromhex("0200000000010200000000020003") + b"ABC" + bytes(43)
    assert len(protected) == 60
    expected = 0xCD5D8A2A
    assert zlib.crc32(protected) == expected
    assert reflected_crc(wire_bits(protected), 32, 0xEDB88320) == expected
    assert expected.to_bytes(4, "little").hex() == "2a8a5dcd"
    # IEEE 3.2.9's mathematical construction, independent of the shift-register
    # implementation above: complement the first 32 bits, append 32 zero bits,
    # divide by the full polynomial, then complement the remainder.
    message = wire_bits(protected)
    dividend = 0
    for index, bit in enumerate(message):
        dividend = (dividend << 1) | (bit ^ int(index < 32))
    dividend <<= 32
    divisor = (1 << 32) | 0x04C11DB7
    while dividend.bit_length() >= divisor.bit_length():
        dividend ^= divisor << (dividend.bit_length() - divisor.bit_length())
    result = dividend ^ 0xFFFFFFFF
    assert result == 0x5451BAB3
    assert [(result >> bit) & 1 for bit in reversed(range(32))] == wire_bits(
        expected.to_bytes(4, "little")
    )
    corrupted = bytes([protected[0] ^ 1]) + protected[1:]
    assert zlib.crc32(corrupted) != expected
    assert zlib.crc32(bytes([0x55]) * 7 + bytes([0xD5]) + protected) != expected
    assert 40_000_000 // 10_000_000 == 4
    assert 96 * 4 == 384

    for name, fragments in {
        "uart.md": ["1  1  0  0  1  0  1  0", "1.041667", "1.145833"],
        "i2c.md": ["0x64 (01100100)", "0x65 (01100101)", "0xA5 (10100101)"],
        "usb-ls.md": ["CRC5 wire bits 01000", "CRC bytes EB 94", "CRC bytes 00 00"],
        "ethernet.md": ["2A 8A 5D CD", "0xCD5D8A2A", "384 ticks"],
    }.items():
        text = (ROOT / name).read_text()
        assert all(fragment in text for fragment in fragments), name
    print("PASS: UART/I2C example arithmetic, USB CRC/PID/NRZI examples, Ethernet FCS/wire order")


def check_files():
    manifest = json.loads((ROOT / "sources/manifest.json").read_text())
    records = manifest["sources"]
    assert len({record["id"] for record in records}) == len(records)
    retained = []
    for record in records:
        if record["sha256"] is not None:
            assert re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
        if record["retained_path"]:
            path = ROOT / "sources" / record["retained_path"]
            data = path.read_bytes()
            assert len(data) == record["bytes"]
            assert hashlib.sha256(data).hexdigest() == record["sha256"]
            retained.append(path)
    assert set((ROOT / "sources").glob("*.pdf")) == set(retained)

    # Simple inline relative links in this documentation set, including fragments.
    documents = list(ROOT.rglob("*.md"))
    placeholders = ROOT.parent / "placeholders/protocols"
    for name in ("uart", "i2c", "usb-ls", "ethernet"):
        path = placeholders / f"{name}.md"
        content = path.read_text()
        assert "status: missing\n" in content
        assert "documentation_status: acquired" in content
        documents.append(path)
    count = 0
    for path in documents:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" in target:
                continue
            filename, _, fragment = unquote(target).partition("#")
            destination = path.parent / filename if filename else path
            assert destination.exists(), (path, target)
            if fragment and destination.suffix == ".md":
                headings = re.findall(r"^#+\s+(.+)$", destination.read_text(), re.M)
                anchors = [re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-") for h in headings]
                assert fragment in anchors, (path, target)
            count += 1
    print(f"PASS: {len(records)} source records, {len(retained)} retained PDF checksum, {count} local links, four unresolved evidence statuses")


if __name__ == "__main__":
    check_examples()
    check_files()
