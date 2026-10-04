import json
import unittest

import numpy as np

from work.model.reservoir_model import DecisionRule, ReservoirReceiver, make_reservoir_config
from work.study.comparison import (
    choose_classes, collect_states, fit_readout, measure, score_states, verify_reload,
)
from work.study.signals import SignalStream, make_stream, run_length_predictions


class ComparisonTests(unittest.TestCase):
    def test_clean_reference_and_stabilizer_latency(self):
        stream = make_stream(19, patterns=12, jitter=0)
        prediction = run_length_predictions(stream.levels, tolerance=0)
        self.assertEqual(prediction, stream.targets)
        metrics, _ = measure([stream], [prediction], hold_ticks=3)
        self.assertEqual(metrics["event_f1"], 1)
        self.assertEqual(metrics["balanced_accuracy"], 1)
        # Three agreeing ticks delay emission by two, but keep the first tick's timestamp.
        self.assertEqual(metrics["median_latency_ticks"], 2)
        self.assertEqual(metrics["mean_abs_timestamp_error"], 0)

    def test_extra_events_are_false_positives(self):
        target = [2] * 21 + [0] * 4 + [2] * 5
        stream = SignalStream(0, [0] * 30, target, [{"class_id": 0, "start": 21, "end": 25}], 0, 0)
        predicted = [2] * 30
        predicted[21] = predicted[23] = 0
        metrics, _ = measure([stream], [predicted], 1)
        self.assertEqual(metrics["matched_events"], 1)
        self.assertEqual(metrics["predicted_events"], 2)
        self.assertAlmostEqual(metrics["event_f1"], 2 / 3)

    def test_target_windows_are_causal_and_noise_keeps_intent(self):
        clean = make_stream(31, patterns=12, jitter=0)
        noisy = make_stream(31, patterns=12, jitter=0, flip_probability=.5)
        self.assertEqual(clean.targets, noisy.targets)
        self.assertNotEqual(clean.levels, noisy.levels)
        for window in clean.windows:
            self.assertEqual(clean.levels[window["start"] - 1], 1)
            self.assertEqual(clean.levels[window["start"]], 0)
            self.assertEqual(clean.targets[window["start"] - 1], 2)

    def test_fitting_and_reloaded_streaming_match_cached_states(self):
        config = make_reservoir_config(23)
        train = [make_stream(1, 6), make_stream(2, 6)]
        states = [collect_states(stream, config) for stream in train]
        held_out = make_stream(100, 6)
        held_out_states = collect_states(held_out, config)
        selected = {}
        for kind in ("hamming", "linear_bits", "linear_full"):
            readout = fit_readout(train, states, kind)
            decision = DecisionRule(-8 if kind == "hamming" else .4, .1)
            receiver = ReservoirReceiver(config, readout, decision, 2)
            selected[kind] = {"receiver": json.loads(json.dumps(receiver.to_dict()))}
            scores = score_states(readout, held_out_states)
            batch = choose_classes(scores, readout.class_ids, decision)
            scalar = [decision.choose(row, readout.class_ids) for row in scores]
            np.testing.assert_array_equal(batch, scalar)
        verify_reload(held_out, held_out_states, selected)


if __name__ == "__main__":
    unittest.main()
