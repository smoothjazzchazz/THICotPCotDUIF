"""A configurable event-to-response mapping, with no processor emulation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResponseRequest:
    symbol_id: int
    requested_tick: int


class MappingController:
    def __init__(self, class_to_transmit_symbol):
        self.class_to_transmit_symbol = dict(class_to_transmit_symbol)
        self.reset()

    def reset(self):
        self.last_event = None
        self.last_request = None

    def step(self, event, tick):
        self.last_event = event
        self.last_request = None
        if event is None or event.class_id is None:
            return None
        symbol_id = self.class_to_transmit_symbol.get(event.class_id)
        if symbol_id is not None:
            self.last_request = ResponseRequest(symbol_id, tick)
        return self.last_request
