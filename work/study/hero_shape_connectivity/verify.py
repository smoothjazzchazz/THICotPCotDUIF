"""Historical preservation, immutable confirmations, and exact training replay."""
import argparse
import json
from pathlib import Path
import tempfile
import numpy as np
from .run import ROOT,digest
from .train import fit,write_json
from .data import load,save


def verify(root):
    checks={};failures=[]
    for name,base,manifest in [('historical',Path('.'),root/'historical_sha256.json')]:
        hashes=json.loads(manifest.read_text())
        for path,expected in hashes.items():
            p=base/path
            if not p.exists() or digest(p)!=expected:failures.append(str(p))
        checks[name+'_files']=len(hashes)
    for comparison in sorted((root/'confirmations').iterdir()):
        freeze=comparison/'freeze.json'
        if not freeze.exists():continue
        spec=json.loads(freeze.read_text());count=0
        for rel,h in spec['source_hashes'].items():
            if digest(comparison/'source'/rel)!=h:failures.append(str(comparison/'source'/rel))
            count+=1
        for e in spec['entries']:
            if digest(comparison/e['weight_path'])!=e['weight_sha256']:failures.append(str(comparison/e['weight_path']))
            count+=1
        for rel,h in json.loads((comparison/'data_hashes.json').read_text()).items():
            if digest(comparison/'data'/rel)!=h:failures.append(str(comparison/'data'/rel))
            count+=1
        checks[comparison.name+'_files']=count
    write_json(root/'preservation_verification.json',dict(checks=checks,failures=failures,pass_all=not failures))
    if failures:raise AssertionError(failures[:10])
    print(checks,flush=True)


def replay(root):
    # Small continuous real stream: this checks optimizer/state continuation,
    # not qualification or training coverage. Independent run directories.
    with tempfile.TemporaryDirectory(prefix='hero_resume_',dir='/tmp') as temporary:
        temp=Path(temporary);stream=load(root/'data'/'spi1'/'clean')
        for name in ('direct','resumed'):
            folder=temp/name
            for split in ('clean','patterns','dev')+tuple(f'mixed_{i:02d}' for i in range(12)):
                save(folder/'data'/'spi1'/split,stream)
        kwargs=dict(code='srr',schedule='registered')
        fit((str(temp/'direct'),kwargs,'spi1',11,5,'matched'))
        fit((str(temp/'resumed'),kwargs,'spi1',11,3,'matched'))
        fit((str(temp/'resumed'),kwargs,'spi1',11,5,'matched'))
        path='models/matched/srr_registered_24-20-20/spi1/11/epoch_0005.npz'
        a=np.load(temp/'direct'/path);b=np.load(temp/'resumed'/path)
        result={key:bool(np.array_equal(a[key],b[key])) for key in ('p','m','v','ending_state','metadata')}
        write_json(root/'checkpoint_replay_verification.json',dict(epoch_3_to_5=result,pass_all=all(result.values())))
        if not all(result.values()):raise AssertionError(result)
        print('exact checkpoint continuation',result,flush=True)


def fresh_replay(root):
    import shutil
    from .shapes import make_shape
    kwargs=json.loads((ROOT/'wider_both_candidate.json').read_text())[0];sh=make_shape(**kwargs)
    source=root/'models'/'phase_portfolio'/sh.name/'uart_n'/'11'/'block_0300.json'
    checkpoint=json.loads(source.read_text())['checkpoint'];stream=load(root/'data'/'uart_n'/'clean')
    with tempfile.TemporaryDirectory(prefix='hero_fresh_replay_',dir='/tmp') as temporary:
        temp=Path(temporary)
        for name in ('direct','resumed','profile'):
            folder=temp/name;recipe='phase_profile_fresh' if name=='profile' else 'phase_fresh'
            for subfolder in ('data','data_extended'):
                for split in ('clean','patterns','dev')+tuple(f'mixed_{i:02d}' for i in range(12)):
                    save(folder/subfolder/'uart_n'/split,stream)
            for epoch in (1,2):save(folder/'data_fresh'/'uart_n'/f'epoch_{epoch:04d}',stream)
            model=folder/'models'/recipe/sh.name/'uart_n'/'11';model.mkdir(parents=True)
            write_json(model/'warm_start.json',dict(checkpoint=checkpoint))
        fit((str(temp/'direct'),kwargs,'uart_n',11,2,'phase_fresh'))
        fit((str(temp/'resumed'),kwargs,'uart_n',11,1,'phase_fresh'))
        fit((str(temp/'resumed'),kwargs,'uart_n',11,2,'phase_fresh'))
        fit((str(temp/'profile'),kwargs,'uart_n',11,2,'phase_profile_fresh'))
        tail=sh.name+'/uart_n/11/epoch_0002.npz'
        a=np.load(temp/'direct'/'models'/'phase_fresh'/tail);b=np.load(temp/'resumed'/'models'/'phase_fresh'/tail)
        c=np.load(temp/'profile'/'models'/'phase_profile_fresh'/tail)
        fields=('p','m','v','aux_weights','aux_m','aux_v','leaks','ending_state')
        checks={k:bool(np.array_equal(a[k],b[k]) and np.array_equal(a[k],c[k])) for k in fields}
        original=np.load(checkpoint);mask=json.loads(str(original['metadata']))['frozen_parameter_indices']
        checks['frozen_ring_preserved']=bool(np.array_equal(a['p'][mask],original['p'][mask]))
        write_json(root/'fresh_recipe_replay_verification.json',dict(checks=checks,pass_all=all(checks.values()),
            scope='two short-stream epochs; optimizer/auxiliary/frozen-mask resume contract only, not training coverage'))
        if not all(checks.values()):raise AssertionError(checks)
        print('fresh recipe exact continuation',checks,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['preservation','replay','fresh-replay']);a=ap.parse_args()
    {'preservation':verify,'replay':replay,'fresh-replay':fresh_replay}[a.action](ROOT/'runs'/'connectivity01')
