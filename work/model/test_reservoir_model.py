import json
import unittest

from work.model.reservoir_model import (
    DecisionRule, FeatureExtractor, HammingReadout, IntegerReservoir,
    LinearReadout, ReservoirConfig, ReservoirReceiver, Stabilizer,
    make_reservoir_config,
)
from work.model.system_simple_model import run_simulation


class ReservoirTests(unittest.TestCase):
    def test_parallel_update_and_saturation(self):
        config = ReservoirConfig(6, [0, 0, 0], [[[1, 1]], [[0, 1]], []], [[], [], [[0, 2]]])
        reservoir = IntegerReservoir(config)
        reservoir.state = (8, 0, 0)
        # The first two nodes swap old values; the third hits each signed state limit.
        self.assertEqual(reservoir.step((100,)), (0, 8, 31))
        self.assertEqual(reservoir.step((-100,)), (8, 0, -32))

    def test_signed_shift_and_integer_deadband(self):
        reservoir = IntegerReservoir(ReservoirConfig(6, [1, 2, 2], [[], [], []], [[], [], []]))
        reservoir.state = (-3, 1, 3)
        self.assertEqual(reservoir.step(()), (-1, 1, 3))
        # Small positive values persist: clipping plus leak is not a fading proof.
        for _ in range(12):
            reservoir.step(())
        self.assertEqual(reservoir.state, (0, 1, 3))

    def test_feature_timing_and_seed(self):
        features = FeatureExtractor()
        self.assertEqual([features.step(x) for x in [0, 1, 1, 0]],
                         [(-1, 0, 1), (1, 1, 0), (1, 0, 1), (-1, -1, 0)])
        self.assertEqual(make_reservoir_config(23), make_reservoir_config(23))

    def test_readout_scores_and_rejection(self):
        state = (-1, 4, -2)
        readout = HammingReadout([0, 1], [[0, 1, 0], [1, 0, 1]])
        self.assertEqual(readout.score(state), (0, -3))
        linear = LinearReadout([0, 1], [[-2, 1, 0], [0, 0, 0]], [-1, 0], scale=1)
        self.assertEqual(linear.score(state), (5, 0))
        rule = DecisionRule(-2, 1)
        self.assertEqual(rule.choose((0, -3), [0, 1]), 0)
        self.assertEqual(rule.choose((-3, -5), [0, 1]), 7)
        self.assertEqual(rule.choose((0, 0), [0, 1]), 7)

    def test_stabilizer_change_flicker_and_timestamp_wrap(self):
        stabilizer = Stabilizer(2)
        sequence = [0, 0, 0, 1, 0, 0, 7, 7]
        events = [stabilizer.step(value, 4095 + i) for i, value in enumerate(sequence)]
        self.assertEqual(events[1], {"class_id": 0, "start_tick": 4095})
        self.assertTrue(all(event is None for event in events[2:7]))
        self.assertEqual(events[7], {"class_id": 7, "start_tick": 5})

    def test_configuration_reload_and_existing_controller(self):
        config = ReservoirConfig(6, [0, 0, 0], [[], [], []], [[[0, 1]], [], []])
        readout = HammingReadout([0, 1], [[1, 1, 1], [0, 1, 1]])
        receiver = ReservoirReceiver(config, readout, DecisionRule(0, 1))
        restored = ReservoirReceiver.from_dict(json.loads(json.dumps(receiver.to_dict())))
        inputs = [0, 1, 1, 0, 0, 1]
        self.assertEqual(run_simulation(inputs, receiver), run_simulation(inputs, restored))
        receiver.reset()
        trace = run_simulation(inputs, receiver)
        self.assertEqual(trace[1]["rx_event"], {"class_id": 0, "start_tick": 1})
        self.assertEqual(trace[1]["controller_action"], "request symbol 2")
        self.assertEqual(trace[2]["receiver_state"]["state"], (1, 0, 0))


if __name__ == "__main__":
    unittest.main()
