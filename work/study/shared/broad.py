"""Shared causal state collection and four-class readout for new experiments.

Historical evaluation and event matching remain in comparison.py, unchanged.
"""
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
import numpy as np
from work.model.reservoir_model import DecisionRule, FeatureExtractor, IntegerReservoir, ReservoirConfig, Stabilizer
from work.study.shared.comparison import choose_classes, measure
from work.study.shared.signals import CLASS_IDS, WARMUP_TICKS, make_stream
from work.study.polynomial_memory.reservoir import PolynomialMemory
from work.study.boolean_ca.reservoir import BooleanCA
from work.study.delay_feedback.reservoir import DelayFeedback
from work.study.modular_reservoirs.reservoir import ModularReservoir

CONDITIONS = {'clean': (0, 0), 'jitter': (2, 0), 'glitches': (0, .02), 'mixed': (2, .02)}
ROOT = Path('work/study')


def save(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sources():
    paths = list(ROOT.rglob('*.py')) + [ROOT / 'broad_search/PLAN.md', Path('work/model/reservoir_model.py')]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if '.venv' not in p.parts}


def reserve(experiment, purpose, config):
    path = ROOT / 'results' / experiment / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    path.mkdir(parents=True, exist_ok=False)
    save(path / 'manifest.json', {'created_utc': datetime.now(timezone.utc).isoformat(), 'purpose': purpose,
         'config': config, 'source_sha256': sources(), 'git_revision': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
         'numpy_version': np.__version__})
    return path


class Legacy:
    def __init__(self, config):
        self.features = FeatureExtractor()
        self.reservoir = IntegerReservoir(ReservoirConfig(**config['reservoir']))

    @property
    def state(self):
        return np.asarray(self.reservoir.state, float) / 32

    @state.setter
    def state(self, state):
        self.reservoir.state = tuple(np.clip(np.rint(state * 32), -32, 31).astype(int))

    def step(self, level):
        return np.asarray(self.reservoir.step(self.features.step(level))) / 32


def build(config):
    return {'polynomial': PolynomialMemory, 'ca': BooleanCA, 'delay': DelayFeedback,
            'modular': ModularReservoir, 'legacy': Legacy}[config['family']](config)


def collect(streams, config):
    result = []
    for s in streams:
        model = build(config)
        result.append(np.asarray([model.step(u) for u in s.levels]))
    return result


def fit(streams, states, ridge, explicit=True):
    x = np.concatenate([s[WARMUP_TICKS:] for s in states])
    x = np.column_stack([x, np.ones(len(x))])
    y = np.concatenate([s.targets[WARMUP_TICKS:] for s in streams])
    ids = CLASS_IDS if explicit else CLASS_IDS[:3]
    weight = np.zeros(len(y))
    for k in CLASS_IDS:
        weight[y == k] = 1 / np.count_nonzero(y == k)
    target = np.column_stack([y == k for k in ids])
    penalty = np.eye(x.shape[1]) * ridge
    penalty[-1, -1] = 0
    w = np.linalg.solve(x.T @ (weight[:, None] * x) + penalty, x.T @ (weight[:, None] * target))
    return {'weights': w[:-1].tolist(), 'bias': w[-1].tolist(), 'class_ids': list(ids), 'ridge': ridge}


def scores(states, readout):
    return [x @ np.asarray(readout['weights']) + readout['bias'] for x in states]


def predict(states, readout):
    rule = DecisionRule(readout['floor'], readout['margin'])
    return [choose_classes(x, readout['class_ids'], rule) for x in scores(states, readout)]


def quantize(readout, bits):
    """Power-of-two coefficient scaling; no retraining or threshold retuning."""
    maximum = max(np.max(np.abs(readout['weights'])), np.max(np.abs(readout['bias'])))
    scale = 2. ** np.floor(np.log2((2 ** (bits - 1) - 1) / maximum))
    return {**readout, 'weights': np.rint(np.asarray(readout['weights']) * scale).astype(int).tolist(),
            'bias': np.rint(np.asarray(readout['bias']) * scale).astype(int).tolist(),
            'floor': int(np.ceil(readout['floor'] * scale)),
            'margin': int(np.ceil(readout['margin'] * scale)),
            'coefficient_scale': scale, 'coefficient_bits': bits}


def select(train, ts, validation, vs, explicit=True):
    best, key = None, None
    for ridge in (.0001, .01, .1, 1.):
        r = fit(train, ts, ridge, explicit)
        sc = scores(vs, r)
        for floor in (0, .2, .4, .6):
            for margin in (0, .1, .2):
                pred = [choose_classes(x, r['class_ids'], DecisionRule(floor, margin)) for x in sc]
                for hold in (1, 2, 3):
                    m, _ = measure(validation, pred, hold)
                    ratios = [m[k] / .8 for k in ('event_precision', 'event_recall', 'unknown_recall')]
                    rank = (min(1., min(ratios)), m['event_f1'], m['balanced_accuracy'], -m['false_events_per_1000_ticks'])
                    if key is None or rank > key:
                        best = {**r, 'floor': floor, 'margin': margin, 'hold': hold, 'validation': m}
                        key = rank
    return best


