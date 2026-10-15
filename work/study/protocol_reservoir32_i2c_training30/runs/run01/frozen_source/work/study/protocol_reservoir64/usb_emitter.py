"""USB source gate and separately generated six-one NRZI diagnostic.

Packet fields, CRC polynomials and handshake timing have no filed source. Do not
turn this diagnostic into a falsely named USB packet implementation.
"""

MISSING = ('checked packet field layout', 'CRC5/CRC16 polynomials and bit order',
           'sync/EOP acceptance and handshake timing', 'configured-device transaction profile')


class MissingUSBSource(RuntimeError):
    pass


def nrzi_diagnostic(bits):
    symbols, level, run = [], 0, 0
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError('binary bits required')
        if bit == 0:
            level ^= 1
            run = 0
        else:
            run += 1
        symbols.append(('J', 'K')[level])
        if run == 6:
            level ^= 1
            symbols.append(('J', 'K')[level])
            run = 0
    return symbols


def generate_packet(*args, **kwargs):
    raise MissingUSBSource('; '.join(MISSING))


class USBPeer:
    def __init__(self, *args, **kwargs):
        raise MissingUSBSource('; '.join(MISSING))


def training_gate(qualified):
    if not qualified:
        return dict(status='not_started', reason='UART/I2C frozen end-to-end gate failed',
                    additional_source_blocks=list(MISSING), fit_steps=0)
    return dict(status='blocked_missing_source', reason='; '.join(MISSING), fit_steps=0)
