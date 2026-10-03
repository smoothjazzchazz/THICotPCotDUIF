# Python models

The planned golden model of the core and symbol layer will be the single ISA
reference described in v0.3 section 7. The current model is only a small starting
transmitter model, not the complete transmitter specification or ISA reference.

`transmit_simple_model.py` provides `Transmitter` and a symbol table containing
IDs `0` through `15`. Each symbol plays its four-bit binary value, most significant
bit first: for example, `2: [0, 0, 1, 0]` and `15: [1, 1, 1, 1]`. It uses one
output lane and integer levels, emitting one bit per tick for four ticks.

- `Transmitter(capacity=2)` starts empty. Capacity must be a positive integer and
  counts all unfinished symbols, including the currently playing symbol.
- `send(symbol_id)` queues a valid integer ID and returns `True`. It returns
  `False` without adding the request when full. Invalid IDs raise `ValueError`,
  even when full.
- `step()` advances one simulated tick and returns `0` or `1`. Requests play in
  arrival order without interruption or an inserted idle tick. A completed
  request is removed immediately, freeing capacity on its final tick.
- `step()` returns `None` when empty. **`None` is a software marker, not an
  electrical output state**; it does not represent low, high, or high impedance.
  There are no real-time sleeps.

Run this example from the repository root with Python 3.10 or newer:

```sh
python3 -B - <<'PY'
from work.model.transmit_simple_model import Transmitter

transmitter = Transmitter(capacity=3)
for symbol_id in [2, 2, 0]:
    assert transmitter.send(symbol_id)

levels = []
while True:
    level = transmitter.step()
    if level is None:
        break
    levels.append(level)
print(levels)  # [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0]
PY
```

Run the small model tests from the repository root:

```sh
python3 -B -m unittest discover -s work/model -p 'test_*.py' -v
```
