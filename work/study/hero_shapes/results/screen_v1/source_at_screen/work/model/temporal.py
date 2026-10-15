"""Measure levels and runs without assigning classes or guessing boundaries."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CompletedRun:
    level: int
    start_tick: int
    duration: int


@dataclass(frozen=True)
class TemporalSample:
    tick: int
    level: int
    transition: int
    run_start_tick: int
    elapsed_ticks: int
    completed_run: CompletedRun | None

    @property
    def features(self):
        # A small shared numerical representation; exact timing remains above.
        return (2.0 * self.level - 1.0, float(self.transition),
                min(self.elapsed_ticks, 7) / 7.0)


class TemporalEncoder:
    def __init__(self):
        self.reset()

    def reset(self):
        self.level = None
        self.run_start_tick = None
        self.last_tick = None

    def step(self, level, tick):
        if level not in (0, 1):
            raise ValueError("level must be 0 or 1")
        if not isinstance(tick, int) or tick < 0:
            raise ValueError("tick must be a nonnegative integer")
        if self.last_tick is not None and tick != self.last_tick + 1:
            raise ValueError("one sample is required per consecutive tick")
        completed_run = None
        transition = 0
        if self.level is None:
            # Reset has no observed predecessor, so the first sample is no edge.
            self.run_start_tick = tick
        elif level != self.level:
            transition = level - self.level
            completed_run = CompletedRun(
                self.level, self.run_start_tick, tick - self.run_start_tick)
            self.run_start_tick = tick
        self.level = level
        self.last_tick = tick
        return TemporalSample(tick, level, transition, self.run_start_tick,
                              tick - self.run_start_tick, completed_run)


@dataclass(frozen=True)
class FramedTemporalSample(TemporalSample):
    frame_started: bool
    frame_complete: bool
    frame_valid: bool
    frame_start_tick: int | None
    frame_run_count: int
    frame_active: bool


class FramedTemporalEncoder(TemporalEncoder):
    """Qualify low-idle boundaries using only samples seen so far.

    Twenty low samples means completion at falling_edge + 19, not +20.
    A burst observed before any complete idle delimiter is explicitly invalid.
    Long/overfull bursts remain invalid until their actual delimiter; counters
    saturate instead of rolling over and making a valid-looking suffix.
    """

    def __init__(self, idle_ticks=20, max_runs=31, max_frame_ticks=512,
                 startup_ignore_ticks=0):
        if any(not isinstance(n, int) or n < 1
               for n in (idle_ticks, max_runs, max_frame_ticks)):
            raise ValueError("framing limits must be positive integers")
        self.idle_ticks = idle_ticks
        self.max_runs = max_runs
        self.max_frame_ticks = max_frame_ticks
        if not isinstance(startup_ignore_ticks, int) or startup_ignore_ticks < 0:
            raise ValueError("startup_ignore_ticks must be nonnegative")
        self.startup_ignore_ticks = startup_ignore_ticks
        self.reset()

    def reset(self):
        super().reset()
        self.armed = False
        self.frame_active = False
        self.frame_valid = False
        self.frame_start_tick = None
        self.frame_run_count = 0

    def step(self, level, tick):
        sample = super().step(level, tick)
        started = complete = False
        if level == 1 and not self.frame_active:
            started = True
            self.frame_active = True
            self.frame_valid = self.armed
            self.frame_start_tick = tick
            self.frame_run_count = 0
            self.armed = False
        if self.frame_active:
            if sample.completed_run is not None and not started:
                self.frame_run_count = min(self.frame_run_count + 1,
                                           self.max_runs + 1)
            if (self.frame_run_count > self.max_runs
                    or tick - self.frame_start_tick > self.max_frame_ticks):
                self.frame_valid = False
        # A conditioner can emit its reset fill before real samples propagate.
        # Those ticks cannot qualify an observed delimiter. The composer loads
        # the known delay + filter settling time; this is not a stimulus marker.
        observed_idle = min(sample.elapsed_ticks + 1,
                            max(0, tick - self.startup_ignore_ticks + 1))
        if level == 0 and observed_idle >= self.idle_ticks:
            complete = self.frame_active
            self.frame_active = False
            self.armed = True
        return FramedTemporalSample(
            sample.tick, sample.level, sample.transition, sample.run_start_tick,
            sample.elapsed_ticks, sample.completed_run, started, complete,
            self.frame_valid, self.frame_start_tick, self.frame_run_count,
            self.frame_active)
