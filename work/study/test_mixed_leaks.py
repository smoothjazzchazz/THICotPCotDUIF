"""Small checks for isolation, probe timing, selection failure, and replay."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from work.model.reservoir_model import DecisionRule, ReservoirConfig, ReservoirReceiver
from work.study.comparison import collect_states, fit_readout, verify_reload
from work.study.mixed_leaks import (
    eligibility_reasons, fit_candidates, memory_diagnostics, memory_probe_streams, mixed_candidates,
)
from work.study.run_mixed_leaks import reserve_output
from work.study.select_reservoir import candidate_configs
from work.study.signals import make_stream, run_length_predictions


class MixedLeakTests(unittest.TestCase):
    def test_reproducible_independent_candidates_change_only_leaks(self):
        candidates = list(mixed_candidates())
        self.assertEqual(candidates, list(mixed_candidates()))
        base = dict(candidate_configs(24, 1))["seed24/forward_leak0"]
        self.assertEqual(candidates[0][1], base)
        for _, config in candidates:
            actual = config.to_dict()
            actual["leak_shifts"] = base.leak_shifts
            self.assertEqual(actual, base.to_dict())
            self.assertEqual(len(config.leak_shifts), 16)
            self.assertTrue(set(config.leak_shifts) <= {0, 1, 2, 3})
        unchanged = deepcopy(candidates[1:])
        candidates[0][1].leak_shifts[0] = 3
        candidates[0][1].feature_taps[0][0][1] = 99
        candidates[0][1].recurrent_taps[0][0][1] = 99
        self.assertEqual(candidates[1:], unchanged)
        self.assertEqual(list(mixed_candidates())[0][1], base)

    def test_probe_timing_and_continuous_history(self):
        probes = memory_probe_streams()
        # Five targets, all 25 two-pattern prefixes at two rest lengths, plus reset.
        self.assertEqual(len(probes), 5 * (25 * 2 + 1))
        first = probes[0]["stream"]
        self.assertEqual(first.levels, [0] * 20 + [1] * 3 + [0] * 3 + [1] * 8 + [0] * 4)
        self.assertEqual(first.windows, [{"class_id": 0, "start": 34, "end": 38}])
        for record in probes:
            stream = record["stream"]
            self.assertEqual(stream.targets, run_length_predictions(stream.levels, 0))
            self.assertEqual(len(stream.windows), 1 if record["context"] == "reset" else 3)
            final = stream.windows[-1]
            self.assertEqual(stream.levels[final["start"] - 1:final["end"]], [1, 0, 0, 0, 0])

    def test_known_collision_and_uniform2_magnitude_only_memory(self):
        probes = memory_probe_streams()
        configs = dict(mixed_candidates())
        diagnostics = {}
        for name in ("uniform0", "uniform2"):
            states = [collect_states(record["stream"], configs[name]) for record in probes]
            diagnostics[name] = memory_diagnostics(probes, states)
        # The leak-zero DAG has forgotten the first pulse by the final falling edge.
        for pair in diagnostics["uniform0"]["comparisons"]:
            self.assertEqual(pair["full"]["reset_distance"], [0] * 4)
            self.assertEqual(pair["bits"]["continuous_min_distance"], [0] * 4)
        # This protects the diagnostic distinction, without asserting recognition.
        for pair in diagnostics["uniform2"]["comparisons"]:
            self.assertTrue(all(value > 0 for value in pair["full"]["reset_distance"]))
        self.assertTrue(any(0 in pair["bits"]["reset_distance"]
                            for pair in diagnostics["uniform2"]["comparisons"]))

    def test_distance_diagnostic_does_not_confuse_prefix_with_target(self):
        probes = memory_probe_streams()
        states = []
        for record in probes:
            # Every target has identical states within a context. Prefix identity
            # changes the state by ten counts; that cannot count as pulse memory.
            value = 0 if record["context"] == "reset" else (len(states) // 5) % 2 * 10
            states.append(np.full((len(record["stream"].levels), 16), value))
        result = memory_diagnostics(probes, states)
        for pair in result["comparisons"]:
            self.assertEqual(pair["full"]["continuous_min_distance"], [0] * 4)
            self.assertEqual(pair["full"]["cross_context_min_distance"], [0] * 4)
            self.assertEqual(pair["full"]["within_target_max_distance"], [160] * 4)

    def test_all_rejected_has_no_selection_but_saves_diagnostic_settings(self):
        train, validation = [make_stream(1, 3)], [make_stream(2, 3)]
        config = dict(mixed_candidates())["uniform0"]
        stats = {"event_f1": .9, "balanced_accuracy": .9, "false_events_per_1000_ticks": 0,
                 "event_precision": .9, "event_recall": .9, "unknown_recall": .9}
        # A strong validation score must not override loss of pulse information.
        methods = {}
        state = collect_states(train[0], config)
        for kind in ("hamming", "linear_bits", "linear_full"):
            readout = fit_readout(train, [state], kind)
            methods[kind] = {"receiver": ReservoirReceiver(config, readout, DecisionRule(0, 0)).to_dict(),
                             "validation": stats}
        with patch("work.study.mixed_leaks.mixed_candidates", return_value=[("uniform0", config)]), \
                patch("work.study.mixed_leaks.train_and_select", return_value=methods):
            audit, frozen = fit_candidates(train, validation, memory_probe_streams(), progress=lambda _: None)
        self.assertIsNone(audit["selected_candidate"])
        record = audit["candidates"][0]
        self.assertTrue(any("collision" in reason for reason in record["rejection_reasons"]))
        self.assertIn("uniform0", frozen)
        # Original dynamics screens remain mandatory even if later scores look good.
        record["training"]["saturated_state_fraction"] = .51
        record["initial_state"]["maximum_tail_gap"] = 2
        reasons = eligibility_reasons(record)
        self.assertTrue(any("saturated" in reason for reason in reasons))
        self.assertTrue(any("initial-state" in reason for reason in reasons))
        json.dumps(audit, allow_nan=False)

    def test_json_reload_replays_mixed_config_and_all_readouts(self):
        config = dict(mixed_candidates())["cycle0123"]
        restored = ReservoirConfig(**json.loads(json.dumps(config.to_dict())))
        train = [make_stream(1, 6), make_stream(2, 6)]
        states = [collect_states(stream, config) for stream in train]
        stream = make_stream(3, 6)
        expected = collect_states(stream, config)
        np.testing.assert_array_equal(expected, collect_states(stream, restored))
        selected = {}
        for kind in ("hamming", "linear_bits", "linear_full"):
            readout = fit_readout(train, states, kind)
            receiver = ReservoirReceiver(restored, readout, DecisionRule(-6 if kind == "hamming" else .4, .1), 2)
            selected[kind] = {"receiver": json.loads(json.dumps(receiver.to_dict()))}
        verify_reload(stream, expected, selected)

    def test_original_results_and_existing_outputs_are_protected(self):
        for path in ("latest", "selected", "selected/subdirectory"):
            with self.assertRaisesRegex(ValueError, "Protected"):
                reserve_output(Path(__file__).parent / "results" / path)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "keep.txt").write_text("keep")
            with self.assertRaisesRegex(ValueError, "new or empty"):
                reserve_output(path)
            self.assertEqual((path / "keep.txt").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
