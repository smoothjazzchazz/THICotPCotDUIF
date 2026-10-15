"""Loaded parameters turn memory into scores; fitting belongs in work/study."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ClassScores:
    scores: tuple[tuple[int, float], ...]
    start_tick: int


class PrototypeReadout:
    """Higher score = smaller mean squared distance to a loaded prototype.

    A falling trigger is a measured high-run completion, not a stimulus marker.
    every_tick instead supports continuous recognition and tick stabilization.
    """

    def __init__(self, prototypes, trigger="falling"):
        if trigger not in ("falling", "every_tick"):
            raise ValueError("trigger must be falling or every_tick")
        self.prototypes = {class_id: tuple(values)
                           for class_id, values in prototypes.items()}
        dimensions = {len(values) for values in self.prototypes.values()}
        if len(dimensions) > 1 or 0 in dimensions:
            raise ValueError("prototypes must have a common nonzero dimension")
        if any(not isinstance(class_id, int) for class_id in self.prototypes):
            raise ValueError("class IDs must be integers; None is unknown")
        if any(not isfinite(value) for row in self.prototypes.values() for value in row):
            raise ValueError("prototype values must be finite")
        self.trigger = trigger

    def reset(self):
        pass  # Loaded parameters survive reset; this stage has no runtime state.

    def step(self, memory_state, sample):
        if self.trigger == "falling":
            if sample.completed_run is None or sample.completed_run.level != 1:
                return None
            start_tick = sample.completed_run.start_tick
        else:
            start_tick = sample.tick
        scores = []
        for class_id, prototype in self.prototypes.items():
            if len(memory_state) != len(prototype):
                raise ValueError("memory/prototype dimensions differ; refit the readout")
            distance = 0.0
            for value, expected in zip(memory_state, prototype):
                distance += (value - expected) ** 2
            scores.append((class_id, -distance / len(prototype)))
        return ClassScores(tuple(scores), start_tick)


class PulseLengthReadout:
    """Keep the original exact-duration baseline behind the same score interface.

    This deliberately bypasses memory and reads a completed measurement. It is a
    conventional baseline, not evidence that either memory recognizes patterns.
    """

    def __init__(self, pulse_length_to_class):
        self.pulse_length_to_class = dict(pulse_length_to_class)

    def reset(self):
        pass

    def step(self, memory_state, sample):
        run = sample.completed_run
        if run is None or run.level != 1:
            return None
        class_id = self.pulse_length_to_class.get(run.duration)
        scores = () if class_id is None else ((class_id, 0.0),)
        return ClassScores(scores, run.start_tick)


class StreamingTemplateReadout:
    """Compare runs as they arrive, keeping errors rather than run history.

    Templates contain alternating high/low durations, starting with high. Each
    loaded scale is a separate timing hypothesis. A hypothesis retains its
    largest relative duration error; a class gets the best hypothesis's negative
    error. DecisionStage applies the loaded score cutoff and winning margin.

    Only an observed frame delimiter releases scores. The encoder owns framing
    and validity, including startup and overflow. A frame-start signal clears
    errors and excludes the completed leading idle run. No generated-example
    reset, label, or look-ahead is used here.

    For C classes, S scales and L runs per template, loaded storage is C*L + S
    values. Runtime storage is C*S errors and one run counter. Each completed
    run computes C*S relative errors and maxima, and completion reduces S errors
    per eligible class. There is no whole-frame input buffer or per-tick vector
    computation. These are floating-point software counts, not hardware costs.
    """

    def __init__(self, templates, scales=(1.0,)):
        self.templates = {class_id: tuple(durations)
                          for class_id, durations in templates.items()}
        self.scales = tuple(scales)
        if any(not isinstance(class_id, int) for class_id in self.templates):
            raise ValueError("class IDs must be integers; None is unknown")
        if any(not durations for durations in self.templates.values()):
            raise ValueError("each template must contain at least one duration")
        if any(not isfinite(value) or value <= 0
               for durations in self.templates.values() for value in durations):
            raise ValueError("template durations must be finite and positive")
        if not self.scales or any(not isfinite(scale) or scale <= 0
                                  for scale in self.scales):
            raise ValueError("scales must be finite and positive")
        if any(not isfinite(duration * scale) or duration * scale == 0
               for durations in self.templates.values()
               for duration in durations for scale in self.scales):
            raise ValueError("scaled durations must remain finite and positive")
        self.max_progress = max(map(len, self.templates.values()), default=0) + 1
        self.reset()

    def reset(self):
        self.progress = 0
        self.errors = {class_id: [0.0] * len(self.scales)
                       for class_id in self.templates}

    @property
    def state(self):
        """An immutable snapshot survives later updates to this readout."""
        return (self.progress, tuple((class_id, tuple(errors))
                                     for class_id, errors in self.errors.items()))

    def step(self, memory_state, sample):
        if sample.frame_started:
            self.reset()
        elif sample.completed_run is not None and (
                sample.frame_active or sample.frame_complete):
            run = sample.completed_run
            for class_id, durations in self.templates.items():
                if self.progress >= len(durations):
                    continue
                for index, scale in enumerate(self.scales):
                    error = abs(run.duration / (durations[self.progress] * scale) - 1)
                    self.errors[class_id][index] = max(
                        self.errors[class_id][index], error)
            self.progress = min(self.progress + 1, self.max_progress)
        if not sample.frame_complete:
            return None
        if not sample.frame_valid or sample.frame_run_count != self.progress:
            return ClassScores((), sample.frame_start_tick)
        scores = tuple((class_id, -min(self.errors[class_id]))
                       for class_id, durations in self.templates.items()
                       if self.progress == len(durations))
        return ClassScores(scores, sample.frame_start_tick)


class FramePrototypeReadout:
    """Nearest loaded exemplar per class, evaluated at the observed delimiter.

    The supplied memory tuple may be a latched pre-delimiter state. Latching and
    any input buffering belong to the memory stage, so they stay visible in its
    state and resource accounting. Fitting exemplars belongs in work/study.
    expected_runs optionally adds explicit measured-count validity; it is extra
    information beyond the memory vector and must be named in comparisons.

    For P total prototypes of dimension D, this stage stores P*D loaded values,
    holds no inference history, and computes P*D squared differences at each
    completed valid frame. Each class score is minus its smallest mean squared
    distance. The unbounded precision and same-tick arithmetic are software
    modeling assumptions, not a proposed hardware schedule.
    """

    def __init__(self, prototypes, expected_runs=None):
        self.prototypes = {
            class_id: tuple(tuple(vector) for vector in vectors)
            for class_id, vectors in prototypes.items()}
        if any(not isinstance(class_id, int) for class_id in self.prototypes):
            raise ValueError("class IDs must be integers; None is unknown")
        if any(not vectors for vectors in self.prototypes.values()):
            raise ValueError("each class needs at least one prototype")
        dimensions = {len(vector) for vectors in self.prototypes.values()
                      for vector in vectors}
        if len(dimensions) > 1 or 0 in dimensions:
            raise ValueError("prototypes must have a common nonzero dimension")
        if any(not isfinite(value) for vectors in self.prototypes.values()
               for vector in vectors for value in vector):
            raise ValueError("prototype values must be finite")
        if expected_runs is not None and (
                not isinstance(expected_runs, int) or expected_runs < 1):
            raise ValueError("expected_runs must be a positive integer or None")
        self.expected_runs = expected_runs

    def reset(self):
        pass  # Memory owns inference state; loaded exemplars survive reset.

    def step(self, memory_state, sample):
        if not sample.frame_complete:
            return None
        if not sample.frame_valid or (self.expected_runs is not None
                                     and sample.frame_run_count != self.expected_runs):
            return ClassScores((), sample.frame_start_tick)
        scores = []
        for class_id, prototypes in self.prototypes.items():
            distances = []
            for prototype in prototypes:
                if len(memory_state) != len(prototype):
                    raise ValueError("memory/prototype dimensions differ; refit the readout")
                distance = 0.0
                for value, expected in zip(memory_state, prototype):
                    distance += (value - expected) ** 2
                distances.append(distance / len(prototype))
            scores.append((class_id, -min(distances)))
        return ClassScores(tuple(scores), sample.frame_start_tick)
