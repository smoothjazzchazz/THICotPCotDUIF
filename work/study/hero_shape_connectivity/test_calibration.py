"""Analytic STOP-onset intervals agree with direct causal pulse generation."""
import unittest
import numpy as np
from .margin_calibrate import allowed_interval
from .runtime import pulses

class CalibrationContracts(unittest.TestCase):
    def test_intervals_match_all_direct_threshold_onsets(self):
        rng=np.random.default_rng(261)
        for _ in range(50):
            tau=rng.normal(size=30);original=float(rng.normal());truth=pulses(np.where(original>=tau,4,0))
            previous=np.r_[np.inf,tau[:-1]];true=truth==4
            lower=max(-8,float(tau[true].max()) if true.any() else -8)
            upper=min(8,float(previous[true].min()) if true.any() else 8)
            false=(~true)&(tau<previous);forbidden=list(zip(tau[false],previous[false]))
            intervals=allowed_interval(lower,upper,forbidden) if lower<upper else []
            for delta in np.linspace(-7.9,7.9,101):
                analytical=any(lo<=delta<hi for lo,hi in intervals)
                direct=np.array_equal(pulses(np.where(delta>=tau,4,0)),truth)
                self.assertEqual(analytical,direct)

if __name__=='__main__':unittest.main()
