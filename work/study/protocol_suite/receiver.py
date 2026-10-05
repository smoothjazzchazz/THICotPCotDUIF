"""Portable sample-at-a-time receiver and JSON state checkpoint/replay."""
import numpy as np
from .models import Features,Frontend
from .learning import decisions


class Receiver:
    def __init__(self,config,readout):
        self.config,self.readout = config,readout
        self.front = Frontend(config.get("filtered",True))
        self.engine = Features(config)
        self.captured = self.engine.state.copy()

    def step(self,sample):
        tick = self.front.tick
        obs = self.front.step(int(sample))
        self.engine.step(obs)
        if self.config.get("latch") and obs[0]==0 and obs[1]:
            self.captured = self.engine.state.copy()
        if not obs[5]:
            return None
        if self.config.get("latch"):
            live = self.engine.state
            self.engine.state = self.captured
            x = self.engine.vector()
            self.engine.state = live
        else:
            x = self.engine.vector()
        record = {"x":np.asarray([x]),"ticks":[tick],"stamps":[obs[6]],
                  "support":np.asarray([[self.engine.run_count,self.engine.run_min,self.engine.run_max]])}
        return decisions([record],self.readout,scalar=True)[0][0]

    def snapshot(self):
        return {"schema":1,"config":self.config,"readout":self.readout,
                "frontend":dict(vars(self.front)),"state":self.engine.state.tolist(),
                "support":[self.engine.run_count,self.engine.run_min,self.engine.run_max],
                "captured":self.captured.tolist()}

    @classmethod
    def restore(cls,snapshot):
        if snapshot["schema"]!=1:
            raise ValueError("unsupported schema")
        r = cls(snapshot["config"],snapshot["readout"])
        r.front.__dict__.update(snapshot["frontend"])
        r.engine.state = np.asarray(snapshot["state"],np.int64)
        r.engine.run_count,r.engine.run_min,r.engine.run_max = snapshot["support"]
        r.captured = np.asarray(snapshot["captured"],np.int64)
        return r
