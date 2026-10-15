import unittest
import numpy as np
from .bit_hold_diagnostic_v9 import held_bit_labels
from .runtime import pulses


class HeldClassContracts(unittest.TestCase):
    def test_repeated_bits_and_boundary_pulses_unchanged(self):
        labels=np.zeros(24,dtype=np.int32);labels[[0,4,8,12,16,20]]=[3,2,2,1,4,5]
        for extension in (1,2):
            held=held_bit_labels(labels,extension)
            np.testing.assert_array_equal(pulses(held),labels)
            np.testing.assert_array_equal(held[[1,17,21]],0)
            self.assertEqual(held[5],2)
        with self.assertRaises(ValueError):held_bit_labels(np.array([2,0,2],dtype=np.int32),2)


if __name__=='__main__':unittest.main()
