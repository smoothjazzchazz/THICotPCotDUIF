"""Synthetic sampled-waveform contracts. Metadata is for offline scoring only."""
import numpy as np

TASKS = ("pulse", "biphase", "clockdata", "context")
CONDITIONS = ("clean", "jitter", "glitches", "mixed", "novel", "idle", "recovery")
QUIET = 10
WORDS = ("001101", "110001")
UNKNOWN_WORDS = ("010101", "101001", "000101", "111001")
NOVEL_WORDS = ("001001", "110101", "011101", "100001")
TRANSFER_WORDS = ("10110010", "01101010")


def encode(task, cls, rng, novel=False):
    """Return (packed-lane value, nominal duration) runs, before jitter/noise."""
    if task == "pulse":
        widths = ((3, 8), (8, 3))[cls] if cls != 7 else rng.choice(
            [(3, 5), (5, 3), (8, 5), (5, 8)] if novel else [(3, 3), (8, 8), (5, 5)])
        return [(1, int(widths[0])), (0, 3), (1, int(widths[1]))]
    if task in ("biphase", "clockdata"):
        word = WORDS[cls] if cls != 7 else rng.choice(NOVEL_WORDS if novel else UNKNOWN_WORDS)
        runs = [(1, 3), (0, 3)] if task == "biphase" else [(3, 3), (1, 3)]
        for bit in map(int, word):
            runs.extend([(1-bit, 3), (bit, 3)] if task == "biphase" else
                        [(2*bit, 3), (1+2*bit, 3)])
        # Last bit is 1, so completion is observable when the final high ends.
        return runs
    if task == "context":
        first = int(rng.integers(2))
        bits = [first, *rng.integers(2, size=4).tolist(), first ^ (cls if cls != 7 else int(rng.integers(2))), 0, 1]
        widths = [3+3*b for b in bits]
        if cls == 7:
            if novel:
                widths[int(rng.choice([0, 5]))] = 9
            else:
                bits[6:] = rng.choice([[0, 0], [1, 0], [1, 1]]).tolist()
                widths = [3+3*b for b in bits]
        return [(v, n) for i, w in enumerate(widths) for v, n in
                ([(1, w), (0, 3)] if i < 7 else [(1, w)])]
    if task == "transfer":
        word = TRANSFER_WORDS[cls] if cls != 7 else rng.choice(
            ["10010010", "01001010", "10100010", "01111010"] if novel else
            ["11110010", "00101010", "10001010", "01010010"])
        level = int(rng.integers(2))
        # Lane 1 is an in-band activity level, not a hidden boundary annotation.
        # Each 1 toggles lane 0; each 0 holds. Last absolute level is uninformative.
        runs = [(2+level, 3)]
        for b in word:
            level ^= int(b)
            runs.append((2+level, 3))
        return runs
    raise ValueError(task)


def make_stream(task, seed, condition="clean", bursts=72):
    rng = np.random.default_rng(seed)
    jitter = condition in ("jitter", "mixed", "recovery")
    noise = .01 if condition in ("glitches", "mixed", "recovery") else 0.
    order = np.resize([0, 1, 7], bursts)
    rng.shuffle(order)
    samples = [0] * int(rng.integers(10, 31))
    events = []
    for i, c in enumerate(order):
        start = len(samples)
        runs = encode(task, int(c), rng, novel=condition == "novel")
        for v, n in runs:
            length = max(2, n + (int(rng.integers(-1, 2)) if jitter else 0))
            samples.extend([v] * length)
        end = len(samples)
        events.append({"class": int(c), "start": start, "end": end, "group": i//4})
        gap = int(rng.integers(10, 81)) if condition == "idle" else int(rng.integers(14, 29))
        samples.extend([0] * gap)
    clean = np.asarray(samples, dtype=np.uint8)
    x = clean.copy()
    if noise:
        for lane in range(2):
            x ^= (rng.random(len(x)) < noise).astype(np.uint8) << lane
    crop = 0
    if condition == "recovery":
        # Receiver starts in an active first burst, not at an oracle reset.
        crop = int(rng.integers(events[0]["start"]+1, events[0]["end"]))
        # One dropout forces a malformed burst; intended event remains in truth.
        target = events[len(events)//2]
        pos = (target["start"] + target["end"])//2
        x[pos:pos+5] = 0
        x, clean = x[crop:], clean[crop:]
        events = [{**e, "start": e["start"]-crop, "end": e["end"]-crop}
                  for e in events if e["start"] >= crop]
    return {"task": task, "seed": seed, "condition": condition, "samples": x.tolist(),
            "events": events, "crop": crop, "ticks": len(x)}


def dataset(task, base, count, bursts, conditions=CONDITIONS):
    return [make_stream(task, base+1000*i+j, c, bursts)
            for i,c in enumerate(conditions) for j in range(count)]


def training(task, base, bursts=144):
    return dataset(task, base, 1, bursts, CONDITIONS[:4])
