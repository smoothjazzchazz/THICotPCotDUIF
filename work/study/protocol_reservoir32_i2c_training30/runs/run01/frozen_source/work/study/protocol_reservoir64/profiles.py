"""Loaded profile tables; node dynamics and input interface stay invariant."""
import json
from pathlib import Path
from work.model.stream_reservoir import ARCHITECTURE_HASH

PROFILES = {
    'uart_n': dict(program='uart_echo', parity=False, bit_ticks=16, capacity=32,
                   deadline_ticks=1024, clock_ratio=[.97, 1.03], cell_jitter_ticks=1),
    'uart_e': dict(program='uart_echo', parity=True, bit_ticks=16, capacity=32,
                   deadline_ticks=1024, clock_ratio=[.97, 1.03], cell_jitter_ticks=1),
    'i2c': dict(program='i2c_store_read', address=0x32, capacity=4096, stretch_ticks=18,
                setup_deadline_ticks=6, low_ticks=[8, 12], high_ticks=[8, 12]),
}


def write_configs(root):
    directory = Path(root) / 'config'
    directory.mkdir(exist_ok=False)
    for name, config in PROFILES.items():
        (directory / f'{name}.json').write_text(json.dumps(dict(
            profile=name, architecture_hash=ARCHITECTURE_HASH, decision_margin=.15,
            weight_files=[f'models/{name}/seed_{seed}/selected.npz' for seed in (11, 29, 47)],
            source_status='explicit experimental assumptions; protocol source still missing',
            **config), indent=2) + '\n')


def load_config(root, name):
    config = json.loads((Path(root) / 'config' / f'{name}.json').read_text())
    if config['architecture_hash'] != ARCHITECTURE_HASH:
        raise ValueError('configuration would change the frozen architecture')
    return config
