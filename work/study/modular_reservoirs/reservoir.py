"""Matched-total-storage dynamical controls; fixed weights, fitted readout only."""
import numpy as np
from work.model.reservoir_model import FeatureExtractor


class ModularReservoir:
    def __init__(self, config):
        self.config = config
        n = config['nodes']
        self.state = np.zeros(n)
        self.features = FeatureExtractor()
        rng = np.random.default_rng(config.get('seed', 31))
        mode, structure = config.get('mode', 'single'), config.get('structure', 'sparse')
        groups = 1 if mode == 'single' else 2
        size = n // groups
        self.weights = np.zeros((n, n))
        for i in range(n):
            start = i // size * size
            if structure == 'sparse':
                taps = rng.choice(np.arange(start, start + size), 3, replace=False)
            elif structure == 'ring':
                taps = [start + (i - start - 1) % size]
            elif structure == 'local':
                taps = [start + (i - start + d) % size for d in (-1, 0, 1)]
            else:
                taps = [max(start, i - d) for d in (1, 2, 4)]
            for j in taps:
                self.weights[i, j] += rng.choice([-1., 1.])
        self.weights *= config.get('coupling', .8) / np.maximum(1, np.abs(self.weights).sum(axis=1))[:, None]
        self.inputs = rng.uniform(-1, 1, (n, 3))
        if mode == 'stacked':
            self.inputs[size:] = 0
            self.weights[size:, :size] += np.eye(size) * .3
        elif mode == 'coupled':
            self.weights[:size, size:] += np.eye(size) * .1
            self.weights[size:, :size] += np.eye(size) * .1
        elif mode == 'specialized':
            self.inputs[:size, 1:] = 0
            self.inputs[size:, 0] = 0
        self.leak = np.full(n, config.get('leak', .5))
        if groups == 2:
            self.leak[size:] = config.get('slow_leak', .2)

    def step(self, level):
        f = np.asarray(self.features.step(level)) / [1, 1, 7]
        drive = self.weights @ self.state + self.inputs @ f
        y = np.clip(drive, -1, 1) if self.config.get('nonlinearity') == 'clip' else np.tanh(drive)
        self.state = (1 - self.leak) * self.state + self.leak * y
        if self.config.get('bits'):
            scale = 2 ** (self.config['bits'] - 1) - 1
            self.state = np.round(self.state * scale) / scale
        return self.state.copy()
