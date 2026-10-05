"""Discrete nonlinear scalar with delayed feedback; buffer costs are explicit."""
import numpy as np


class DelayFeedback:
    def __init__(self, config):
        self.config = config
        self.state = np.zeros(config['nodes'])

    def step(self, level):
        c = self.config
        drive = c.get('gain', 1.0) * (2 * level - 1)
        feedback = c.get('coupling', .6) * self.state[-1]
        leak = c.get('leak', .5)
        nonlinear = np.sin(drive + feedback) if c.get('nonlinearity') == 'sin' else np.tanh(drive + feedback)
        value = (1 - leak) * self.state[0] + leak * nonlinear
        self.state[1:] = self.state[:-1]
        self.state[0] = value
        if c.get('bits'):
            scale = 2 ** (c['bits'] - 1) - 1
            self.state = np.round(self.state * scale) / scale
        return self.state.copy()
