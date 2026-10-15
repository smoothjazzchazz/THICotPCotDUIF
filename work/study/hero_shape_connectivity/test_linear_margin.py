import unittest
import numpy as np
from .linear_margin_diagnostic import solve,minimum_change


class LinearMarginContracts(unittest.TestCase):
    def test_separable_and_colliding_labels(self):
        prior=np.zeros((6,2));x=np.array([[1.,1.],[-1.,1.]])
        yes,w=solve(x,np.array([1,2]),prior,.25)
        self.assertTrue(yes['success']);self.assertGreater(yes['verified_minimum_margin'],.1)
        self.assertEqual(yes['support_errors'],0);self.assertLessEqual(yes['max_constraint_residual'],1e-8)
        no,w=solve(np.ones((2,2)),np.array([1,2]),prior,None)
        self.assertTrue(no['success']);self.assertAlmostEqual(no['verified_minimum_margin'],0,places=7)
        fit=minimum_change(x,np.array([1,2]),prior)
        self.assertTrue(fit.success)
        self.assertLess(fit.fun,1.)
        bad=minimum_change(np.ones((2,2)),np.array([1,2]),prior)
        self.assertFalse(bad.success)


if __name__=='__main__':unittest.main()
