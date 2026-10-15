"""Disjoint whole-stream splits. Reserved demonstration bytes are final-only."""
import json
from pathlib import Path
import numpy as np
from . import uart_emitter, i2c_emitter
from .checkers import uart_decode, i2c_decode

PROFILES = ('uart_n', 'uart_e', 'i2c')
RESERVED = b'House Improvement Committee'


def payload_for(rng, length, kind):
    if kind == 0:
        return rng.integers(0, 256, length, dtype=np.uint8).tobytes()
    if kind == 1:
        return bytes([int(rng.integers(0, 256))]) * length
    if kind == 2:
        return (bytes([0, 255, 0, 255, 85, 170]) * (length // 6 + 1))[:length]
    return bytes((i * 17 + int(rng.integers(0, 256))) & 255 for i in range(length))


def generate_split(profile, split):
    number, base = (12, 10000) if split == 'train' else (4, 20000)
    streams, checks = [], []
    for index in range(number):
        seed = base + PROFILES.index(profile) * 100 + index
        rng = np.random.default_rng(seed)
        payload = payload_for(rng, 32 if profile.startswith('uart') else 16, index % 4)
        if RESERVED in payload:
            raise AssertionError('reserved phrase leaked into fitting data')
        if profile.startswith('uart'):
            stream = uart_emitter.generate(payload, seed, parity=profile == 'uart_e',
                ratio=float(rng.uniform(.97, 1.03)), jitter=1, gaps=index % 2 == 1,
                bad_at=(7,) if index % 4 == 3 else ())
            checked = uart_decode(stream['lines'][:, 0], parity=profile == 'uart_e',
                                  period=16 * stream['metadata']['ratio'])
            expected = [v for i, v in enumerate(payload) if not (index % 4 == 3 and i == 7)]
            # Malformed recovery can legitimately reacquire inside a damaged frame;
            # only independently check clean generation for exact frame contents.
            valid = index % 4 == 3 or checked['bytes'] == expected
        else:
            stream = i2c_emitter.generate(payload, seed)
            checked = i2c_decode(stream['lines'])
            valid = len(checked) == 2 and checked[0]['bytes'] == [0x64] + list(payload) and checked[1]['bytes'] == [0x65] + list(payload)
        if not valid:
            raise AssertionError(f'independent emitter validation failed: {profile} {seed}')
        checks.append(dict(seed=seed, clean_exact_checked=not (profile.startswith('uart') and index % 4 == 3),
                           checker=checked))
        stream['metadata'].update(split=split, stream_id=f'{profile}-{split}-{seed}')
        streams.append(stream)
    return streams, checks


def save_split(root, profile, split):
    directory = Path(root) / 'data' / profile / split
    directory.mkdir(parents=True)
    streams, checks = generate_split(profile, split)
    for stream in streams:
        np.savez_compressed(directory / f"{stream['metadata']['seed']}.npz",
                            lines=stream['lines'], labels=stream['labels'],
                            metadata=json.dumps(stream['metadata']))
    (directory / 'checker_results.json').write_text(json.dumps(checks, indent=2) + '\n')


def load_split(root, profile, split):
    streams = []
    for path in sorted((Path(root) / 'data' / profile / split).glob('*.npz')):
        with np.load(path, allow_pickle=False) as saved:
            streams.append(dict(lines=saved['lines'], labels=saved['labels'], metadata=json.loads(str(saved['metadata']))))
    return streams
