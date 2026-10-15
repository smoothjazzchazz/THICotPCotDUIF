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
