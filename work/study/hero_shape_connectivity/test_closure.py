"""Finite objectives and an independent scalar check of cached training audits."""
import tempfile,unittest
from pathlib import Path
import numpy as np
from .run import ROOT
from .hard_readout import objective
from .shapes import make_shape,initialize
from .runtime import run
from .data import save
from .readout_probe import trajectory
from .closure_v6 import verify_training


class ClosureContracts(unittest.TestCase):
    def test_multiclass_empty_support_and_gradient(self):
        rng=np.random.default_rng(718);prior=rng.normal(size=(6,5));w=prior+.1
        value,g=objective(w.ravel(),np.empty((0,5)),np.empty(0,dtype=np.int32),prior)
        self.assertAlmostEqual(value,1e-6*.01*30);np.testing.assert_allclose(g,2e-7)
        x=rng.normal(size=(17,5));y=rng.integers(0,6,17,dtype=np.int32);flat=w.ravel();value,g=objective(flat,x,y,prior)
        for i in (0,7,19,29):
            plus=flat.copy();minus=flat.copy();plus[i]+=1e-6;minus[i]-=1e-6
            self.assertAlmostEqual((objective(plus,x,y,prior)[0]-objective(minus,x,y,prior)[0])/2e-6,g[i],places=6)

    def test_training_audit_cache_matches_scalar_and_masks_only_prefix(self):
        sh=make_shape();p=initialize(sh,11);rng=np.random.default_rng(908);x=rng.normal(size=(103,9));labels=run(sh,p,x)[2].argmax(1).astype(np.int32)
        labels[:7]=(labels[:7]+1)%6;labels[82]=(labels[82]+1)%6
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'case';cache=root/'cache';cache.mkdir()
            save(path,dict(lines=np.ones((len(x),3),dtype=np.uint8),x=x,labels=labels,startup_ambiguous_until=7))
            uncached=verify_training(sh,p,[path.with_suffix('.json')],cache)
            np.save(cache/'0000.npy',trajectory(sh,p,x));cached=verify_training(sh,p,[path.with_suffix('.json')],cache)
            self.assertEqual(uncached,cached);self.assertEqual(cached['canonical_errors'],1)

if __name__=='__main__':unittest.main()
