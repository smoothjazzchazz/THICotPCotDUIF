"""Contracts that can invalidate the experiment independent of learned accuracy."""
import unittest
import tempfile
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import StreamReceiver, features, initial_weights, MASK, LEAKS
from work.study.protocol_reservoir64.training import batch, loss_gradient
from work.study.protocol_reservoir64_training30.test_training import TrainingTests as InheritedTests
from .training import dev_predictions
from .investigation import initialize
from .uart_scoring import uart_case
from .data import cases

class Tests(unittest.TestCase):
    def test_training_online_and_chunk_continuity(self):
        from .data import transaction
        for profile in ('uart_n','uart_e'):
            s=transaction(profile,19000001,5)
            for recipe in ('previous','memory095','memory105'):
                w=initialize(11,recipe); x,y,v=batch([s]); rx=StreamReceiver(w)
                _,kinds=dev_predictions(w,(x,y,v),np.ones(8))
                state=np.zeros((1,64))
                for start in range(0,len(x),512):
                    stop=min(start+512,len(x))
                    _,state,_=loss_gradient(w,x[start:stop],y[start:stop],v[start:stop],state,np.ones(8),False)
                    for t in range(start,stop):
                        rx.step(s['lines'][t],t)
                        self.assertEqual(rx.last_class,kinds[t,0])
                    np.testing.assert_allclose(state[0],rx.state,atol=2e-14,rtol=0)

    def test_mask_and_repeated_identical_bits(self):
        from work.study.protocol_reservoir64.uart_emitter import generate
        for recipe in ('previous','memory095','memory105'):
            for seed in (11,29,47,71,101,131):
                w=initialize(seed,recipe)
                self.assertEqual(np.count_nonzero(MASK),256)
                self.assertFalse(np.any(w['wh']*(1-MASK)))
        for parity in (False,True):
            s=generate(b'\x00\xff'*3,19100001,parity=parity)
            for f in s['frames']:
                ticks=np.flatnonzero(s['labels'][f['start']:f['end']+1])+f['start']
                self.assertEqual(len(ticks),10+parity)
                self.assertTrue(np.all(np.diff(ticks[1:9])==16))
                self.assertTrue(np.all(s['labels'][ticks[1:9]]== (1 if f['value']==0 else 2)))
                self.assertTrue(np.all(s['labels'][ticks[1:9]+1]==0))

    def test_timing_controls_applied_without_final_data(self):
        for profile in ('uart_n','uart_e'):
            for c in cases(profile,'dev'):
                s=uart_case(c,c['seed']-90001,profile=='uart_e')
                # Independent replay of cell durations with actual seeded rounding.
                rng=np.random.default_rng(c['seed']); elapsed=12.+rng.random(); cursor=12
                if c.get('disturbance') or c.get('malformed'): continue
                gaps=[]; durations=[]
                for i,f in enumerate(s['frames']):
                    self.assertEqual(f['start'],cursor)
                    for cell in range(11 if profile=='uart_e' else 10):
                        elapsed+=16*c.get('ratio',1.)+(int(rng.integers(-1,2)) if c.get('jitter') else 0)
                        end=round(elapsed);durations.append(end-cursor);cursor=end
                    self.assertEqual(f['end'],cursor-1)
                    if c.get('gaps'):
                        gap=int(rng.integers(0,3))*16; gaps.append(gap);cursor+=gap;elapsed+=gap
                if c.get('jitter'): self.assertGreater(len(set(durations)),1)
                if c.get('gaps'): self.assertGreater(max(gaps),0)

if __name__=='__main__': unittest.main()
