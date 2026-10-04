from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from work.model.reservoir_model import ReservoirConfig, make_reservoir_config
from work.study.select_reservoir import candidate_configs, initial_state_diagnostics, select_reservoir
from work.study.signals import make_stream


def responsive_config(seed):
    return ReservoirConfig(6, [0, 0, 0], [[], [], []], [[[0, 1]], [[0, 1]], [[0, 1]]], seed)


class ReservoirSelectionTests(unittest.TestCase):
    def setUp(self):
        self.train = [make_stream(10, 6), make_stream(11, 6)]
        self.validation = [make_stream(20, 6)]

    def test_candidates_are_reproducible_and_preserve_tap_indices(self):
        candidates = list(candidate_configs(23, 1))
        self.assertEqual(candidates, list(candidate_configs(23, 1)))
        original = make_reservoir_config(23)
        self.assertEqual(candidates[0][1], original)
        for name, config in candidates:
            self.assertEqual(len(config.leak_shifts), 16)
            self.assertEqual(config.state_bits, 6)
            for expected, actual in zip(original.recurrent_taps, config.recurrent_taps):
                self.assertEqual([tap[0] for tap in expected], [tap[0] for tap in actual])
            if "forward" in name:
                for node, row in enumerate(config.recurrent_taps):
                    active = [source for source, weight in row if weight]
                    self.assertLessEqual(len(active), 1)
                    self.assertTrue(all(source < node for source in active))
        candidates[-1][1].recurrent_taps[0][0][1] = 99
        self.assertEqual(candidates[0][1], original)

    def test_initial_state_probe_catches_persistent_feedback(self):
        good = responsive_config(0)
        self.assertEqual(initial_state_diagnostics(good, [0] * 128)["maximum_tail_gap"], 0)
        bad = deepcopy(good)
        bad.recurrent_taps[0] = [[0, 1]]
        bad.feature_taps[0] = []
        self.assertEqual(initial_state_diagnostics(bad, [0] * 128)["maximum_tail_gap"], 63)

    def test_failed_screen_does_not_fit_or_silently_choose_a_candidate(self):
        with patch("work.study.select_reservoir.train_and_select") as fit:
            config, readouts, report = select_reservoir(
                self.train, self.validation, [("original", make_reservoir_config(23))])
        fit.assert_not_called()
        self.assertIsNone(config)
        self.assertIsNone(readouts)
        self.assertIsNone(report["selected_candidate"])
        self.assertIn("constant binary fingerprint", report["candidates"][0]["rejection_reasons"])
        json.dumps(report, allow_nan=False)

    def test_selection_balances_primary_readouts_and_keeps_one_config(self):
        def fitted_readouts(train, states, validation, validation_states, config, **kwargs):
            # Candidate 2 wins the primary average despite losing both linear comparisons.
            f1 = {1: (.2, 1.0, .9), 2: (.7, 0.0, .6)}[config.seed]
            return {name: {"receiver": {"reservoir": config.to_dict()}, "validation": {
                "event_f1": score, "balanced_accuracy": .5, "false_events_per_1000_ticks": 1}}
                    for name, score in zip(("hamming", "linear_bits", "linear_full"), f1)}

        candidates = [("first", responsive_config(1)), ("second", responsive_config(2))]
        with patch("work.study.select_reservoir.train_and_select", side_effect=fitted_readouts) as fit:
            config, readouts, report = select_reservoir(self.train, self.validation, candidates)
        self.assertEqual(config.seed, 2)
        self.assertEqual(report["selected_candidate"], "second")
        for method in ("hamming", "linear_bits", "linear_full"):
            self.assertEqual(readouts[method]["receiver"]["reservoir"], config.to_dict())
        self.assertEqual(fit.call_count, 2)
        self.assertTrue(all(call.kwargs["include_reference"] is False for call in fit.call_args_list))

    def test_training_and_validation_seed_overlap_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "disjoint"):
            select_reservoir(self.train, self.train, candidate_configs(23, 1))


if __name__ == "__main__":
    unittest.main()
