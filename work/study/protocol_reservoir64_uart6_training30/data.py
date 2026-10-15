"""Long continuous corpora; all teacher information stays on the training side."""
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import BIT0, START, STOP, FALL
from work.study.protocol_reservoir64.data import PROFILES, RESERVED, payload_for, load_split
from work.study.protocol_reservoir64.uart_emitter import generate as uart_generate
from work.study.protocol_reservoir64.checkers import uart_decode, i2c_decode, bus_events
from work.study.protocol_reservoir64.test_experiment import EdgeReference
from work.study.protocol_reservoir64_training30.simulation import run_i2c

PROFILES = ("uart_n", "uart_e")
BASES = dict(train=1000000, dev=40000000, final=50000000)


def transaction(profile, seed, index):
    rng = np.random.default_rng(seed)
    length = (1, 2, 4, 8, 16, 32)[index % 6]
    payload = payload_for(rng, length, index % 4)
    assert RESERVED not in payload
    if profile.startswith('uart'):
        parity = profile == 'uart_e'
        ratio = (.97, 1.03, 1., float(rng.uniform(.97, 1.03)))[index % 4]
        bad = (min(2, length - 1),) if index % 9 == 8 else ()
        stream = uart_generate(payload, seed, parity=parity, ratio=ratio,
                               jitter=index % 2, gaps=index % 3 == 1, bad_at=bad)
        # A parity error changes the observed bit label, never the intended byte.
        parity_bad = parity and index % 11 == 10
        if parity_bad:
            f = stream['frames'][0]
            pulses = np.flatnonzero(stream['labels'][f['start']:f['end'] + 1]) + f['start']
            center = pulses[9]
            # Locate the cell using the emitter's rounding schedule independently.
            clock_rng = np.random.default_rng(seed)
            elapsed = 12. + float(clock_rng.random())
            cursor = 12
            bounds = []
            for _ in range(11):
                elapsed += 16 * ratio + (int(clock_rng.integers(-1, 2)) if index % 2 else 0)
                end = round(elapsed)
                bounds.append((cursor, end))
                cursor = end
            a, b = bounds[9]
            assert a <= center < b
            stream['lines'][a:b, 0] ^= 1
            stream['labels'][center] = BIT0 + int(stream['lines'][center, 0])
            f['valid'] = False
        active = sum(f['end'] - f['start'] + 1 for f in stream['frames'])
        checked = uart_decode(stream['lines'][:, 0], parity, period=16 * ratio)
        expected = [f['value'] for f in stream['frames'] if f['valid']]
        check = dict(clean=not bad and not parity_bad, exact=checked['bytes'] == expected,
                     output_errors=checked['errors'])
        # Jitter changes true cell centers; labels must retain one pulse per cell.
        for f in stream['frames']:
            pos = np.flatnonzero(stream['labels'][f['start']:f['end'] + 1]) + f['start']
            assert len(pos) == 10 + parity
            assert stream['labels'][pos[0]] == START
            assert all(stream['labels'][t] == BIT0 + stream['lines'][t, 0] for t in pos[1:-1])
            assert stream['labels'][pos[-1]] in (STOP, 6)
        stream['metadata'].update(frames=stream['frames'], parity_bad=parity_bad)
    else:
        low, high = ((8, 8), (12, 12), (8, 12), (12, 8), (10, 10))[index % 5]
        foreign = index % 13 == 12
        malformed = index % 7 == 6
        result = run_i2c(payload, EdgeReference(delay=index % 3), low=low, high=high,
                         address=0x35 if foreign else 0x32, repeated=index % 3 != 2,
                         malformed=malformed, jitter=index % 5 == 4,
                         disturbance=index % 17 == 16, peer_seed=seed)
        lines = result['lines']
        labels = np.zeros(len(lines), dtype=np.int64)
        for t, kind in bus_events(lines):
            labels[t] = kind
        decoded = i2c_decode(lines)
        reads = [b for d in decoded if d['bytes'] and d['bytes'][0] & 1 for b in d['bytes'][1:]]
        expected = [] if foreign else list(payload)
        assert reads == expected and result['peer'].read == expected and not result['peer'].timeout
        # Exclude initial/final idle and disturbance prefixes from budget credit.
        # Low cells (including real stretching) and high clock cells are real traffic.
        start_events = np.flatnonzero(labels == START)
        stop_events = np.flatnonzero(labels == STOP)
        active = int(stop_events[-1] - start_events[-(3 if malformed else 2)] + 1)
        if malformed:
            active = int(stop_events[-1] - start_events[0] + 1)
        check = dict(clean=not malformed, exact=reads == expected,
                     stretch_waits=result['peer'].stretches, decoded=decoded)
        stream = dict(lines=lines, labels=labels, metadata=dict(expected=list(payload),
                      low=low, high=high, foreign=foreign, malformed=malformed,
                      observer_delay=index % 3, jitter=index % 5 == 4))
    stream['metadata'].update(seed=seed, transaction_ticks=active, independent_check=check)
    return stream


