"""Controllers consume timed events only. Deterministic TX is separate from emitters."""
from work.model.stream_reservoir import BIT0, BIT1, START, STOP, FALL, INVALID


class UARTController:
    def __init__(self, tx, parity=False, bit_ticks=16, capacity=32):
        self.tx, self.parity, self.bit_ticks, self.capacity = tx, parity, bit_ticks, capacity
        self.active, self.bits = False, []
        self.received, self.received_ticks, self.errors, self.overflow = [], [], [], 0
        self.busy_until, self.pending = 0, []
        self.last_event = -1

    def step(self, event, tick):
        self.pending = [end for end in self.pending if end > tick]
        if self.active and tick - self.last_event > 256:
            self.active, self.bits = False, []
            self.errors.append((tick, 'timeout'))
        if event is None:
            return
        self.last_event = tick
        if event.kind == START:
            if self.active:
                self.errors.append((tick, 'restart'))
            self.active, self.bits = True, []
        elif event.kind == INVALID:
            if self.active:
                self.errors.append((tick, 'invalid'))
            self.active, self.bits = False, []
        elif event.kind in (BIT0, BIT1) and self.active:
            self.bits.append(event.kind - BIT0)
            if len(self.bits) > 8 + self.parity:
                self.active, self.bits = False, []
                self.errors.append((tick, 'extra bit'))
        elif event.kind == STOP and self.active:
            good = len(self.bits) == 8 + self.parity
            if good and self.parity:
                good = sum(self.bits) % 2 == 0
            if good:
                value = sum(bit << i for i, bit in enumerate(self.bits[:8]))
                self.received.append(value)
                self.received_ticks.append(tick)
                self.echo(value, tick)
            else:
                self.errors.append((tick, 'length/parity'))
            self.active, self.bits = False, []

    def echo(self, value, tick):
        if len(self.pending) >= self.capacity:
            self.overflow += 1
            return
        # TX builds its own framing from recovered bytes, never generator cells.
        words = [0]
        parity = 0
        for position in range(8):
            bit = (value >> position) & 1
            words.append(bit)
            parity ^= bit
        if self.parity:
            words.append(parity)
        words.append(1)
        start = max(tick + 1, self.busy_until)
        if len(self.tx.commands) + len(words) > self.tx.capacity:
            self.overflow += 1
            return
        for index, bit in enumerate(words):
            self.tx.schedule(0, bit, True, start + index * self.bit_ticks, tick)
        self.busy_until = start + len(words) * self.bit_ticks
        self.pending.append(self.busy_until)


class I2CController:
    def __init__(self, tx, address=0x32, capacity=4096, stretch_ticks=18):
        self.tx, self.address, self.capacity = tx, address, capacity
        self.stretch_ticks = stretch_ticks
        self.storage, self.received, self.received_ticks = [], [], []
        self.state, self.next_state = 'idle', 'idle'
        self.value, self.count, self.pointer, self.tx_bit = 0, 0, 0, 0
        self.tx_seen, self.ack, self.stretch = False, False, False
        self.errors, self.overflow, self.last_event = [], 0, -1
        self.response_requests = []

    def drive(self, lane, low, tick, delay=1):
        self.tx.schedule(lane, 0, bool(low), tick + delay, tick)
        if lane == 1:
            self.response_requests.append((tick, tick + delay))

    def release(self, tick):
        self.drive(0, False, tick)
        self.drive(1, False, tick)

    def begin_read(self, tick):
        self.tx_bit, self.tx_seen = 0, False
        if self.pointer >= len(self.storage):
            self.value = 255
            self.errors.append((tick, 'read beyond recovered storage'))
        else:
            self.value = self.storage[self.pointer]
        self.pointer += 1
        self.drive(1, (self.value & 128) == 0, tick)
        self.state = 'send'

    def step(self, event, tick):
        if self.state != 'idle' and tick - self.last_event > 256:
            self.errors.append((tick, 'timeout'))
            self.release(tick)
            self.state = 'idle'
        if event is None:
            return
        self.last_event = tick
        kind = event.kind
        if kind == START:
            self.state, self.value, self.count = 'address', 0, 0
            self.release(tick)
            return
        if kind in (STOP, INVALID):
            if kind == INVALID and self.state != 'idle':
                self.errors.append((tick, 'invalid'))
            if kind == STOP and self.state in ('address', 'receive') and self.count:
                self.errors.append((tick, 'partial byte'))
            self.state = 'idle'
            self.release(tick)
            return
        if kind in (BIT0, BIT1):
            bit = kind - BIT0
            if self.state in ('address', 'receive'):
                self.value = ((self.value << 1) | bit) & 255
                self.count += 1
                if self.count == 8:
                    self.stretch = False
                    if self.state == 'address':
                        self.ack = (self.value >> 1) == self.address
                        reading = bool(self.value & 1)
                        self.next_state = ('send' if reading else 'receive') if self.ack else 'idle'
                        if self.ack:
                            self.pointer = 0
                            if not reading:
                                self.storage.clear()
                    else:
                        self.ack = len(self.storage) < self.capacity
                        self.next_state = 'receive' if self.ack else 'idle'
                        if self.ack:
                            self.storage.append(self.value)
                            self.received.append(self.value)
                            self.received_ticks.append(tick)
                            self.stretch = True
                        else:
                            self.overflow += 1
                    self.state = 'ack_setup'
            elif self.state == 'ack_clock':
                self.state = 'ack_release'
            elif self.state == 'send':
                self.tx_seen = True
            elif self.state == 'master_ack':
                self.state = 'read_next' if bit == 0 else 'idle'
        elif kind == FALL:
            if self.state == 'ack_setup':
                self.drive(1, self.ack, tick)
                if self.stretch and self.ack:
                    self.drive(0, True, tick)
                    self.drive(0, False, tick, self.stretch_ticks + 1)
                self.state = 'ack_clock'
            elif self.state == 'ack_release':
                self.drive(1, False, tick)
                self.state, self.count, self.value = self.next_state, 0, 0
                if self.state == 'send':
                    self.begin_read(tick)
            elif self.state == 'send' and self.tx_seen:
                self.tx_bit += 1
                self.tx_seen = False
                if self.tx_bit == 8:
                    self.drive(1, False, tick)
                    self.state = 'master_ack'
                else:
                    self.drive(1, not bool(self.value & (128 >> self.tx_bit)), tick)
            elif self.state == 'read_next':
                self.begin_read(tick)
