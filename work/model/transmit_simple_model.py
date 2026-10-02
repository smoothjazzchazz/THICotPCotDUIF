TX_TABLE = {0:[0,0], 1:[0,1], 2:[1,0], 3:[1,1]}

class Transmitter:
    def __init__(self, symbols):
        self.symbols = list(symbols)
        self.symbol_index = 0
        self.position = 0

    def step(self):

        if self.symbol_index >= len(self.symbols):
            return None

        symbol_id = self.symbols[self.symbol_index]
        pattern = TX_TABLE[symbol_id]
        level = pattern[self.position]

        self.position += 1

        if self.position == len(pattern):
            self.position = 0
            self.symbol_index += 1

        return level