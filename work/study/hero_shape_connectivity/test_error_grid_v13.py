import unittest
from .error_grid_v13 import schedule,case
from .startup_audit import mismatches

class ErrorGridContracts(unittest.TestCase):
    def test_balanced_complete_and_independently_parsed(self):
        entries=schedule();self.assertEqual(len(entries),5376);self.assertEqual(len(set(entries)),5376)
        for index in (0,335,671):
            stream=case(index);self.assertEqual(sum(g['valid'] for g in stream['groups']),8)
            self.assertFalse(mismatches(stream));self.assertEqual(len(stream['coverage_entries']),8)

if __name__=='__main__':unittest.main()
