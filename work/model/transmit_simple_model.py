"""One sampled lane of configurable pattern playback, with an unbounded queue."""

TX_TABLE = {0: [0, 0], 1: [0, 1], 2: [1, 0], 3: [1, 1]}


class Transmitter:
    def __init__(self, symbols=(), patterns=None):
        patterns = TX_TABLE if patterns is None else patterns
        self.patterns = {symbol: tuple(levels) for symbol, levels in patterns.items()}
        for levels in self.patterns.values():
            if not levels or any(level not in (0, 1) for level in levels):
                raise ValueError("patterns must contain one or more binary levels")
        self.initial_symbols = tuple(symbols)
        if any(symbol not in self.patterns for symbol in self.initial_symbols):
            raise ValueError("Unknown Symbol")
        self.reset()

    def reset(self):
        # Reset replays the constructor's initial requests, not later send() calls.
        self.symbols = list(self.initial_symbols)
        # Completed requests stay in the list; this index skips past them.
        self.symbol_index = 0
        self.position = 0

    def send(self, symbol_id):
        if symbol_id not in self.patterns:
            raise ValueError("Unknown Symbol")

        self.symbols.append(symbol_id)

    def step(self):
        if self.symbol_index >= len(self.symbols):
            return None

        symbol_id = self.symbols[self.symbol_index]
        pattern = self.patterns[symbol_id]
        level = pattern[self.position]

        self.position += 1

        if self.position == len(pattern):
            self.position = 0
            self.symbol_index += 1

        return level


class ScheduledLineTransmitter:
    """Finite, deterministic multi-line drive scheduler for interactive models.

    A command changes one lane's level and output-enable. It cannot take effect
    until the tick after the controller requested it. Released lines resolve in
    the environment, rather than pretending that software idle is a voltage.
    """

    def __init__(self, lanes=2, capacity=512):
        import heapq
        self.heapq = heapq
        self.capacity = capacity
        self.commands = []
        self.levels = [1] * lanes
        self.enables = [False] * lanes
        self.sequence = 0
        self.overflow = 0
        self.applied = []  # Diagnostic log, never read to make a decision.

    def schedule(self, lane, level, enable, due, requested):
        if due <= requested:
            raise ValueError("a response must start after its request")
        if not 0 <= lane < len(self.levels) or level not in (0, 1):
            raise ValueError("invalid line command")
        if len(self.commands) >= self.capacity:
            self.overflow += 1
            return False
        self.sequence += 1
        self.heapq.heappush(self.commands, (due, self.sequence, lane, level, bool(enable), requested))
        return True

    def step(self, tick):
        while self.commands and self.commands[0][0] <= tick:
            due, _, lane, level, enable, requested = self.heapq.heappop(self.commands)
            self.levels[lane], self.enables[lane] = level, enable
            self.applied.append((tick, lane, level, enable, requested))
        return tuple(self.levels), tuple(self.enables)
