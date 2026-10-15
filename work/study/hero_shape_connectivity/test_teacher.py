import unittest
import numpy as np
from .teacher import timing_targets,inlet_targets
from .vendor.data import Builder


class TeacherTests(unittest.TestCase):
    def test_causal_inlet_pulse_and_unchanged_other_heads(self):
        for profile,last in [('uart_n',151),('uart_e',167)]:
            b=Builder(profile,55);b.message([0]);b.idle(64);s=b.finish();x=s['lines'];start=b.groups[0]['start']
            old=timing_targets(x,profile);new=inlet_targets(x,profile)
            np.testing.assert_array_equal(old[1:],new[1:])
            self.assertEqual(np.flatnonzero(new[0]).tolist(),list(range(start+1,start+last+1,16)))
            changed=x.copy();cut=start+80;changed[cut:,0]^=1
            np.testing.assert_array_equal(inlet_targets(x,profile)[:,:cut],inlet_targets(changed,profile)[:,:cut])

    def test_previous_progress_diagnostic_preserves_n(self):
        b=Builder('uart_n',61);b.message([23,255]);x=b.finish()['lines']
        np.testing.assert_array_equal(timing_targets(x,'uart_n'),timing_targets(x,'uart_n','stop_interval'))

if __name__=='__main__':unittest.main()
