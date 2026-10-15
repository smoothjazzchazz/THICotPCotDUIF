"""Contracts for current-sample nonlinear readout without extra recurrent state."""
import unittest
import numpy as np
from .shapes import make_shape,initialize,cost
from .runtime import run


class ReadoutTests(unittest.TestCase):
    def test_backbone_equivalence_and_state_independence(self):
        kw=dict(sizes=(16,16,16),routing='port_firstlast4',feedback='both2',leaks=(1.,1.,.125))
        base=make_shape(**kw);bp=initialize(base,11);x=np.random.default_rng(4).normal(size=(39,9))
        bz=run(base,bp,x)[2]
        for layout in ('dense','fanin8','fanin32','fanin32_fast'):
            sh=make_shape(**kw,cell='readout16_'+layout);p=initialize(sh,11)
            np.testing.assert_allclose(run(sh,p,x)[2],bz,atol=1e-14,rtol=0)
            p[-6-384:-6].reshape(6,64)[:,48:]=.2
            initial=np.zeros(64);initial[48:]=1e4
            for fixed in (False,True):
                a=run(sh,p,x,quantize=fixed);b=run(sh,p,x,h=initial,quantize=fixed)
                np.testing.assert_array_equal(a[2],b[2])
                first=run(sh,p,x[:13],quantize=fixed)
                rest=run(sh,p,x[13:],h=first[1],quantize=fixed)
                np.testing.assert_array_equal(a[2],np.concatenate([first[2],rest[2]]))
            self.assertEqual(cost(sh)['stored_states'],48)
            self.assertEqual(cost(sh)['nodes'],64)
            self.assertFalse(np.any(sh.src>=48))
            self.assertTrue(np.all(sh.delay[sh.dst>=48]==0))

    def test_fanin32_is_a_real_subset_with_declared_cost(self):
        kw=dict(sizes=(16,16,16),routing='port_firstlast4',feedback='both2',leaks=(1.,1.,.125))
        dense=make_shape(**kw,cell='readout16_dense');pruned=make_shape(**kw,cell='readout16_fanin32')
        dense_edges=set(zip(dense.src,dense.dst,dense.delay));pruned_edges=set(zip(pruned.src,pruned.dst,pruned.delay))
        self.assertTrue(pruned_edges<dense_edges);self.assertEqual(len(dense_edges-pruned_edges),256)
        for j,d in enumerate(range(48,64)):
            actual=set(pruned.src[pruned.dst==d]);expected=set(range(16))|{16+(j+2*k)%16 for k in range(8)}|{32+(j+2*k)%16 for k in range(8)}
            self.assertEqual(actual,expected)
        self.assertEqual(cost(pruned)['macs_per_tick'],1208);self.assertEqual(pruned.parameters,1278)
        fast=make_shape(**kw,cell='readout16_fanin32_fast')
        for j,d in enumerate(range(48,64)):
            self.assertEqual(set(fast.src[fast.dst==d]),set(range(16,32))|{(j+2*k)%16 for k in range(8)}|{32+(j+2*k)%16 for k in range(8)})
        self.assertEqual(cost(fast)['macs_per_tick'],1208);self.assertEqual(fast.parameters,1278)

    def test_hidden_and_core_gradients(self):
        sh=make_shape(sizes=(16,16,16),routing='port_firstlast4',feedback='both2',leaks=(1.,1.,.125),cell='readout16_fanin8')
        p=initialize(sh,29);p[-6-384:-6].reshape(6,64)[:,48:]=np.random.default_rng(8).normal(0,.1,(6,16))
        x=np.random.default_rng(5).normal(size=(11,9));y=np.arange(11,dtype=np.int32)%6
        loss,h,z,g,dh=run(sh,p,x,y,backward=True)
        for i in [0,144,len(sh.src)-1,len(sh.src)+63,len(p)-7]:
            a=p.copy();b=p.copy();a[i]+=1e-5;b[i]-=1e-5
            fd=(run(sh,a,x,y)[0]-run(sh,b,x,y)[0])/2e-5
            self.assertAlmostEqual(g[i],fd,places=7)

if __name__=='__main__':unittest.main()