def generate_stream(profile, split, index, minimum):
    base = BASES[split] + PROFILES.index(profile) * 100000 + index * 1000
    lines, labels, meta, active, offset = [], [], [], 0, 0
    counter = 0
    while active < minimum:
        s = transaction(profile, base + counter, counter + index)
        meta.append(dict(offset=offset, ticks=len(s['lines']), **s['metadata']))
        lines.append(s['lines']); labels.append(s['labels'])
        active += s['metadata']['transaction_ticks']
        offset += len(s['lines'])
        counter += 1
        assert counter < 1000
    return dict(lines=np.concatenate(lines), labels=np.concatenate(labels),
                metadata=dict(seed=base, split=split, transactions=meta,
                              transaction_ticks=active, transaction_count=counter))


def save_split(output, profile, split):
    import shutil
    source = Path(__file__).parent.parent / 'protocol_reservoir64_training30/runs/run01/data' / profile / split
    shutil.copytree(source, Path(output) / 'data' / profile / split)


def cases(profile, split):
    base = BASES[split] + ('uart_n','uart_e','i2c').index(profile) * 100000 + 90000
    rng = np.random.default_rng(base)
    def random(n):
        return rng.integers(0, 256, n, dtype=np.uint8).tobytes()
    if split == 'final':
        specs = [('phrase', RESERVED, {}), ('every_byte', bytes(range(256)), {}),
                 ('random_binary', random(2048), {}), ('long_message', random(1024), {}),
                 ('repeated_patterns', b'\x00' * 128 + b'\xff' * 128 + b'\x55\xaa' * 128, {})]
        n = 128
    else:
        specs = [('random_binary', random(24), {}),
                 ('repeated_patterns', b'\x00\xff\x55\xaa' * 4, {})]
        n = 16
    specs += [('fast_clock', random(n), dict(ratio=.97, low=8, high=8)),
              ('slow_clock', random(n), dict(ratio=1.03, low=12, high=12)),
              ('jitter', random(n), dict(jitter=1)),
              ('fast_with_jitter', random(n), dict(ratio=.97, jitter=1, low=8, high=12)),
              ('slow_with_jitter', random(n), dict(ratio=1.03, jitter=1, low=12, high=8)),
              ('malformed_recovery', random(64 if split == 'final' else 16), dict(malformed=True, valid=False)),
              ('idle_and_disturbance', bytes(range(32 if split == 'final' else 16)), dict(disturbance=True, valid=False))]
    if profile.startswith('uart'):
        specs += [('gapped_frames', random(128 if split == 'final' else 16), dict(gaps=True))]
    if profile == 'i2c':
        specs += [('stop_then_read', random(64 if split == 'final' else 16), dict(repeated=False)),
                  ('unrelated_address', b'\x10\x00\xff\x40', dict(address=0x35))]
    result = [dict(dict(name=name, payload=payload, valid=True, seed=base + 1 + i), **kw)
              for i,(name,payload,kw) in enumerate(specs)]
    if split != 'final':
        assert all(RESERVED not in c['payload'] for c in result)
    return result
