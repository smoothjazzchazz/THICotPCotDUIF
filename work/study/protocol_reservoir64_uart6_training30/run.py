"""Reproducible generation, audited training, freeze and untouched confirmation."""
import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import ARCHITECTURE_HASH, ARCHITECTURE
from work.study.protocol_reservoir64.profiles import write_configs
from work.study.protocol_reservoir64.run import verify as verify_original
from .data import PROFILES, BASES, save_split, load_split
from .training import EPOCHS, CHUNK, SEEDS, MULTIPLIERS, fit_job, write_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = HERE.parent / 'protocol_reservoir64'
ORIGINAL = OLD / 'runs/run01'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_paths():
    directories = [HERE, OLD, HERE.parent/'protocol_reservoir64_training30', ROOT/'work/model']
    return sorted(set([p for d in directories for p in d.glob('*.py')] + [HERE/'README.md']))


def preservation_manifest():
    paths = [p for d in (OLD, HERE.parent/'protocol_reservoir64_training30', HERE.parent/'protocol_reservoir32_i2c_training30') for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [ROOT / 'work/model/stream_reservoir.py', ROOT / 'work/model/transmit_simple_model.py']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}


def check_preservation(output):
    recorded = json.loads((output / 'original_preservation.json').read_text())
    current = preservation_manifest()
    if current != recorded:
        raise AssertionError('original experiment/source changed')
    verify_original(ORIGINAL)
    return len(recorded)


