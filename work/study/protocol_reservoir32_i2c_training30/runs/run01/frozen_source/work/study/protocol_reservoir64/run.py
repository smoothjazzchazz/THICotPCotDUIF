"""Generation, fitting, frozen confirmation and observation-only replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import numpy as np
from work.model.stream_reservoir import ARCHITECTURE, ARCHITECTURE_HASH
from .data import PROFILES, save_split, load_split
from .training import SEEDS, EPOCHS, CHUNK, LR, fit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_paths():
    return sorted([*HERE.glob('*.py'), HERE / 'README.md', HERE / 'requirements.txt',
                   ROOT / 'work/model/stream_reservoir.py',
                   ROOT / 'work/model/transmit_simple_model.py'])


def generate(output):
    output.mkdir(parents=True, exist_ok=False)
    from .profiles import write_configs
    write_configs(output)
    write_json(output / 'plan.json', dict(architecture=ARCHITECTURE, architecture_hash=ARCHITECTURE_HASH,
        seeds=SEEDS, epochs=EPOCHS, chunk=CHUNK, lr=LR, profiles=PROFILES,
        training_streams=12, dev_streams=4, split_seed_bases=dict(train=10000, dev=20000, final=90000),
        final_random_bytes=2048, final_long_bytes=1024, decision_margin=.15,
        acceptance='every seed, every valid condition, both arithmetic modes; exact bytes/events/deadlines',
        source_hashes={str(p.relative_to(ROOT)): sha(p) for p in source_paths()},
        python=sys.executable, python_version=platform.python_version(), numpy=np.__version__,
        blas_threads=os.environ.get('OPENBLAS_NUM_THREADS'), command=sys.argv))
    for profile in PROFILES:
        for split in ('train', 'dev'):
            save_split(output, profile, split)
    print(f'Generated independent training/development streams: {output}', flush=True)


def train(output):
    if (output / 'freeze.json').exists():
        raise ValueError('this run is frozen; no further fitting')
    for profile in PROFILES:
        train_data, dev_data = load_split(output, profile, 'train'), load_split(output, profile, 'dev')
        if len(train_data) != 12 or len(dev_data) != 4:
            raise ValueError('generation must complete before fitting')
        for seed in SEEDS:
            directory = output / 'models' / profile / f'seed_{seed}'
            if (directory / 'fit.json').exists():
                continue
            fit(train_data, dev_data, directory, seed)
        directory = output / 'models' / profile / 'readout_only'
        if not (directory / 'fit.json').exists():
            fit(train_data, dev_data, directory, SEEDS[0], readout_only=True)


def freeze(output):
    if (output / 'freeze.json').exists():
        raise ValueError('already frozen')
    for profile in PROFILES:
        for variant in [*(f'seed_{seed}' for seed in SEEDS), 'readout_only']:
            if not (output / 'models' / profile / variant / 'fit.json').exists():
                raise ValueError(f'incomplete fitting: {profile}/{variant}')
    sources = source_paths()
    for path in sources:
        dest = output / 'frozen_source' / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    frozen = dict(architecture_hash=ARCHITECTURE_HASH,
                  sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  artifacts={str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*'))
                             if p.is_file() and 'frozen_source' not in p.parts})
    write_json(output / 'freeze.json', frozen)
    print('Frozen sources, datasets, all weights and selection decisions', flush=True)


def verify(output):
    frozen = json.loads((output / 'freeze.json').read_text())
    if frozen['architecture_hash'] != ARCHITECTURE_HASH:
        raise ValueError('frozen architecture mismatch')
    for relative, digest in frozen['sources'].items():
        if sha(ROOT / relative) != digest:
            raise ValueError(f'frozen source changed: {relative}')
    for relative, digest in frozen['artifacts'].items():
        if sha(output / relative) != digest:
            raise ValueError(f'frozen artifact changed: {relative}')
    return frozen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('generate', 'train', 'freeze', 'evaluate', 'replay', 'verify'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--profile', choices=PROFILES, default='uart_n')
    parser.add_argument('--mode', choices=('float', 'quantized'), default='quantized')
    parser.add_argument('--seed', type=int, choices=SEEDS, default=11)
    args = parser.parse_args()
    if args.action == 'generate':
        generate(args.output)
    elif args.action == 'train':
        train(args.output)
    elif args.action == 'freeze':
        freeze(args.output)
    elif args.action == 'verify':
        verify(args.output)
        print('All frozen hashes match')
    elif args.action == 'evaluate':
        verify(args.output)
        from .evaluation import evaluate
        evaluate(args.output)
    elif args.action == 'replay':
        verify(args.output)
        from .evaluation import replay
        replay(args.output, args.profile, args.mode, args.seed)


if __name__ == '__main__':
    main()
