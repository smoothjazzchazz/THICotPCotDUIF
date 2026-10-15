import unittest,json
import numpy as np
from .run import ROOT
from .shapes import make_shape,initialize
from .readout_probe import trajectory
from .gate_trace_v6 import trace


class MixedTrajectoryContracts(unittest.TestCase):
    def test_dynamic_gate_trajectories_match_independent_scalar_and_runtime(self):
        kwargs=[]
        for file in ('mixed_candidates.json','mixed_first_candidates.json','gate_eight_candidates.json'):
            kwargs.extend(k for k in json.loads((ROOT/file).read_text()) if 'mixed' in k.get('cell','') or k.get('cell')=='parent64_gated8')
        for kw in kwargs:
            sh=make_shape(**kw);p=initialize(sh,11);start=len(sh.src)+sh.n;rng=np.random.default_rng(29713)
            p[start:start+len(sh.gate_src)]=rng.normal(0,.3,len(sh.gate_src));x=rng.uniform(-1,1,(67,9))
            expected,gates,logits=trace(sh,p,x);actual=trajectory(sh,p,x)
            self.assertTrue(np.array_equal(actual,expected));self.assertGreater(float(np.max(np.ptp(gates,axis=0))),.001)


if __name__=='__main__':unittest.main()