def generate(output):
    verify_original(ORIGINAL)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'original_preservation.json', preservation_manifest())
    write_configs(output)
    for profile in PROFILES:
        path=output/'config'/f'{profile}.json'
        config=json.loads(path.read_text())
        config['weight_files']=[f'models/{profile}/{v}/selected.npz' for v in [*(f'seed_{s}' for s in SEEDS),'previous_recipe_11']]
        write_json(path,config)
    write_json(output / 'plan.json', dict(architecture=ARCHITECTURE, architecture_hash=ARCHITECTURE_HASH,
        seeds=SEEDS, epochs=EPOCHS, chunk=CHUNK, batch_size=12, lr=.003,
        loss_multipliers=MULTIPLIERS.tolist(), previous_recipe_seed=11,
        live_case_seed_bases=BASES, copied_corpus_seed_bases=dict(train=1000000,dev=2000000), unique_transaction_ticks_minimum_per_stream=32768,
        selection='lexicographic strict exchanges, exact exchanges, aligned bytes, boundary F1, macro F1, negative false rate, negative loss',
        python=sys.executable, python_version=platform.python_version(), numpy=np.__version__,
        platform=platform.platform(), blas_threads=os.environ.get('OPENBLAS_NUM_THREADS'),
        command=sys.argv, generation_sources={str(p.relative_to(ROOT)):sha(p) for p in source_paths()}))
    exposure = {}
    for profile in PROFILES:
        for split in ('train', 'dev'):
            save_split(output, profile, split)
        data = load_split(output, profile, 'train')
        original = json.loads((ORIGINAL / 'models' / profile / 'seed_11/fit.json').read_text())
        ticks = sum(len(s['labels']) for s in data)
        transaction_ticks = sum(s['metadata']['transaction_ticks'] for s in data)
        maximum = max(len(s['labels']) for s in data)
        updates = ((maximum + CHUNK - 1) // CHUNK) * EPOCHS
        assert transaction_ticks >= 4 * original['training_ticks']
        assert updates >= 2 * original['steps']
        exposure[profile] = dict(original_unique_nonpadding_ticks=original['training_ticks'],
            original_updates=original['steps'], unique_nonpadding_ticks=ticks,
            unique_transaction_ticks=transaction_ticks, excluded_idle_ticks=ticks-transaction_ticks,
            unique_transactions=sum(s['metadata']['transaction_count'] for s in data),
            padded_batch_ticks=maximum * 12, padding_ticks=maximum * 12 - ticks,
            batch_size=12, chunk=CHUNK, epochs=EPOCHS, optimizer_updates=updates,
            repeated_nonpadding_presentations=ticks * EPOCHS,
            repeated_transaction_presentations=transaction_ticks * EPOCHS,
            transaction_to_original_nonpadding_ratio=transaction_ticks / original['training_ticks'],
            update_ratio=updates / original['steps'])
        prior = json.loads((HERE.parent/'protocol_reservoir64_training30/runs/run01/exposure.json').read_text())[profile]
        assert transaction_ticks >= prior['unique_transaction_ticks'] and updates >= prior['optimizer_updates']
        exposure[profile]['previous30_transaction_ticks'] = prior['unique_transaction_ticks']
        exposure[profile]['previous30_updates'] = prior['optimizer_updates']
        print(json.dumps(dict(profile=profile, **exposure[profile])), flush=True)
    write_json(output / 'exposure.json', exposure)


def jobs(output):
    return [(str(output), profile, seed, 'weighted') for profile in PROFILES for seed in SEEDS] + [
            (str(output), profile, 11, 'original') for profile in PROFILES]


def parallel(function, items, workers):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(function, items):
            print(json.dumps(dict(completed=result)), flush=True)


def train(output, workers):
    if (output / 'freeze.json').exists():
        raise ValueError('already frozen')
    audit = json.loads((output / 'audit/preflight.json').read_text())
    assert audit['passed']
    for name, digest in audit['sources'].items():
        assert sha(ROOT / name) == digest, f'change since preflight: {name}'
    check_preservation(output)
    parallel(fit_job, jobs(output), workers)


def freeze(output):
    assert not (output / 'freeze.json').exists()
    check_preservation(output)
    selections = {}
    for _, profile, seed, recipe in jobs(output):
        variant = f'seed_{seed}' if recipe == 'weighted' else 'previous_recipe_11'
        directory = output / 'models' / profile / variant
        fit = json.loads((directory / 'fit.json').read_text())
        selections[profile+'/'+variant] = dict(epoch=fit['best_epoch'],seed=seed,recipe=recipe,selection_key=fit['history'][fit['best_epoch']-1]['selection_key'])
        assert fit['epochs'] == 30 and len(fit['history']) == 30
        for epoch in range(1, 31):
            assert (directory / f'epoch_{epoch:02d}.npz').exists()
            assert (directory / f'optimizer_{epoch:02d}.npz').exists()
    write_json(output/'selection.json',selections)
    write_json(output/'shared_architecture.json',dict(architecture_hash=ARCHITECTURE_HASH,receiver_source='work/model/stream_reservoir.py',receiver_source_sha256=sha(ROOT/'work/model/stream_reservoir.py'),same_class_for_uart_i2c=True))
    sources = source_paths()
    for p in sources:
        destination = output / 'frozen_source' / p.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, destination)
    write_json(output / 'freeze.json', dict(architecture_hash=ARCHITECTURE_HASH,
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
        artifacts={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*'))
                   if p.is_file() and 'frozen_source' not in p.parts and not p.name.endswith('.log')}))
    print('All candidates, selection, configurations, corpora and sources frozen.', flush=True)


def verify(output):
    frozen = json.loads((output / 'freeze.json').read_text())
    assert frozen['architecture_hash'] == ARCHITECTURE_HASH
    for p,d in frozen['sources'].items():
        assert sha(ROOT / p) == d, f'source changed: {p}'
        assert sha(output / 'frozen_source' / p) == d
    for p,d in frozen['artifacts'].items():
        assert sha(output / p) == d, f'artifact changed: {p}'
    n = check_preservation(output)
    print(f'Frozen hashes match; {n} original files preserved.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('generate','audit','train','freeze','evaluate','report','verify'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    if args.action == 'generate': generate(args.output)
    elif args.action == 'audit':
        from .audit import preflight
        preflight(args.output)
    elif args.action == 'train': train(args.output, args.workers)
    elif args.action == 'freeze': freeze(args.output)
    elif args.action == 'verify': verify(args.output)
    elif args.action == 'evaluate':
        verify(args.output)
        from .evaluation import evaluate
        evaluate(args.output, args.workers)
    elif args.action == 'report':
        from .report import report
        report(args.output)


if __name__ == '__main__': main()
