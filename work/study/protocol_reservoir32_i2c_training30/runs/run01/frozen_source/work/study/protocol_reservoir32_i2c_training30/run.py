"""Matched I2C-only generation, training, frozen confirmation and reporting."""
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
from .receiver import ARCHITECTURE, ARCHITECTURE_HASH, load_weights
from .training import write_json, fit_job, EPOCHS, CHUNK, SEEDS

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREVIOUS=HERE.parent/'protocol_reservoir64_training30'
BASELINE=PREVIOUS/'runs/run01'
ORIGINAL=HERE.parent/'protocol_reservoir64'
VARIANTS=('seed_11','seed_29','seed_47','original_loss_11')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_paths():
    return sorted([*HERE.glob('*.py'),HERE/'README.md',*PREVIOUS.glob('*.py'),*ORIGINAL.glob('*.py'),
                   ROOT/'work/model/stream_reservoir.py',ROOT/'work/model/transmit_simple_model.py'])


def preservation_manifest():
    paths=[p for directory in (PREVIOUS,ORIGINAL) for p in directory.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts]
    paths += [ROOT/'work/model/stream_reservoir.py',ROOT/'work/model/transmit_simple_model.py']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}


def preserved(output):
    saved=json.loads((output/'preservation.json').read_text())
    assert saved==preservation_manifest(),'previous experiment changed'
    return len(saved)


def generate(output):
    from work.study.protocol_reservoir64_training30.run import verify as verify64
    verify64(BASELINE)
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'preservation.json',preservation_manifest())
    shutil.copytree(BASELINE/'data/i2c',output/'data/i2c')
    config=json.loads((BASELINE/'config/i2c.json').read_text())
    config['architecture_hash']=ARCHITECTURE_HASH
    (output/'config').mkdir()
    write_json(output/'config/i2c.json',config)
    exposure=json.loads((BASELINE/'exposure.json').read_text())['i2c']
    write_json(output/'exposure.json',exposure)
    for v in VARIANTS:
        dest=output/'baseline64'/v;dest.mkdir(parents=True)
        for file in ('selected.npz','fit.json'):
            shutil.copy2(BASELINE/'models/i2c'/v/file,dest/file)
    write_json(output/'plan.json',dict(architecture=ARCHITECTURE,architecture_hash=ARCHITECTURE_HASH,
        profile='i2c',epochs=EPOCHS,chunk=CHUNK,batch_size=12,learning_rate=.003,seeds=SEEDS,
        variants=VARIANTS,final_case_seed_base=4290000,
        corpus='byte-identical I2C training and development files from previous training30 run',
        baseline='frozen previously selected 64-node I2C weights; no retraining',
        python=sys.executable,python_version=platform.python_version(),numpy=np.__version__,
        blas_threads=os.environ.get('OPENBLAS_NUM_THREADS'),command=sys.argv,
        sources={str(p.relative_to(ROOT)):sha(p) for p in source_paths()}))
    print(json.dumps(dict(prepared=str(output),nodes=32,connections=128,exposure=exposure)),flush=True)


def parallel(fn,jobs,workers):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(fn,jobs): print(json.dumps(dict(completed=result)),flush=True)


def train(output,workers):
    assert not (output/'freeze.json').exists(),'frozen'
    audit=json.loads((output/'audit/preflight.json').read_text());assert audit['passed']
    assert audit['sources']=={str(p.relative_to(ROOT)):sha(p) for p in source_paths()},'source changed since audit'
    preserved(output)
    jobs=[(str(output),'i2c',s,'weighted') for s in SEEDS]+[(str(output),'i2c',11,'original')]
    parallel(fit_job,jobs,workers)


def freeze(output):
    from .audit import checkpoint_audit
    assert not (output/'freeze.json').exists()
    preserved(output)
    checkpoint_audit(output)
    sources=source_paths()
    for p in sources:
        dest=output/'frozen_source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)
    write_json(output/'freeze.json',dict(architecture_hash=ARCHITECTURE_HASH,
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
        artifacts={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*'))
                   if p.is_file() and 'frozen_source' not in p.parts and not p.name.endswith('.log')}))
    print('Frozen all four candidates, selection, datasets and baseline weights.',flush=True)


def verify(output):
    saved=json.loads((output/'freeze.json').read_text());assert saved['architecture_hash']==ARCHITECTURE_HASH
    for p,d in saved['sources'].items():
        assert sha(ROOT/p)==d,p
        assert sha(output/'frozen_source'/p)==d,p
    for p,d in saved['artifacts'].items(): assert sha(output/p)==d,p
    n=preserved(output)
    print(f'All frozen hashes match; {n} previous files unchanged.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('generate','audit','train','freeze','evaluate','report','verify'))
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--workers',type=int,default=3)
    a=parser.parse_args()
    if a.action=='generate':generate(a.output)
    elif a.action=='audit':
        from .audit import preflight
        preflight(a.output)
    elif a.action=='train':train(a.output,a.workers)
    elif a.action=='freeze':freeze(a.output)
    elif a.action=='verify':verify(a.output)
    elif a.action=='evaluate':
        verify(a.output)
        from .evaluation import evaluate
        evaluate(a.output,a.workers)
    elif a.action=='report':
        verify(a.output)
        from .report import report
        report(a.output)


if __name__=='__main__':main()
