"""Online elementary cellular automaton: simultaneous local updates + input."""
import numpy as np


class BooleanCA:
    def __init__(self, config):
        self.config = config
        self.state = np.zeros(config['nodes'], dtype=np.int64)
        rng = np.random.default_rng(config.get('seed', 31))
        self.sites = rng.choice(len(self.state), config.get('inputs', 1), replace=False)

    def step(self, level):
        left = np.roll(self.state, 1)
        right = np.roll(self.state, -1)
        if self.config.get('structure', 'ring') == 'chain':
            # One-way local logic, so arbitrary initialization flushes in N ticks.
            right = np.roll(self.state, 2)
            left[0] = level
            right[:2] = level
        code = 4 * left + 2 * self.state + right
        self.state = (self.config.get('rule', 90) >> code) & 1
        self.state[self.sites] = level
        return 2.0 * self.state - 1
