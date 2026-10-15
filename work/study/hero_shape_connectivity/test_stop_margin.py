import unittest
import numpy as np
from .stop_margin import objective


class StopObjective(unittest.TestCase):
    def test_empty_support_is_finite_prior_penalty(self):
        w=np.array([2.,3.]);prior=np.array([1.,1.])
        value,g=objective(w,np.empty((0,2)),np.empty(0),np.empty(0),prior)
        self.assertAlmostEqual(value,5e-6)
        np.testing.assert_allclose(g,[2e-6,4e-6])

    def test_gradient_and_unchanged_competitors(self):
        rng=np.random.default_rng(803);x=rng.normal(size=(37,6));w=rng.normal(size=6);prior=rng.normal(size=6)
        sign=rng.choice([-1.,1.],37);threshold=rng.normal(size=37)
        value,g=objective(w,x,sign,threshold,prior)
        for i in range(6):
            plus=w.copy();minus=w.copy();plus[i]+=1e-6;minus[i]-=1e-6
            self.assertAlmostEqual((objective(plus,x,sign,threshold,prior)[0]-objective(minus,x,sign,threshold,prior)[0])/2e-6,g[i],places=6)
        # Binary margin compares exactly against the five fixed event logits.
        z=rng.normal(size=(37,6));z[:,4]=x@w;other=np.max(z[:,[0,1,2,3,5]],axis=1)
        np.testing.assert_array_equal(z.argmax(1)==4,z[:,4]>other)

if __name__=='__main__':unittest.main()
