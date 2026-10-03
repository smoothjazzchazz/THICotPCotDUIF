import unittest

from work.model.transmit_simple_model import Transmitter


class TransmitterTests(unittest.TestCase):
    def test_symbol_sequence(self):
        transmitter = Transmitter(capacity=3)
        for symbol_id in [2, 2, 0]:
            self.assertTrue(transmitter.send(symbol_id))
        levels = [transmitter.step() for _ in range(12)]
        self.assertEqual(levels, [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0])
        self.assertIsNone(transmitter.step())

    def test_arrival_during_playback_and_capacity(self):
        transmitter = Transmitter()
        self.assertTrue(transmitter.send(2))
        self.assertEqual(transmitter.step(), 0)
        self.assertTrue(transmitter.send(1))
        self.assertFalse(transmitter.send(0))  # Playing + waiting fills capacity.
        self.assertEqual([transmitter.step() for _ in range(3)], [0, 1, 0])
        self.assertTrue(transmitter.send(0))  # Symbol 2 just finished.
        levels = [transmitter.step() for _ in range(8)]
        self.assertEqual(levels, [0, 0, 0, 1, 0, 0, 0, 0])
        self.assertIsNone(transmitter.step())

    def test_empty_and_invalid_request(self):
        transmitter = Transmitter()
        self.assertIsNone(transmitter.step())
        with self.assertRaises(ValueError):
            transmitter.send(16)
        self.assertIsNone(transmitter.step())


if __name__ == "__main__":
    unittest.main()
