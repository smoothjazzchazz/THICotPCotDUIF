"""Separate offline clock/data generator and a live pull-low/release bus master."""
import numpy as np
from work.model.stream_reservoir import NONE, BIT0, START, STOP, FALL


def generate(payload, seed, low=10, high=10, address=0x32):
    """Labeled training traffic; target ACK/read data are generated off-line only."""
    rng = np.random.default_rng(seed)
    lines = [(1, 1)] * 12
    def hold(scl, sda, ticks):
        lines.extend([(scl, sda)] * ticks)
    def clock(bit, stretch=0):
        hold(0, bit, low + int(rng.integers(-2, 3)) + stretch)
        hold(1, bit, high + int(rng.integers(-2, 3)))
    def start():
        hold(0, 1, low)
        hold(1, 1, high)
        hold(1, 0, high)
    def octet(value):
        for shift in range(7, -1, -1):
            clock((int(value) >> shift) & 1)
    start()
    octet(address << 1)
    clock(0)
    for value in payload:
        octet(value)
        clock(0, stretch=6)
    start()  # Repeated START, without an artificial idle delimiter.
    octet((address << 1) | 1)
    clock(0)
    for i, value in enumerate(payload):
        octet(value)
        clock(int(i == len(payload) - 1))
    hold(0, 0, low)
    hold(1, 0, high)
    hold(1, 1, high + 12)
    array = np.array(lines, dtype=np.uint8)
    labels = np.zeros(len(lines), dtype=np.int64)
    for t in range(1, len(lines)):
        before, now = lines[t - 1], lines[t]
        if before[0] and now[0] and before[1] != now[1]:
            labels[t] = START if now[1] == 0 else STOP
        elif before[0] == 0 and now[0] == 1:
            labels[t] = BIT0 + now[1]
        elif before[0] == 1 and now[0] == 0:
            labels[t] = FALL
    return dict(lines=array, labels=labels, metadata=dict(seed=seed, address=address,
                expected=list(payload), source_status='assumed profile, unverified'))


class BusMaster:
    """Interactive peer; released SCL may stay low, and ACK/read bits come from bus.

    The payload is private stimulus state. Only the yielded drive pair reaches
    the emulator. One bus observation is sent back after each resolved tick.
    """
    def __init__(self, payload, low=10, high=10, address=0x32, repeated=True, malformed=False,
                 jitter=False, disturbance=False):
        self.payload = bytes(payload)
        self.low, self.high, self.address = low, high, address
        self.repeated, self.malformed = repeated, malformed
        self.jitter, self.disturbance = jitter, disturbance
        self.rng = np.random.default_rng(90123)
        self.acks, self.read, self.stretches = [], [], []
        self.done, self.timeout, self.tick = False, False, 0
        self.g = self.transaction()
        self.drive = next(self.g)

    def observe(self, bus):
        self.tick += 1
        if self.done:
            return
        try:
            self.drive = self.g.send(bus)
        except StopIteration:
            self.done, self.drive = True, (False, False)

    def hold(self, n, scl_low, sda_low):
        last = (1, 1)
        for _ in range(n):
            last = yield bool(scl_low), bool(sda_low)
        return last

    def raise_clock(self, sda_low):
        waits = 0
        while True:
            bus = yield False, bool(sda_low)
            if bus[0]:
                break
            waits += 1
            if waits >= 64:
                self.timeout = True
                return bus
        if waits:
            self.stretches.append(waits)
        return bus

    def bit(self, bit):
        low = int(self.rng.integers(8, 13)) if self.jitter else self.low
        high = int(self.rng.integers(8, 13)) if self.jitter else self.high
        yield from self.hold(low, True, bit == 0)
        first = yield from self.raise_clock(bit == 0)
        sample = first[1]
        for h in range(high - 1):
            bus = yield False, bit == 0
            if h == (high - 1) // 2:
                sample = bus[1]
        return sample

    def start(self):
        yield from self.hold(self.low, True, False)
        yield from self.raise_clock(False)
        yield from self.hold(self.high - 1, False, False)
        yield from self.hold(self.high, False, True)

    def stop(self):
        yield from self.hold(self.low, True, True)
        yield from self.raise_clock(True)
        yield from self.hold(self.high - 1, False, True)
        yield from self.hold(self.high, False, False)

    def write(self, value):
        for shift in range(7, -1, -1):
            yield from self.bit((value >> shift) & 1)
        ack = (yield from self.bit(1)) == 0
        self.acks.append(ack)
        return ack

    def transaction(self):
        yield from self.hold(12, False, False)
        if self.disturbance:
            yield from self.hold(256, False, False)
            for _ in range(32):
                yield from self.hold(1, False, True)
                yield from self.hold(1, False, False)
        if self.malformed:
            yield from self.start()
            for bit in (0, 1, 1, 0):
                yield from self.bit(bit)
            yield from self.stop()
        yield from self.start()
        addressed = yield from self.write(self.address << 1)
        if addressed:
            for value in self.payload:
                if not (yield from self.write(value)):
                    break
        if not self.repeated:
            yield from self.stop()
        yield from self.start()
        addressed = yield from self.write((self.address << 1) | 1)
        if addressed:
            for i in range(len(self.payload)):
                value = 0
                for _ in range(8):
                    value = (value << 1) | (yield from self.bit(1))
                self.read.append(value)
                yield from self.bit(int(i == len(self.payload) - 1))
        yield from self.stop()
        yield from self.hold(24, False, False)
