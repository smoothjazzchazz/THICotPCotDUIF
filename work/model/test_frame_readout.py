"""Framed scoring checks independent of the encoder's implementation."""

from types import SimpleNamespace
import unittest

from work.model.decision import DecisionStage
from work.model.readout import ClassScores, FramePrototypeReadout, StreamingTemplateReadout
from work.model.temporal import CompletedRun


def frame_samples(durations, start=30, valid=True):
    """Build only measured fields; readouts never receive the durations tuple."""
    yield SimpleNamespace(
        tick=start, frame_started=True, frame_complete=False, frame_active=True,
        frame_valid=valid, frame_start_tick=start, frame_run_count=0,
        completed_run=CompletedRun(0, 0, start))
    tick = start
    for index, duration in enumerate(durations):
        run = CompletedRun(1 - index % 2, tick, duration)
        tick += duration
        yield SimpleNamespace(
            tick=tick, frame_started=False, frame_complete=False, frame_active=True,
            frame_valid=valid, frame_start_tick=start, frame_run_count=index + 1,
            completed_run=run)
    # The falling edge above is the first delimiter low; 19 further samples are
    # needed for a 20-low delimiter. End-of-input itself never completes a frame.
    for offset in range(1, 20):
        yield SimpleNamespace(
            tick=tick + offset, frame_started=False, frame_complete=offset == 19,
            frame_active=offset != 19, frame_valid=valid, frame_start_tick=start,
            frame_run_count=len(durations), completed_run=None)


def feed(readout, durations, **kwargs):
    return [readout.step((), sample) for sample in frame_samples(durations, **kwargs)]


class StreamingTemplateTests(unittest.TestCase):
    def test_only_delimiter_emits_and_leading_idle_is_excluded(self):
        readout = StreamingTemplateReadout({0: (4, 8, 12), 1: (12, 8, 4)})
        results = feed(readout, (4, 8, 12), start=50)
        self.assertTrue(all(result is None for result in results[:-1]))
        self.assertEqual(results[-1], ClassScores(((0, 0.0), (1, -2.0)), 50))
        self.assertEqual(readout.progress, 3)

    def test_scale_is_global_and_error_is_worst_run(self):
        readout = StreamingTemplateReadout({0: (4, 8, 12)}, scales=(1, 2))
        self.assertEqual(feed(readout, (8, 16, 24))[-1].scores, ((0, 0.0),))
        # Mixing two speeds within one frame cannot select a new scale per run.
        self.assertEqual(feed(readout, (4, 16, 12))[-1].scores, ((0, -0.5),))

    def test_threshold_is_loaded_in_decision_and_is_inclusive(self):
        readout = StreamingTemplateReadout({0: (4, 8, 12)})
        decision = DecisionStage(minimum_score=-0.25)
        boundary = feed(readout, (5, 10, 15))[-1]
        self.assertEqual(boundary.scores, ((0, -0.25),))
        self.assertEqual(decision.classify(boundary.scores).class_id, 0)
        outside = feed(readout, (6, 10, 15))[-1]
        self.assertIsNone(decision.classify(outside.scores).class_id)

    def test_count_invalid_frame_and_recovery(self):
        readout = StreamingTemplateReadout({0: (4, 8, 12)})
        for durations in ((4,), (4, 8, 12, 8, 4)):
            self.assertEqual(feed(readout, durations)[-1].scores, ())
        self.assertEqual(feed(readout, (4, 8, 12), valid=False)[-1].scores, ())
        self.assertEqual(feed(readout, (4, 8, 12))[-1].scores, ((0, 0.0),))
        # An inconsistent count must not make missing observations look valid.
        sample = list(frame_samples((4, 8, 12)))[-1]
        sample.frame_run_count = 1
        self.assertEqual(readout.step((), sample).scores, ())

    def test_reset_configuration_copy_and_instance_independence(self):
        templates = {0: [4, 8, 12]}
        scales = [1, 2]
        first = StreamingTemplateReadout(templates, scales)
        second = StreamingTemplateReadout(templates, scales)
        initial = first.state
        templates[0][0] = 99
        scales[0] = 99
        feed(first, (6, 8, 12))
        snapshot = first.state
        self.assertEqual(second.state, initial)
        self.assertNotEqual(first.state, initial)
        first.reset()
        self.assertEqual(first.state, initial)
        self.assertEqual(snapshot[0], 3)
        self.assertEqual(first.templates[0], (4, 8, 12))
        self.assertEqual(first.scales, (1, 2))
        feed(first, (4, 8, 12))
        retained = first.state
        idle = list(frame_samples((4, 8, 12)))[-1]
        idle.frame_complete = False
        self.assertIsNone(first.step((), idle))
        self.assertEqual(first.state, retained)

    def test_constructor_validation(self):
        for bad in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    StreamingTemplateReadout({0: (bad,)})
                with self.assertRaises(ValueError):
                    StreamingTemplateReadout({0: (4,)}, scales=(bad,))
        for templates, scales in (({0: ()}, (1,)), ({None: (4,)}, (1,)),
                                  ({0: (4,)}, ())):
            with self.assertRaises(ValueError):
                StreamingTemplateReadout(templates, scales)


class FramePrototypeTests(unittest.TestCase):
    def test_nearest_exemplar_and_completion_timestamp(self):
        readout = FramePrototypeReadout({0: ((0, 0), (2, 2)), 1: ((4, 4),)})
        samples = list(frame_samples((4, 8, 12), start=50))
        self.assertTrue(all(readout.step((2, 2), sample) is None
                            for sample in samples[:-1]))
        self.assertEqual(readout.step((2, 2), samples[-1]),
                         ClassScores(((0, 0.0), (1, -4.0)), 50))

    def test_validity_and_optional_count_gate(self):
        plain = FramePrototypeReadout({0: ((1, 2),)})
        guarded = FramePrototypeReadout({0: ((1, 2),)}, expected_runs=3)
        short = list(frame_samples((4,)))[-1]
        self.assertEqual(plain.step((1, 2), short).scores, ((0, 0.0),))
        self.assertEqual(guarded.step((1, 2), short).scores, ())
        complete = list(frame_samples((4, 8, 12)))[-1]
        self.assertEqual(guarded.step((1, 2), complete).scores, ((0, 0.0),))
        complete.frame_valid = False
        self.assertEqual(plain.step((1, 2), complete).scores, ())
        self.assertEqual(guarded.step((1, 2), complete).scores, ())

    def test_config_copy_reset_and_dimension_check(self):
        prototypes = {0: [[0, 0], [2, 2]]}
        readout = FramePrototypeReadout(prototypes)
        prototypes[0][1][0] = 99
        prototypes[0].append([100, 100])
        sample = list(frame_samples((4, 8, 12)))[-1]
        expected = ClassScores(((0, 0.0),), 30)
        self.assertEqual(readout.step((2, 2), sample), expected)
        readout.reset()
        self.assertEqual(readout.step((2, 2), sample), expected)
        with self.assertRaises(ValueError):
            readout.step((2,), sample)
        self.assertEqual(FramePrototypeReadout({}).step((), sample).scores, ())

    def test_constructor_validation(self):
        for prototypes in ({0: ()}, {0: ((),)}, {0: ((0,), (0, 1))},
                           {None: ((0,),)}, {0: ((float("nan"),),)},
                           {0: ((float("inf"),),)}):
            with self.subTest(prototypes=prototypes):
                with self.assertRaises(ValueError):
                    FramePrototypeReadout(prototypes)
        for count in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                FramePrototypeReadout({0: ((0,),)}, expected_runs=count)


if __name__ == "__main__":
    unittest.main()
