import unittest
import numpy as np
from .startup_grid_v10 import case
from .runtime import pulses,events
from .vendor.data import assemble


class StartupGridContracts(unittest.TestCase):
    def test_extreme_idles_all_conditions_payload_and_causal_features(self):
        for profile in ('uart_n','uart_e'):
            for idle in (17,48):
                for condition in range(7):
                    for value in (0,255,85,170):
                        s=case(profile,idle,condition,value)
                        self.assertTrue(np.all(s['lines'][:idle]==1));self.assertEqual(s['lines'][idle,0],0)
                        self.assertEqual(s['x'][idle,6],0);self.assertEqual(s['labels'][idle+7],3)
                        accepted,_=assemble(events(pulses(s['labels'])),profile)
                        self.assertEqual([v for a in accepted for v in a['bytes']],[value])
                        t=case(profile,idle,condition,value);self.assertTrue(np.array_equal(s['lines'],t['lines']))


if __name__=='__main__':unittest.main()
