import unittest

from work.model.system_simple_model import run_simulation


class SystemTests(unittest.TestCase):
    def test_recognized_pulses(self):
        input_levels = [0, 1, 1, 0, 0, 1, 1, 1, 1, 0] + [0] * 8
        trace = run_simulation(input_levels)
        expected_events = {
            3: {"class_id": 0, "start_tick": 1},
            9: {"class_id": 1, "start_tick": 5},
        }
        expected_actions = {3: "request symbol 2", 9: "request symbol 1"}
        expected_output = [None] * len(input_levels)
        expected_output[4:6] = [1, 0]
        expected_output[10:12] = [0, 1]

        self.assertEqual(len(trace), len(input_levels))
        for tick, row in enumerate(trace):
            self.assertEqual(row["tick"], tick)
            self.assertEqual(row["input_level"], input_levels[tick])
            self.assertEqual(row["rx_event"], expected_events.get(tick))
            self.assertEqual(row["controller_action"], expected_actions.get(tick, "idle"))
            self.assertEqual(row["output_level"], expected_output[tick])
        self.assertEqual(
            [row["high_count"] for row in trace],
            [0, 1, 2, 0, 0, 1, 2, 3, 4, 0] + [0] * 8,
        )

    def test_unknown_pulse(self):
        trace = run_simulation([0, 1, 1, 1, 0, 0, 0, 0])
        for tick, row in enumerate(trace):
            self.assertIsNone(row["output_level"])
            if tick == 4:
                self.assertEqual(row["rx_event"], {"class_id": 7, "start_tick": 1})
                self.assertEqual(row["controller_action"], "consume class 7")
                self.assertEqual(row["high_count"], 0)
            else:
                self.assertIsNone(row["rx_event"])
                self.assertEqual(row["controller_action"], "idle")


if __name__ == "__main__":
    unittest.main()
