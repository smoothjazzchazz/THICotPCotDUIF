"""Audit labels, dimensions, preservation and reproducible continuation."""
import io
import json
import unittest
from pathlib import Path
import numpy as np
from .receiver import MASK, initial_weights, load_weights
from .data import load_split
from .training import write_json, restore_optimizer, adam_step, CHUNK
from .bptt import loss_gradient
from work.study.protocol_reservoir64.training import batch
from work.study.protocol_reservoir64.checkers import bus_events


def preflight(output):
    from .run import ROOT,BASELINE,source_paths,sha,preserved
    from .test_experiment import I2C32Tests
    directory=output/'audit';directory.mkdir(exist_ok=True)
    preserved(output)
    log=io.StringIO()
    tests=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(I2C32Tests))
    (directory/'tests.log').write_text(log.getvalue())
    assert tests.wasSuccessful(),log.getvalue()
    labels={};seeds=set();files={}
    for split in ('train','dev'):
        counts=np.zeros(8,dtype=np.int64)
        for file in sorted((output/'data/i2c'/split).glob('*.npz')):
            assert sha(file)==sha(BASELINE/'data/i2c'/split/file.name)
            files[str(file.relative_to(output))]=sha(file)
        for stream in load_split(output,'i2c',split):
            y=stream['labels'];counts+=np.bincount(y,minlength=8)
            assert [(int(t),int(y[t])) for t in np.flatnonzero(y)]==bus_events(stream['lines'])
            payload=b''
            for tx in stream['metadata']['transactions']:
                assert tx['seed'] not in seeds;seeds.add(tx['seed'])
                payload+=bytes(tx['expected'])
            assert b'House Improvement Committee' not in payload
        assert counts[3]>0 and counts[4]>0
        labels[split]=list(map(int,counts))
    oldcfg=json.loads((BASELINE/'config/i2c.json').read_text())
    newcfg=json.loads((output/'config/i2c.json').read_text())
    oldcfg.pop('architecture_hash');newcfg.pop('architecture_hash');assert oldcfg==newcfg
    result=dict(passed=True,tests=tests.testsRun,corpus_hashes=files,class_counts=labels,
        distinct_transaction_seeds=len(seeds),identical_timing_and_event_configuration=True,
        nodes=32,connections=int(MASK.sum()),sources={str(p.relative_to(ROOT)):sha(p) for p in source_paths()})
    write_json(directory/'preflight.json',result)
    print(json.dumps(dict(preflight_passed=True,tests=tests.testsRun,class_counts=labels)),flush=True)


def checkpoint_audit(output):
    from .run import VARIANTS
    records=[]
    x,y,valid=batch(load_split(output,'i2c','train'))
    for variant in VARIANTS:
        directory=output/'models/i2c'/variant
        fit=json.loads((directory/'fit.json').read_text())
        assert fit['epochs']==30 and len(fit['history'])==30 and fit['steps']==2820
        assert fit['unique_nonpadding_ticks']==467802
        initial,_=load_weights(directory/'initial.npz')
        for k,v in initial_weights(fit['seed']).items():np.testing.assert_array_equal(initial[k],v)
        for epoch in range(1,31):
            w,metadata=load_weights(directory/f'epoch_{epoch:02d}.npz')
            assert not np.any(w['wh']*(1-MASK))
            assert w['wh'].shape==(32,32) and metadata['epoch']==epoch
            assert all(np.all(np.isfinite(a)) for a in w.values())
            assert (directory/f'optimizer_{epoch:02d}.npz').exists()
        w,meta=load_weights(directory/'selected.npz')
        selected,_=load_weights(directory/f"epoch_{fit['best_epoch']:02d}.npz")
        for k in w:np.testing.assert_array_equal(w[k],selected[k])
        # All four real candidates must resume reproducibly, not just a toy case.
        w,m,v,meta=restore_optimizer(directory/'optimizer_29.npz')
        step=meta['step'];state=np.zeros((12,32));weights=np.array(fit['class_weights'])
        for a in range(0,len(x),CHUNK):
            _,state,gradient=loss_gradient(w,x[a:a+CHUNK],y[a:a+CHUNK],valid[a:a+CHUNK],state,weights)
            step+=1;adam_step(w,gradient,m,v,step)
        end,em,ev,last=restore_optimizer(directory/'optimizer_30.npz')
        assert step==last['step']
        for aa,bb in ((w,end),(m,em),(v,ev)):
            for k in aa:np.testing.assert_array_equal(aa[k],bb[k])
        with np.load(directory/'optimizer_30.npz') as stored:np.testing.assert_array_equal(state,stored['ending_state'])
        records.append(dict(variant=variant,epochs=30,selected_epoch=fit['best_epoch'],
            exact_epoch29_to_30_continuation=True,parameters_changed=fit['parameter_l2_changes']))
    write_json(output/'audit/checkpoints.json',records)
