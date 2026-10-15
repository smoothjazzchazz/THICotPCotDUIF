import unittest

from work.study.stage_demo.run_demo import DemoConfig, run_demo
from work.model.system_simple_model import run_simulation


class DemoTests(unittest.TestCase):
    def test_same_runner_for_both_memories_and_conditioning(self):
        for memory in ("history", "reservoir", "pulse"):
            for stable_ticks in (1, 2):
                for delay_ticks in (0, 1, 2):
                    with self.subTest(memory=memory, stable=stable_ticks, delay=delay_ticks):
                        receiver, levels, trace, results = run_demo(
                            DemoConfig(memory, stable_ticks, delay_ticks))
                        self.assertTrue(results["all_expected"], results)
                        self.assertEqual(results["false_known_events_on_unfamiliar_or_background"], 0)
                        self.assertEqual([row["request"].symbol_id for row in trace
                                          if row["request"] is not None], [2, 1, 2])
                        offset = stable_ticks - 1 + delay_ticks
                        expected_output = [None] * len(levels)
                        expected_output[11 + offset:13 + offset] = [1, 0]
                        expected_output[34 + offset:36 + offset] = [0, 1]
                        expected_output[53 + offset:55 + offset] = [1, 0]
                        self.assertEqual([row["output_level"] for row in trace], expected_output)
                        # Freeze fitted parameters, then vary unseen suffixes.
                        prefix = levels[:20]
                        short = run_simulation(iter(prefix), receiver)
                        longer = run_simulation(iter(prefix + [1, 0, 1, 0]), receiver)
                        self.assertEqual(short, longer[:len(prefix)])


if __name__ == "__main__":
    unittest.main()
