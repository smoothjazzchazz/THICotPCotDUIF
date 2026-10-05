"""Focused checks for finite memory, unchanged controls, isolation and replay."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from work.model.reservoir_model import (
    DecisionRule, FeatureExtractor, IntegerReservoir, ReservoirConfig, ReservoirReceiver,
)
from work.study.shared.comparison import collect_states, fit_readout, verify_reload
from work.study.delay_chains.delay_chains import EXPERIMENT, choose_chain, delay_candidates
from work.study.delay_chains.delay_chain_probes import boundary_diagnostics, first_pulse_delay, verify_chain
from work.study.mixed_leaks.mixed_leaks import memory_diagnostics, memory_probe_streams, mixed_candidates
from work.study.delay_chains.run_delay_chains import development_streams, reserve_output, run, seed_inventory
from work.study.mixed_leaks.run_mixed_leaks import development_streams as original_development_streams
from work.study.readout_comparison.select_reservoir import candidate_configs
from work.study.shared.signals import make_stream


class DelayChainTests(unittest.TestCase):
    def test_fixed_configs_independent_slots_and_original_controls(self):
        configs = dict(delay_candidates())
        self.assertEqual(configs, dict(delay_candidates()))
        self.assertEqual(configs["seed24_forward_leak0"], dict(candidate_configs(24, 1))["seed24/forward_leak0"])
        self.assertEqual(configs["cycle3210"], dict(mixed_candidates())["cycle3210"])
        for name in EXPERIMENT["root_age_weights"]:
            config = configs[name]
            self.assertEqual(config.state_bits, 6)
            self.assertEqual(config.leak_shifts, [0] * 16)
            for node, (recurrent, features) in enumerate(zip(config.recurrent_taps, config.feature_taps)):
                self.assertEqual((len(recurrent), len(features)), (3, 2))
                self.assertTrue(all(0 <= source < 16 for source, _ in recurrent))
                self.assertTrue(all(0 <= source < 3 for source, _ in features))
                self.assertEqual([tap for tap in recurrent if tap[1]], [[node - 1, 1]] if node else [])
                if node:
                    self.assertTrue(all(weight == 0 for _, weight in features))
        age = configs["age_chain"].to_dict()
        age["feature_taps"][0][1][1] = 0
        self.assertEqual(age, configs["level_chain"].to_dict())
        originals = deepcopy(configs)
        configs["age_chain"].feature_taps[0][0][1] = 7
        configs["age_chain"].recurrent_taps[1][0][1] = 7
        configs["age_chain"].leak_shifts[0] = 2
        self.assertEqual(configs["level_chain"], originals["level_chain"])
        self.assertEqual(dict(delay_candidates()), originals)

    def test_manual_root_sequence_and_simultaneous_propagation(self):
        reservoir = IntegerReservoir(dict(delay_candidates())["age_chain"])
        features = FeatureExtractor()
        # Hand-derived q: an initial low has age 1; edges have age 0;
        # successive high ages 1,2,3 have log buckets 1,2,2.
        expected = [[-2], [1, -2], [0, 1, -2], [-1, 0, 1, -2],
                    [-1, -1, 0, 1, -2], [-1, -1, -1, 0, 1, -2],
                    [-2, -1, -1, -1, 0, 1, -2]]
        for level, row in zip([0, 1, 1, 1, 1, 0, 0], expected, strict=True):
            self.assertEqual(reservoir.step(features.step(level)), tuple(row + [0] * (16 - len(row))))

    def test_current_plus_fifteen_previous_ticks_and_flush(self):
        configs = dict(delay_candidates())
        reservoir = IntegerReservoir(configs["level_chain"])
        features = FeatureExtractor()
        for tick in range(16):
            state = reservoir.step(features.step(int(tick == 0)))
            self.assertEqual(state[tick], 1)
        self.assertEqual(state, (-1,) * 15 + (1,))
        self.assertEqual(reservoir.step(features.step(0)), (-1,) * 16)
        for name, weight in EXPERIMENT["root_age_weights"].items():
            result = verify_chain(configs[name], weight)
            self.assertEqual(result["first_equal_update"], 16)
            self.assertEqual(result["maximum_initial_gap_by_update"], [63] * 15 + [0] * 17)
            # A nonuniform initial vector must also be fully displaced.
            left, right = IntegerReservoir(configs[name]), IntegerReservoir(configs[name])
            left.state = tuple(range(-8, 8))
            right.state = tuple(range(15, -1, -1))
            for tick in range(16):
                a, b = left.step((1, 0, 3)), right.step((1, 0, 3))
                self.assertEqual(a[:tick + 1], b[:tick + 1])
            self.assertEqual(a, b)

    def test_nominal_probe_timing_and_boundary_loss(self):
        configs = {name: config for name, config in delay_candidates() if name in EXPERIMENT["root_age_weights"]}
        probes = memory_probe_streams()
        self.assertEqual(len(probes), 255)
        self.assertEqual(probes[0]["stream"].windows[-1]["start"], 34)
        self.assertEqual([first_pulse_delay(3, 8, d) for d in range(4)], [12, 13, 14, 15])
        for name, config in configs.items():
            states = [collect_states(p["stream"], config) for p in probes]
            stats = memory_diagnostics(probes, states)
            first = stats["comparisons"][0]
            if name == "age_chain":
                self.assertTrue(all(first["full"]["cross_context_min_distance"]))
                self.assertEqual(first["bits"]["reset_distance"][-1], 0)
            else:
                self.assertEqual(first["full"]["reset_distance"], [2, 0, 0, 0])
            # Compare updated states, including the falling-edge root input.
            onset = probes[0]["stream"].windows[0]["start"]
            self.assertEqual(states[0][onset, 0], -1)
        timing = boundary_diagnostics(configs)
        self.assertEqual(len(timing["records"]), 204)
        for row in timing["records"]:
            for offset, inside in enumerate(row["last_first_high_inside"]):
                if not inside:
                    for stats in row["candidates"].values():
                        self.assertEqual(stats["full_distance"][offset], 0)
        self.assertEqual(first_pulse_delay(4, 9, 3), 17)
        self.assertEqual(first_pulse_delay(5, 10, 3), 19)

    def test_controls_never_win_and_rejections_never_fall_back(self):
        records = [{"name": name, "selection_key": [score, .8, -1], "rejection_reasons": reasons}
                   for name, score, reasons in [("age_chain", .5, ["probe failure"]),
                                                ("level_chain", .6, ["collision"]),
                                                ("cycle3210", 1, [])]]
        self.assertIsNone(choose_chain(records))
        records[0]["rejection_reasons"] = []
        self.assertEqual(choose_chain(records), "age_chain")
        records[1]["rejection_reasons"] = []
        self.assertEqual(choose_chain(records), "level_chain")

    def test_reload_and_streaming_replay_for_both_chains(self):
        train = [make_stream(1, 6), make_stream(2, 6)]
        stream = make_stream(3, 6)
        for name, config in delay_candidates():
            if name not in EXPERIMENT["root_age_weights"]:
                continue
            restored = ReservoirConfig(**json.loads(json.dumps(config.to_dict())))
            expected = collect_states(stream, config)
            np.testing.assert_array_equal(expected, collect_states(stream, restored))
            states = [collect_states(s, config) for s in train]
            methods = {}
            for kind in ("hamming", "linear_bits", "linear_full"):
                readout = fit_readout(train, states, kind)
                receiver = ReservoirReceiver(restored, readout, DecisionRule(-6 if kind == "hamming" else .4, .1), 2)
                methods[kind] = {"receiver": json.loads(json.dumps(receiver.to_dict()))}
            verify_reload(stream, expected, methods)

    def test_original_data_and_protected_results_and_seed_reuse(self):
        self.assertEqual(development_streams(), original_development_streams())
        for folder in ("latest", "selected", "mixed-leaks-seed24-test104/subdirectory"):
            with self.assertRaisesRegex(ValueError, "Protected"):
                reserve_output(Path(__file__).resolve().parents[1] / "results" / folder)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with self.assertRaisesRegex(ValueError, "new"):
                reserve_output(path)
            self.assertFalse(seed_inventory(path)["prior_use_found"])
            (path / "metrics.json").write_text(json.dumps({"experiment": {"test_seed": 105}}))
            with self.assertRaisesRegex(ValueError, "already used"):
                seed_inventory(path)

    def test_freeze_precedes_held_out_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new"

            def stop_at_test_generation(_):
                frozen = json.loads((output / "config.json").read_text())
                self.assertIsNone(frozen["selected_candidate"])
                for name in ("plan.json", "selection.json", "freeze.json"):
                    self.assertTrue((output / name).is_file())
                self.assertFalse((output / "test_streams.json").exists())
                raise RuntimeError("Reached test generation after freeze")

            with patch("work.study.delay_chains.run_delay_chains.seed_inventory", return_value={}), \
                    patch("work.study.delay_chains.run_delay_chains.boundary_diagnostics", return_value={}), \
                    patch("work.study.delay_chains.run_delay_chains.fit_candidates", return_value=({"selected_candidate": None, "candidates": []}, {})), \
                    patch("work.study.delay_chains.run_delay_chains.select_reference", return_value={}), \
                    patch("work.study.delay_chains.run_delay_chains.held_out_streams", side_effect=stop_at_test_generation):
                with self.assertRaisesRegex(RuntimeError, "after freeze"):
                    run(output)


if __name__ == "__main__":
    unittest.main()
