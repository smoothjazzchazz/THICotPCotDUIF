import unittest

from work.model.transmit_simple_model import Transmitter


class TransmitterTests(unittest.TestCase):
    def test_symbol_sequence(self):
        transmitter = Transmitter([])
        for symbol_id in [2, 2, 0]:
            transmitter.send(symbol_id)
        levels = [transmitter.step() for _ in range(6)]
        self.assertEqual(levels, [1, 0, 1, 0, 0, 0])
        self.assertIsNone(transmitter.step())

    def test_arrival_during_playback(self):
        transmitter = Transmitter([2])
        self.assertEqual(transmitter.step(), 1)
        # A new request must wait for the current pattern to finish.
        transmitter.send(1)
        self.assertEqual(transmitter.step(), 0)
        self.assertEqual([transmitter.step() for _ in range(2)], [0, 1])
        self.assertIsNone(transmitter.step())
        transmitter.send(0)
        self.assertEqual([transmitter.step() for _ in range(2)], [0, 0])
        self.assertIsNone(transmitter.step())

    def test_empty_and_invalid_request(self):
        transmitter = Transmitter([])
        self.assertIsNone(transmitter.step())
        with self.assertRaises(ValueError):
            transmitter.send(4)
        self.assertIsNone(transmitter.step())


if __name__ == "__main__":
    unittest.main()