def metrics(streams, states, readout):
    return measure(streams, predict(states, readout), readout['hold'])[0]


def development(base=31000000, count=6, patterns=24):
    return {k: [make_stream(base + 10000 * i + j, patterns, *c) for j in range(count)]
            for i, (k, c) in enumerate(CONDITIONS.items())}


def probe(config, readout):
    from work.study.mixed_leaks.mixed_leaks import memory_probe_streams, probe_readout_diagnostics
    probes = memory_probe_streams()
    streams = [p['stream'] for p in probes]
    xs = collect(streams, config)
    decisions = probe_readout_diagnostics(probes, {'candidate': {'predictions': predict(xs, readout)}})['candidate']
    grouped = {}
    for p, x in zip(probes, xs):
        start = p['stream'].windows[-1]['start']
        grouped.setdefault(tuple(p['pair']), []).append(x[start:start + 4])
    memory = []
    for known, unknown in (((3,8),(8,8)), ((8,3),(3,3))):
        a,b = np.asarray(grouped[known]), np.asarray(grouped[unknown])
        cross = np.abs(a[:,None] - b[None,:]).sum(axis=-1)
        within = np.abs(a[:,None] - a[None,:]).sum(axis=-1)
        memory.append({'known':known, 'unknown':unknown, 'cross_min':cross.min(axis=(0,1)).tolist(),
                       'prefix_diameter':within.max(axis=(0,1)).tolist()})
    initial = []
    for levels in ([0]*128,[1]*128,make_stream(2300000).levels[:128]):
        a,b = build(config), build(config)
        a.state = np.full_like(a.state, -1 if config['family'] != 'ca' else 0)
        b.state = np.full_like(b.state, 1)
        gaps=[]
        for u in levels:
            a.step(u); b.step(u)
            gaps.append(float(np.max(np.abs(a.state-b.state))))
        initial.append(max(gaps[-16:]))
    return {'decisions':decisions, 'memory':memory, 'initial_tail_gaps':initial,
            'eligible': decisions['all_reset_ticks_correct'] and decisions['minimum_continuous_recall'] >= .9
            and all(min(m['cross_min']) > 1e-12 for m in memory) and max(initial) <= 1/32}


def training_diagnostics(config, states):
    x = np.concatenate([s[WARMUP_TICKS:] for s in states])
    result = {'distinct_states': len(np.unique(x, axis=0)),
              'varying_sign_bits': int(np.count_nonzero(np.ptp((x > 0).astype(int), axis=0)))}
    if config['family'] in ('ca', 'polynomial'):
        result['clipped_fraction'] = None
        result['clipping_applicability'] = 'Boolean/delay samples have no saturating arithmetic'
    else:
        result['clipped_fraction'] = float(np.mean(np.abs(x) >= 1))
    result['eligible'] = result['distinct_states'] >= 2 and (result['clipped_fraction'] or 0) <= .5
    return result


class Receiver:
    def __init__(self, config, readout):
        self.config, self.readout = config, readout
        self.model = build(config)
        self.stabilizer = Stabilizer(readout['hold'])
        self.rule = DecisionRule(readout['floor'], readout['margin'])
        self.tick = 0

    def step(self, level):
        self.state = self.model.step(level)
        # Scalar accumulation is independent of the cached batch matrix path.
        w = self.readout['weights']
        convert = int if 'coefficient_bits' in self.readout else float
        self.scores = [bias + sum(convert(x) * row[j] for x,row in zip(self.state,w))
                       for j,bias in enumerate(self.readout['bias'])]
        self.prediction = self.rule.choose(self.scores, self.readout['class_ids'])
        event = self.stabilizer.step(self.prediction, self.tick)
        self.tick += 1
        return event

    def snapshot(self):
        features = getattr(self.model, 'features', None)
        return {'schema': 1, 'config': self.config, 'readout': self.readout,
                'tick': self.tick, 'state': self.model.state.tolist(),
                'features': vars(features).copy() if features is not None else None,
                'stabilizer': vars(self.stabilizer).copy()}

    @classmethod
    def restore(cls, data):
        if data['schema'] != 1:
            raise ValueError('Unsupported snapshot schema')
        receiver = cls(data['config'], data['readout'])
        receiver.model.state = np.asarray(data['state'], dtype=receiver.model.state.dtype)
        if data['features'] is not None:
            receiver.model.features.__dict__.update(data['features'])
        receiver.stabilizer.__dict__.update(data['stabilizer'])
        receiver.tick = data['tick']
        return receiver
