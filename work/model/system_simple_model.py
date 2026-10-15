"""Shared receiver composition and the single waveform-to-waveform runner."""

from dataclasses import dataclass

from work.model.conditioning import ConditionedSample, InputConditioner
from work.model.controller import MappingController
from work.model.decision import DecisionOutput, DecisionStage, SymbolEvent
from work.model.memory import ExplicitHistory
from work.model.readout import ClassScores, PulseLengthReadout
from work.model.temporal import TemporalEncoder, TemporalSample
from work.model.transmit_simple_model import Transmitter


@dataclass(frozen=True)
class ReceiverObservation:
    conditioned: ConditionedSample
    temporal: TemporalSample
    memory: tuple[float, ...]
    readout: ClassScores | None
    decision: DecisionOutput


class StagedReceiver:
    """Pass owned stage instances directly; there is no registry or plugin layer."""

    def __init__(self, conditioner, encoder, memory, readout, decision):
        self.conditioner = conditioner
        self.encoder = encoder
        self.memory = memory
        self.readout = readout
        self.decision = decision
        self.reset()

    def reset(self):
        self.conditioner.reset()
        self.encoder.reset()
        self.memory.reset()
        self.readout.reset()
        self.decision.reset()
        self.observation = None

    def step(self, input_level, tick):
        conditioned = self.conditioner.step(input_level)
        temporal = self.encoder.step(conditioned.level, tick)
        memory_state = self.memory.step(temporal)
        scores = self.readout.step(memory_state, temporal)
        decision = self.decision.step(scores, tick)
        self.observation = ReceiverObservation(
            conditioned, temporal, memory_state, scores, decision)
        return decision.event


class PulseReceiver(StagedReceiver):
    """Original constructor/event format, now using the shared receive stages."""

    def __init__(self, pulse_length_to_class):
        super().__init__(InputConditioner(), TemporalEncoder(), ExplicitHistory(1),
                         PulseLengthReadout(pulse_length_to_class), DecisionStage())

    @property
    def high_count(self):
        if self.observation is None or self.observation.temporal.level == 0:
            return 0
        return self.observation.temporal.elapsed_ticks + 1

    @property
    def start_tick(self):
        return self.encoder.run_start_tick if self.high_count else None

    @property
    def pulse_length_to_class(self):
        return self.readout.pulse_length_to_class

    def step(self, input_level, tick):
        return legacy_event(super().step(input_level, tick))


def legacy_event(event):
    """Only the original dictionary interface reserves class 7 for unknown."""
    if event is None:
        return None
    return {"class_id": 7 if event.class_id is None else event.class_id,
            "start_tick": event.start_tick}


def typed_event(event, tick):
    if event is None or isinstance(event, SymbolEvent):
        return event
    class_id = event["class_id"]
    return SymbolEvent(None if class_id == 7 else class_id, event["start_tick"], tick)


def controller_action(event, request):
    if request is not None:
        return f"request symbol {request.symbol_id}"
    if event is not None:
        class_id = 7 if event.class_id is None else event.class_id
        return f"consume class {class_id}"
    return "idle"


class Controller:
    """Compatibility wrapper for the original queue-based controller API."""

    def __init__(self, class_to_transmit_symbol):
        self.mapping = MappingController(class_to_transmit_symbol)
        self.class_to_transmit_symbol = self.mapping.class_to_transmit_symbol

    def reset(self):
        self.mapping.reset()

    def step(self, rx_queue, transmitter):
        event = typed_event(rx_queue.popleft(), 0) if rx_queue else None
        request = self.mapping.step(event, 0)
        if request is not None:
            transmitter.send(request.symbol_id)
        return controller_action(event, request)


def run_simulation(input_levels, receiver=None, controller=None, transmitter=None):
    """Run a fresh tick-zero epoch; supplied components reset but keep parameters.

    input_levels may be a generator. No length, look-ahead, labels, or implicit
    tail flush is used. Supply actual trailing samples to finish RX runs/TX work.
    """
    receiver = PulseReceiver({2: 0, 4: 1}) if receiver is None else receiver
    controller = MappingController({0: 2, 1: 1}) if controller is None else controller
    transmitter = Transmitter() if transmitter is None else transmitter
    receiver.reset()
    controller.reset()
    transmitter.reset()
    trace = []

    for tick, input_level in enumerate(input_levels):
        # TX runs first: a request made below can start at t+1, never at t.
        output_level = transmitter.step()
        event = typed_event(receiver.step(input_level, tick), tick)
        request = controller.step(event, tick)
        if request is not None:
            transmitter.send(request.symbol_id)
        trace.append({
            "tick": tick,
            "input_level": input_level,
            "high_count": getattr(receiver, "high_count", None),
            "receiver_state": receiver.observation,
            "event": event,
            "rx_event": legacy_event(event),
            "request": request,
            "controller_action": controller_action(event, request),
            "output_level": output_level,
        })
    return trace


def print_trace(title, trace):
    """Two lines per tick keep the full memory visible without hiding zeroes."""
    print(f"\n{title}")
    print("raw -> delayed -> conditioned; elapsed starts at 0; '-' means absent")
    for row in trace:
        observation = row["receiver_state"]
        conditioned = observation.conditioned
        temporal = observation.temporal
        run = temporal.completed_run
        completed = "-" if run is None else f"{run.level}x{run.duration}@{run.start_tick}"
        scores = "-" if observation.readout is None else str(
            [(class_id, round(score, 5)) for class_id, score in observation.readout.scores])
        candidate = observation.decision.candidate
        decision = "no evaluation" if candidate is None else (
            f"{'unknown' if candidate.class_id is None else candidate.class_id}"
            f" ({candidate.reason}, hold={observation.decision.stable_ticks})")
        event = row["event"]
        event_text = "-" if event is None else (
            f"{'unknown' if event.class_id is None else event.class_id}"
            f"@{event.start_tick},emit={event.decision_tick}")
        request = row["request"]
        request_text = "-" if request is None else str(request.symbol_id)
        output = "idle" if row["output_level"] is None else str(row["output_level"])
        print(f"t={row['tick']:02d} in={conditioned.raw_level}->{conditioned.delayed_level}"
              f"->{conditioned.level} edge={temporal.transition:+d}"
              f" elapsed={temporal.elapsed_ticks} done={completed}"
              f" | event={event_text} request={request_text} tx={output}")
        print(f"     features={tuple(round(x, 3) for x in temporal.features)}"
              f" memory={tuple(round(x, 3) for x in observation.memory)}"
              f" scores={scores} decision={decision}")


def main():
    # Stimuli, fitting and settings live with the example, not in the pipeline.
    from work.study.stage_demo.run_demo import main as run_demo
    run_demo()


if __name__ == "__main__":
    main()
