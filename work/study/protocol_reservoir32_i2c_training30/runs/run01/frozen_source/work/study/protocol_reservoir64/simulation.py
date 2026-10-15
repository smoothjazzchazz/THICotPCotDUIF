"""One continuous two-line update order; labels live only in offline scoring."""
import numpy as np
from work.model.transmit_simple_model import ScheduledLineTransmitter
from .controllers import UARTController, I2CController
from .i2c_emitter import BusMaster


def run_uart(lines, receiver, parity=False, tail=1200, config=None):
    tx = ScheduledLineTransmitter()
    config = config or dict(parity=parity, bit_ticks=16, capacity=32)
    controller = UARTController(tx, **{k: config[k] for k in ('parity', 'bit_ticks', 'capacity')})
    observations, outputs, enables, events = [], [], [], []
    for tick in range(len(lines) + tail):
        levels, oe = tx.step(tick)
        observed = tuple(lines[tick]) if tick < len(lines) else (1, 1)
        event = receiver.step(observed, tick)
        controller.step(event, tick)
        observations.append(observed)
        outputs.append(levels[0] if oe[0] else 1)
        enables.append(oe)
        if event is not None:
            events.append(event)
    return dict(lines=np.array(observations, dtype=np.uint8),
                output=np.array(outputs, dtype=np.uint8), enables=np.array(enables),
                events=events, controller=controller, tx=tx)


def run_i2c(payload, receiver, low=10, high=10, address=0x32, repeated=True, malformed=False,
            jitter=False, disturbance=False, config=None):
    peer = BusMaster(payload, low=low, high=high, address=address,
                     repeated=repeated, malformed=malformed, jitter=jitter, disturbance=disturbance)
    tx, rows, events, enables, peer_drives = ScheduledLineTransmitter(), [], [], [], []
    config = config or dict(address=0x32, capacity=4096, stretch_ticks=18)
    controller = I2CController(tx, **{k: config[k] for k in ('address', 'capacity', 'stretch_ticks')})
    budget = (len(payload) * 2 + 6) * 9 * (low + high + 30) + 3000
    for tick in range(budget):
        levels, oe = tx.step(tick)
        # Both outputs are open drain; a high-enabled drive is a model error.
        if any(oe[i] and levels[i] != 0 for i in range(2)):
            raise AssertionError('I2C target attempted active-high drive')
        drive = peer.drive
        bus = tuple(int(not (drive[i] or oe[i])) for i in range(2))
        event = receiver.step(bus, tick)
        controller.step(event, tick)
        peer.observe(bus)
        rows.append(bus)
        enables.append(oe)
        peer_drives.append(drive)
        if event is not None:
            events.append(event)
        if peer.done:
            break
    return dict(lines=np.array(rows, dtype=np.uint8), events=events, controller=controller,
                tx=tx, peer=peer, enables=np.array(enables), peer_drives=np.array(peer_drives))
