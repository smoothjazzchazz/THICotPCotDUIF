"""Focused integration checks for causal framing and end-to-end evaluation."""

from copy import deepcopy
import unittest

from work.model.controller import ResponseRequest
from work.model.temporal import FramedTemporalEncoder

from .models import build_receiver, candidate_configs, simulate
from .scoring import response_check, score_events
from .stimuli import FAMILIES, expand_runs


class HeroIntegrationTests(unittest.TestCase):
    def config(self, kind="stream_templates"):
        config = next(c for c in candidate_configs("pulse_order") if c["kind"] == kind)
        config["minimum_score"] = -.34
        return config

    def test_framing_conditioning_and_exact_response_latency(self):
        config = self.config()
        burst = expand_runs(FAMILIES["pulse_order"]["templates"][0])
        for idle in (19, 20, 40):
            for delay in (0, 1, 2, 25):
                with self.subTest(idle=idle, delay=delay):
                    config["delay_ticks"] = delay
                    trace = simulate([0] * idle + burst + [0] * 80, config)
                    emitted = [row for row in trace if row["event"] is not None]
                    self.assertEqual(len(emitted), 1)
                    event = emitted[0]["event"]
                    self.assertEqual(event.class_id, 0 if idle >= 20 else None)
                    self.assertEqual(event.start_tick, idle + delay + 1)
                    self.assertEqual(event.decision_tick, idle + len(burst) + delay + 20)
                    if idle >= 20:
                        self.assertEqual(trace[event.decision_tick + 1]["output_level"], 1)
                        self.assertEqual(response_check(trace, config)["waveform_mismatch_ticks"], [])

    def test_reset_instance_independence_and_causal_prefix_all_topologies(self):
        prefix = [0] * 24 + expand_runs((4, 4, 8))
        for config in candidate_configs("pulse_order"):
            with self.subTest(kind=config["kind"]):
                first = simulate(prefix, config)
                for future in ([0] * 60, [1] * 60):
                    self.assertEqual(first, simulate(prefix + future, config)[:len(prefix)])
                receiver = build_receiver(config)
                other = build_receiver(config)
                initial = other.memory.state
                for tick, value in enumerate(prefix):
                    receiver.step(value, tick)
                self.assertEqual(other.memory.state, initial)
                self.assertIsNone(other.observation)
                receiver.reset()
                for tick, value in enumerate(prefix):
                    receiver.step(value, tick)
                self.assertEqual(receiver.observation, first[-1]["receiver_state"])
                self.assertTrue(all(r["event"] is None for r in first))

    def test_minimum_gap_missing_delimiter_overflow_and_recovery(self):
        config = self.config()
        burst = expand_runs((4, 4, 8, 4, 4))
        for gap in (19, 20, 21):
            trace = simulate([0] * 24 + burst + [0] * gap + burst + [0] * 40, config)
            events = [row["event"].class_id for row in trace if row["event"] is not None]
            self.assertEqual(events, [None] if gap == 19 else [0, 0])
        junk = expand_runs((2,) * 35)
        trace = simulate([0] * 24 + junk + [0] * 24 + burst + [0] * 40, config)
        self.assertEqual([r["event"].class_id for r in trace if r["event"]], [None, 0])
        self.assertLessEqual(max(r["receiver_state"].temporal.frame_run_count for r in trace), 32)

    def test_incomplete_tail_and_long_high_are_not_silently_flushed(self):
        config = self.config()
        burst = expand_runs((4, 4, 8, 4, 4))
        trace = simulate([0] * 24 + burst + [0] * 20, config)
        self.assertFalse(any(r["event"] for r in trace))
        trace = simulate([0] * 24 + [1] * 600 + [0] * 24 + burst + [0] * 40, config)
        self.assertEqual([r["event"].class_id for r in trace if r["event"]], [None, 0])

    def test_scorer_exposes_duplicate_wrong_early_background_and_bad_response(self):
        stream = {"samples": [0] * 100, "cases": [
            {"id": "one", "condition": "known", "start_tick": 24, "end_tick": 48, "class_id": 0}]}
        events = [{"class_id": 0, "start_tick": 26, "decision_tick": 69},
                  {"class_id": 1, "start_tick": 26, "decision_tick": 70},
                  {"class_id": 0, "start_tick": 26, "decision_tick": 47},
                  {"class_id": 0, "start_tick": 26, "decision_tick": 71}]
        totals = score_events(events, stream)["totals"]
        self.assertEqual(totals["correct_known"], 1)
        self.assertEqual(totals["duplicates"], 2)
        self.assertEqual(totals["wrong_class_events"], 1)
        self.assertEqual(totals["early_or_late_known"], 1)
        self.assertEqual(totals["background_known"], 1)
        config = self.config()
        trace = simulate([0] * 24 + expand_runs((4, 4, 8, 4, 4)) + [0] * 40, config)
        damaged = deepcopy(trace)
        emitted = next(row for row in damaged if row["event"] is not None)
        emitted["request"] = ResponseRequest(0, emitted["tick"] - 1)
        damaged[emitted["tick"] + 1]["output_level"] = 0
        check = response_check(damaged, config)
        self.assertEqual(check["request_mismatch_ticks"], [emitted["tick"]])
        self.assertEqual(check["waveform_mismatch_ticks"], [emitted["tick"] + 1])

    def test_run_history_collision_and_loaded_reconfiguration(self):
        def decision_memory(kind, runs):
            trace = simulate([0] * 24 + expand_runs(runs) + [0] * 40, self.config(kind))
            return next(r["receiver_state"].memory for r in trace if r["event"] is not None)
        known = (4, 4, 8, 4, 4)
        unknown = (6, 2, 8, 4, 4)
        self.assertEqual(decision_memory("sample12", known), decision_memory("sample12", unknown))
        self.assertNotEqual(decision_memory("run_history", known), decision_memory("run_history", unknown))
        config = self.config()
        config["templates"] = {0: unknown, 1: (8, 4, 4, 4, 4)}
        config["minimum_score"] = 0
        config["responses"] = {0: [0, 1, 1], 1: [1, 0]}
        trace = simulate([0] * 24 + expand_runs(unknown) + [0] * 40, config)
        event = next(r["event"] for r in trace if r["event"] is not None)
        self.assertEqual(event.class_id, 0)
        self.assertEqual([r["output_level"] for r in trace[event.decision_tick+1:event.decision_tick+4]], [0, 1, 1])


if __name__ == "__main__":
    unittest.main()
