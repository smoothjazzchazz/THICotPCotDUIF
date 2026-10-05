"""Finite input memory with a fixed polynomial expansion (NGRC convention)."""
import numpy as np
from work.model.reservoir_model import FeatureExtractor


class PolynomialMemory:
    def __init__(self, config):
        self.config = config
        self.n = config['nodes']
        self.state = np.zeros(self.n, dtype=float if config.get('input') == 'age' else np.int64)
        self.features = FeatureExtractor() if config.get('input') == 'age' else None
        self.pairs = np.triu_indices(self.n, 1)

    def step(self, level):
        if level not in (0, 1):
            raise ValueError('Input samples must be 0 or 1')
        self.state[1:] = self.state[:-1]
        if self.features is not None:
            f = self.features.step(level)
            self.state[0] = (f[0] - f[2]) / 8
        else:
            self.state[0] = 2 * level - 1
        if self.config.get('degree', 2) == 1:
            return self.state.copy()
        a, b = self.pairs
        return np.concatenate([self.state, self.state[a] * self.state[b]])
