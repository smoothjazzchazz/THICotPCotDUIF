"""Offline references, independent of emitters, receiver and transmitter code.

These check the declared assumptions, not an external standard. They never
supply events or data to the learned emulator during qualification.
"""


def uart_decode(levels, parity=False, period=16.):
    values, errors, ends = [], [], []
    t, previous = 1, int(levels[0])
    width = 11 if parity else 10
    while t < len(levels):
        if previous == 1 and int(levels[t]) == 0:
            origin = t
            positions = [origin + int((cell + .5) * period) for cell in range(width)]
            if positions[-1] >= len(levels):
                errors.append(dict(tick=origin, reason='truncated'))
                break
            bits = [int(levels[pos]) for pos in positions]
            reason = None
            if bits[0] != 0 or bits[-1] != 1:
                reason = 'framing'
            elif parity and (sum(bits[1:10]) & 1):
                reason = 'parity'
            if reason:
                errors.append(dict(tick=origin, reason=reason))
            else:
                values.append(sum(bits[i + 1] << i for i in range(8)))
                ends.append(positions[-1])
            # Resume in the stop cell, so a back-to-back falling edge is visible.
            t = positions[-1]
        previous = int(levels[t])
        t += 1
    return dict(bytes=values, errors=errors, completion_ticks=ends)


def i2c_decode(lines):
    transactions, current, accumulator, count = [], None, 0, 0
    previous = tuple(int(x) for x in lines[0])
    for tick, pair in enumerate(lines[1:], 1):
        scl, sda = map(int, pair)
        pscl, psda = previous
        if pscl == scl == 1 and sda != psda:
            if current is not None:
                current.update(end=tick, partial_bits=count)
                transactions.append(current)
            current = dict(start=tick, bytes=[], acks=[], end=None, partial_bits=0) if sda == 0 else None
            accumulator, count = 0, 0
        elif pscl == 0 and scl == 1 and current is not None:
            if count < 8:
                accumulator = 2 * accumulator + sda
                count += 1
            else:
                current['bytes'].append(accumulator)
                current['acks'].append(sda == 0)
                accumulator, count = 0, 0
        previous = scl, sda
    if current is not None:
        current.update(partial_bits=count)
        transactions.append(current)
    return transactions


def bus_events(lines):
    """Independent edge reference for scoring an interactive bus after inference."""
    events = []
    clock, data = map(int, lines[0])
    for tick in range(1, len(lines)):
        next_clock, next_data = map(int, lines[tick])
        if clock == next_clock == 1 and data != next_data:
            events.append((tick, 3 if next_data == 0 else 4))
        elif next_clock != clock:
            events.append((tick, 1 + next_data if next_clock else 5))
        clock, data = next_clock, next_data
    return events


def usb_unstuff_nrzi(symbols, initial='J'):
    """Line-code diagnostic only; no packet/CRC/handshake assumptions."""
    result, previous, ones, expect_zero = [], initial, 0, False
    for symbol in symbols:
        if symbol not in ('J', 'K'):
            raise ValueError('non-data line state')
        bit = int(symbol == previous)
        previous = symbol
        if expect_zero:
            if bit:
                raise ValueError('stuff violation')
            expect_zero, ones = False, 0
            continue
        result.append(bit)
        ones = ones + 1 if bit else 0
        expect_zero = ones == 6
    if expect_zero:
        raise ValueError('missing stuffed zero')
    return result
