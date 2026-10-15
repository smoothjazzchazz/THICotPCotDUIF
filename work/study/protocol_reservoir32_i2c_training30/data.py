"""Matched fitting data and disjoint final seeds; unchanged I2C traffic recipe."""
import json
from pathlib import Path
import numpy as np
from .receiver import ARCHITECTURE_HASH
from work.study.protocol_reservoir64.data import load_split, RESERVED
from work.study.protocol_reservoir64_training30.data import cases as previous_cases
PROFILES = ('i2c',)


def load_config(output, profile):
    if profile != 'i2c': raise ValueError('I2C-only experiment')
    config=json.loads((Path(output)/'config/i2c.json').read_text())
    assert config['architecture_hash']==ARCHITECTURE_HASH
    return config


def cases(profile, split):
    if profile != 'i2c':
        raise ValueError('I2C-only experiment')
    if split == 'dev':
        return previous_cases(profile, split)
    if split != 'final':
        raise ValueError('unsupported split')
    base = 4290000
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
    if profile == 'i2c':
        specs += [('stop_then_read', random(64 if split == 'final' else 16), dict(repeated=False)),
                  ('unrelated_address', b'\x10\x00\xff\x40', dict(address=0x35))]
    result = [dict(dict(name=name, payload=payload, valid=True, seed=base + 1 + i), **kw)
              for i,(name,payload,kw) in enumerate(specs)]
    if split != 'final':
        assert all(RESERVED not in c['payload'] for c in result)
    return result
