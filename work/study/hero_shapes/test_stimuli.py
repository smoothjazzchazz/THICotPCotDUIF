"""Data-integrity checks: these validate labels and challenges, not recognition."""

import json
import unittest

from work.study.hero_shapes.stimuli import (
    FAMILIES, IDLE_TICKS, RESERVED_CONDITIONS, RESERVED_RELATIVE_CONDITIONS, build_startup_streams,
    build_stream, conditioned_runs, expand_runs, known_matches,
    nominal_diagnostic_pairs,
)


class StimuliTests(unittest.TestCase):
    def test_definitions_require_order_information(self):
        for family, definition in FAMILIES.items():
            first, second = definition["templates"].values()
            self.assertNotEqual(first, second, family)
            self.assertEqual(sum(first), sum(second), family)
            self.assertEqual(len(first), len(second), family)
            self.assertEqual(first[-2:], second[-2:], family)
            for scale in definition["scales"]:
                self.assertLess(max(first[1::2]) * scale, IDLE_TICKS, family)
                self.assertLess(max(second[1::2]) * scale, IDLE_TICKS, family)

    def test_replay_json_and_annotations(self):
        for family in FAMILIES:
            for split, maximum in (("train", 30), ("dev", 60), ("heldout", 100)):
                stream = build_stream(family, split, 301)
                self.assertEqual(stream, build_stream(family, split, 301))
                json.dumps(stream)
                self.assertLessEqual(len(stream["cases"]), maximum)
                previous = None
                for case in stream["cases"]:
                    waveform = stream["samples"][case["start_tick"]:case["end_tick"]]
                    self.assertEqual(waveform, expand_runs(case["raw_runs"]))
                    self.assertEqual(list(conditioned_runs(waveform)), case["conditioned_runs"])
                    if previous:
                        gap = case["start_tick"] - previous["end_tick"]
                        self.assertGreaterEqual(gap, 20 if previous["boundary_challenge"] else 24)
                    previous = case

    def test_unknowns_outside_all_known_envelopes(self):
        for family in FAMILIES:
            for split in ("dev", "heldout"):
                for seed in range(6):
                    for case in build_stream(family, split, seed)["cases"]:
                        matches = known_matches(family, case["conditioned_runs"])
                        if case["class_id"] is None:
                            self.assertEqual(matches, [], case["id"])
                        else:
                            self.assertIn(case["class_id"], [label for label, _ in matches])

    def test_jitter_vocabulary_is_separate_and_splices_reserved(self):
        for family in FAMILIES:
            vocabularies = []
            reserved = set(RESERVED_CONDITIONS)
            if family == "relative_order":
                reserved.update(RESERVED_RELATIVE_CONDITIONS)
            for split in ("train", "dev", "heldout"):
                cases = build_stream(family, split, 501, repeats=20)["cases"]
                vocabularies.append({tuple(case["jitter_delta"]) for case in cases
                                     if case["jitter_delta"] is not None})
                conditions = {case["condition"] for case in cases}
                if split == "train":
                    self.assertTrue(conditions <= {"known_clean", "known_jitter"})
                if split != "heldout":
                    self.assertFalse(conditions.intersection(reserved))
                else:
                    self.assertTrue(reserved <= conditions)
            self.assertFalse(vocabularies[0] & vocabularies[1])
            self.assertFalse(vocabularies[0] & vocabularies[2])
            self.assertFalse(vocabularies[1] & vocabularies[2])

    def test_glitches_preserve_full_known_shape_and_background_is_removed(self):
        for family in FAMILIES:
            stream = build_stream(family, "heldout", 606)
            for case in stream["cases"]:
                if case["condition"] == "known_glitch":
                    expected = [n * case["scale"] for n in FAMILIES[family]["templates"][case["class_id"]]]
                    self.assertEqual(case["conditioned_runs"], expected)
                    self.assertNotEqual(case["raw_runs"], expected)
            for case in stream["unobservable_cases"]:
                waveform = stream["samples"][case["start_tick"]:case["end_tick"]]
                self.assertEqual(conditioned_runs(waveform), ())

    def test_startup_and_delimiter_challenges(self):
        for family in FAMILIES:
            for stream in build_startup_streams(family, 901):
                first = stream["cases"][0]
                self.assertIsNone(first["class_id"])
                self.assertFalse(first["expected_valid_frame"])
                self.assertLess(first["start_tick"], IDLE_TICKS)
                self.assertEqual([case["class_id"] for case in stream["cases"][1:]], [0, 1])
            cases = build_stream(family, "heldout", 901)["cases"]
            short_gaps = [a for a, b in zip(cases, cases[1:])
                          if b["start_tick"] - a["end_tick"] == IDLE_TICKS]
            self.assertEqual(len(short_gaps), 3)
            for pair in nominal_diagnostic_pairs(family):
                self.assertEqual(sum(pair["left_runs"]), sum(pair["right_runs"]))
                self.assertEqual(len(pair["left_runs"]), len(pair["right_runs"]))


if __name__ == "__main__":
    unittest.main()
