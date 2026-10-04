"""A one-lane waveform-to-event-to-waveform scaffold."""

from collections import deque

from work.model.transmit_simple_model import Transmitter


class PulseReceiver:
    def __init__(self, pulse_length_to_class):
        self.pulse_length_to_class = pulse_length_to_class
        self.high_count = 0
        self.start_tick = None

    def step(self, input_level, tick):
        if input_level == 1:
            if self.high_count == 0:
                self.start_tick = tick
            self.high_count += 1
            return None

        if self.high_count == 0:
            return None

        # The first low sample completes the pulse; its timestamp stays at the start.
        event = {
            "class_id": self.pulse_length_to_class.get(self.high_count, 7),
            "start_tick": self.start_tick,
        }
        self.high_count = 0
        self.start_tick = None
        return event


class Controller:
    def __init__(self, class_to_transmit_symbol):
        self.class_to_transmit_symbol = class_to_transmit_symbol

    def step(self, rx_queue, transmitter):
        if not rx_queue:
            return "idle"

        event = rx_queue.popleft()
        class_id = event["class_id"]
        # Class 7 stays unknown even if the response mapping includes it.
        if class_id == 7 or class_id not in self.class_to_transmit_symbol:
            return f"consume class {class_id}"

        symbol_id = self.class_to_transmit_symbol[class_id]
        transmitter.send(symbol_id)
        return f"request symbol {symbol_id}"


def run_simulation(input_levels, receiver=None):
    # Both receivers emit class IDs and timestamps that the controller can use.
    if receiver is None:
        receiver = PulseReceiver({2: 0, 4: 1})
    rx_queue = deque()
    controller = Controller({0: 2, 1: 1})
    transmitter = Transmitter([])
    trace = []

    for tick, input_level in enumerate(input_levels):
        # Advance TX first so requests made below begin no earlier than the next tick.
        output_level = transmitter.step()
        rx_event = receiver.step(input_level, tick)
        if rx_event is not None:
            rx_queue.append(rx_event)
        controller_action = controller.step(rx_queue, transmitter)

        # Keep the emitted event even when the controller consumed it this tick.
        trace.append({
            "tick": tick,
            "input_level": input_level,
            "high_count": getattr(receiver, "high_count", None),
            "receiver_state": getattr(receiver, "observation", {}),
            "rx_event": rx_event,
            "controller_action": controller_action,
            "output_level": output_level,
        })

    return trace


def print_trace(title, trace):
    print(f"\n{title}")
    header = (
        f"{'tick':>4} | {'input':>5} | {'high count':>10} | "
        f"{'RX event':<16} | {'controller action':<18} | {'output':>6}"
    )
    print(header)
    print("-" * len(header))

    ticks = []
    input_levels = []
    output_levels = []
    for row in trace:
        event = row["rx_event"]
        event_text = "-"
        if event is not None:
            event_text = f"class {event['class_id']}, start {event['start_tick']}"

        output_text = "idle"
        # Testing truthiness here would incorrectly display level 0 as idle.
        if row["output_level"] is not None:
            output_text = str(row["output_level"])

        print(
            f"{row['tick']:>4} | {row['input_level']:>5} | {str(row['high_count']):>10} | "
            f"{event_text:<16} | {row['controller_action']:<18} | {output_text:>6}"
        )
        ticks.append(f"{row['tick']:>4}")
        input_levels.append(f"{row['input_level']:>4}")
        output_levels.append(f"{output_text:>4}")

    print("\ntick:   " + " ".join(ticks))
    print("input:  " + " ".join(input_levels))
    print("output: " + " ".join(output_levels))


def main():
    print("Output idle = None (no pending output); 0 and 1 are output levels.")
    input_levels = [0, 1, 1, 0, 0, 1, 1, 1, 1, 0] + [0] * 8
    trace = run_simulation(input_levels)
    print_trace("Two recognized pulses", trace)

    # Each run creates fresh components, so no state carries between examples.
    unknown_input_levels = [0, 1, 1, 1, 0, 0, 0, 0]
    unknown_trace = run_simulation(unknown_input_levels)
    print_trace("Unknown three-tick pulse", unknown_trace)


if __name__ == "__main__":
    main()
