"""Causal integer front end and fixed feature engines; only readouts are fitted.

The delay-polynomial mechanism adapts work/study/polynomial_memory/reservoir.py.
All code here is suite-local. No external runner or output helper is invoked.
"""
import numpy as np


class Frontend:
    def __init__(self, filtered=True, quiet=10):
        self.filtered, self.quiet = filtered, quiet
        self.pipe = [0, 0]
        self.prev = self.age = self.tick = 0
        self.armed = False

    def step(self, raw):
        a, b = self.pipe
        level = ((a & b) | (a & raw) | (b & raw)) if self.filtered else raw
        self.pipe = [b, raw]
        changed = level != self.prev
        token = (self.prev, min(31, self.age)) if changed and self.age else None
        start = changed and self.prev == 0 and self.age >= self.quiet
        if changed:
            self.age = 1
        else:
            self.age = min(255, self.age+1)
        if level:
            self.armed = True
        gate = self.armed and level == 0 and self.age == self.quiet
        stamp = (self.tick - self.age + 1) & 65535
        if gate:
            self.armed = False
        edge = level ^ self.prev
        self.prev = level
        self.tick = (self.tick+1) & 65535
        return level, edge, self.age, token, start, gate, stamp


class Features:
    def __init__(self, config):
        self.config = dict(config)
        self.kind = config["kind"]
        self.n = config.get("n", 16)
        self.seed = config.get("seed", 11)
        self.run_count, self.run_min, self.run_max = 0, 31, 0
        rng = np.random.default_rng(self.seed)
        self.binary_runs = config.get("duration_code") == "threshold"
        if self.kind in ("sample", "run"):
            columns = 2 if self.kind == "sample" else (2+len(config["thresholds"]) if self.binary_runs else 3)
            self.state = np.zeros((self.n, columns), np.int64)
            d = self.state[::config.get("stride",1)].size
            allpairs = list(zip(*np.triu_indices(d, 1)))
            if config.get("degree", 1) == 1:
                allpairs = []
            elif self.kind == "run" and config.get("expansion") in ("block","block_all"):
                allpairs = [(i,j) for i,j in allpairs if
                            (i%columns == j%columns and (i%columns<3 or config.get("expansion")=="block_all")) or i//columns == j//columns]
            self.pairs = np.asarray(allpairs, dtype=int).reshape(-1, 2)
        else:
            self.state = np.zeros(self.n, np.int64)
        if self.kind == "recurrent":
            groups = config.get("groups", 1)
            size = self.n//groups
            self.taps = np.asarray([[i//size*size+int(j) for j in rng.choice(size,3,replace=False)]
                                    for i in range(self.n)])
            self.signs = rng.choice([-1,1], size=(self.n,3))
            self.input_taps = rng.integers(0,6,size=(self.n,2))
            self.input_signs = rng.choice([-1,1],size=(self.n,2))
            leaks = config.get("leaks", [1])
            self.leaks = np.resize(leaks,self.n)
            if groups > 1:
                self.leaks = np.repeat(leaks[:groups], size)
        if self.kind == "boolean":
            self.sites = np.array([0,self.n//4,self.n//2,3*self.n//4])

    def step(self, observation):
        level, edge, age, token, start, gate, stamp = observation
        if self.kind == "sample":
            self.state[1:] = self.state[:-1]
            self.state[0] = [2*(level&1)-1, 2*((level>>1)&1)-1]
        elif self.kind == "run":
            if start:
                # Reset is triggered ONLY by observed long idle -> activity.
                # It is a parser boundary, never a supplied generator boundary.
                self.state[:] = 0
                self.run_count, self.run_min, self.run_max = 0, 31, 0
            elif token is not None:
                v, length = token
                self.run_count = min(255,self.run_count+1)
                self.run_min, self.run_max = min(self.run_min,length),max(self.run_max,length)
                self.state[1:] = self.state[:-1]
                if self.binary_runs:
                    self.state[0] = [2*(v&1)-1,2*((v>>1)&1)-1,
                                     *[2*int(length>t)-1 for t in self.config["thresholds"]]]
                else:
                    self.state[0] = [4*(2*(v&1)-1), 4*(2*((v>>1)&1)-1), length-4]
        elif self.kind == "recurrent":
            x = np.array([4*(2*(level&1)-1), 4*(2*((level>>1)&1)-1),
                          4*(edge&1), 4*((edge>>1)&1), min(15,age)-4, 4*(level==0)])
            recur = np.sum(self.state[self.taps]*self.signs,axis=1) >> 2
            drive = recur + self.config.get("gain", 2)*np.sum(x[self.input_taps]*self.input_signs,axis=1)
            target = np.clip(drive,-31,31)
            self.state += (target-self.state) >> self.leaks
        elif self.kind == "boolean":
            left, center, right = np.roll(self.state,1), self.state, np.roll(self.state,-1)
            index = 4*left+2*center+right
            self.state = (self.config.get("rule",90) >> index) & 1
            self.state[self.sites] = [level&1,(level>>1)&1,edge&1,(edge>>1)&1]
        else:
            raise ValueError(self.kind)

    def vector(self):
        x = self.state[::self.config.get("stride",1)].ravel()
        if self.kind == "run":
            if self.binary_runs:
                return np.concatenate([x,x[self.pairs[:,0]]*x[self.pairs[:,1]]]) if len(self.pairs) else x.copy()
            a = [x*4]
            if len(self.pairs):
                a.extend([x[self.pairs[:,0]]*x[self.pairs[:,1]], self.state[:,2]**2])
            return np.concatenate(a)
        if self.kind == "sample" and len(self.pairs):
            return np.concatenate([x,x[self.pairs[:,0]]*x[self.pairs[:,1]]])
        if self.kind == "boolean":
            return 2*x-1
        return x.copy()

    @property
    def unit(self):
        return 1 if self.binary_runs else {"run":16,"recurrent":32}.get(self.kind,1)


def collect(streams, config):
    records = []
    for stream in streams:
        front = Frontend(config.get("filtered", True))
        engine = Features(config)
        ticks, stamps, rows, support = [], [], [], []
        captured_state = engine.state.copy()
        for tick, sample in enumerate(stream["samples"]):
            obs = front.step(sample)
            engine.step(obs)
            if config.get("latch") and obs[0]==0 and obs[1]:
                captured_state = engine.state.copy()
            if obs[5]:
                ticks.append(tick)
                stamps.append(obs[6])
                if config.get("latch"):
                    live_state = engine.state
                    engine.state = captured_state
                    rows.append(engine.vector())
                    engine.state = live_state
                else:
                    rows.append(engine.vector())
                support.append([engine.run_count,engine.run_min,engine.run_max])
        width = len(engine.vector())
        records.append({"ticks":np.asarray(ticks), "stamps":np.asarray(stamps),
                        "x":np.asarray(rows, np.int64).reshape(-1,width),
                        "support":np.asarray(support,np.int64).reshape(-1,3)})
    return records


def configurations():
    return [
        {"name":"instant", "kind":"sample","n":1,"degree":1},
        {"name":"sample20_linear", "kind":"sample","n":20,"degree":1},
        {"name":"sample20_poly", "kind":"sample","n":20,"degree":2},
        {"name":"sample48_linear", "kind":"sample","n":48,"degree":1},
        {"name":"recurrent32", "kind":"recurrent","n":32,"leaks":[1]},
        {"name":"recurrent32_multiscale", "kind":"recurrent","n":32,"leaks":[1,2,3,4]},
        {"name":"recurrent32_modular", "kind":"recurrent","n":32,"leaks":[1,3],"groups":2},
        {"name":"boolean64_r90", "kind":"boolean","n":64,"rule":90},
        {"name":"boolean64_r30", "kind":"boolean","n":64,"rule":30},
        {"name":"run16_linear", "kind":"run","n":16,"degree":1},
        {"name":"run16_block", "kind":"run","n":16,"degree":2,"expansion":"block"},
        {"name":"run16_full", "kind":"run","n":16,"degree":2,"expansion":"full"},
        {"name":"template32", "kind":"run","n":16,"degree":1,"template":32},
    ]
