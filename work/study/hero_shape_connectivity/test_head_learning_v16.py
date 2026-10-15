import unittest
import numpy as np
from .shapes import make_shape,initialize
from .runtime import run
from .readout_probe import trajectory
from .head_learning_v16 import objective,indices,logits,backbone

class HeadLearningContracts(unittest.TestCase):
    def test_forward_and_trainable_gradients(self):
        rng=np.random.default_rng(16016)
        for cell in ('readout16_dense','readout16_fanin32_fast'):
            sh=make_shape(sizes=(16,16,16),routing='port_firstlast4',feedback='both2',leaks=(1.,1.,.125),cell=cell);p=initialize(sh,29)
            p[-6-384:-6].reshape(6,64)[:,48:]=rng.normal(0,.2,(6,16))
            raw=rng.uniform(-1,1,(23,9));states=trajectory(sh,p,raw)
            np.testing.assert_allclose(logits(sh,p,states[:,:48]),run(sh,p,raw)[2],rtol=0,atol=1e-13)
            base,bp,stamp=backbone(sh,p);np.testing.assert_array_equal(trajectory(base,bp,raw),states[:,:48])
            active=indices(sh);free=p[active];x=rng.uniform(-1,1,(19,48));y=np.arange(19,dtype=np.int32)%6;weights=np.full(19,1/19)
            loss,gradient=objective(free,sh,p,x,y,free,weights)
            for at in (0,128,len(active)-391,len(active)-390,len(active)-7,len(active)-1):
                a=free.copy();b=free.copy();a[at]+=1e-6;b[at]-=1e-6
                fd=(objective(a,sh,p,x,y,free,weights)[0]-objective(b,sh,p,x,y,free,weights)[0])/2e-6
                self.assertAlmostEqual(fd,gradient[at],places=7)
            forbidden=set(np.flatnonzero(sh.dst<48))|set(range(len(sh.src),len(sh.src)+48));self.assertFalse(forbidden&set(active))

if __name__=='__main__':unittest.main()
