"""Numerical and waveform-path checks for the reduced recurrent dimension."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from .receiver import MASK, NODES, LEAKS, StreamReceiver, initial_weights, features
from .bptt import loss_gradient
from .training import dev_predictions, adam_step, restore_optimizer, save_optimizer
from work.study.protocol_reservoir64.training import batch
from work.study.protocol_reservoir64_training30.data import transaction
from work.study.protocol_reservoir64_training30.simulation import run_i2c
from work.study.protocol_reservoir64_training30.metrics import score_case
from work.study.protocol_reservoir64.test_experiment import EdgeReference


class I2C32Tests(unittest.TestCase):
    def test_sparse_shape_and_causality(self):
        self.assertEqual(NODES,32);self.assertEqual(int(MASK.sum()),128)
        np.testing.assert_array_equal(MASK.sum(axis=1),np.full(32,4))
        np.testing.assert_array_equal(LEAKS,np.tile([1,.5,.25,.125],8))
        prefix=[(1,1)]*12+[(1,0)]*10+[(0,1)]*8
        for mode in ('float','quantized'):
            all_records=[]
            for suffix in ([(0,0)]*5,[(1,1)]*5):
                rx=StreamReceiver(initial_weights(11),mode);record=[]
                for t,line in enumerate(prefix+suffix):
                    event=rx.step(line,t)
                    if t<len(prefix):record.append((event,rx.state.copy()))
                all_records.append(record)
            for a,b in zip(*all_records):
                self.assertEqual(a[0],b[0]);np.testing.assert_array_equal(a[1],b[1])

    def test_512_tick_gradients_and_state_continuity(self):
        rng=np.random.default_rng(551)
        x=rng.normal(0,.4,(512,2,6));y=rng.integers(0,8,(512,2))
        valid=np.ones(y.shape);h=rng.normal(0,.1,(2,32));w=initial_weights(11)
        weights=np.array([1,12,12,48,48,5,48,12.])
        _,end,g=loss_gradient(w,x,y,valid,h,weights)
        tap=tuple(map(int,np.argwhere(MASK)[93]))
        for key,index in [('wx',(7,2)),('wh',tap),('wo',(4,7)),('b',(3,)),('bo',(4,))]:
            original=w[key][index];eps=1e-5
            w[key][index]=original+eps;plus=loss_gradient(w,x,y,valid,h,weights,False)[0]
            w[key][index]=original-eps;minus=loss_gradient(w,x,y,valid,h,weights,False)[0]
            w[key][index]=original
            self.assertAlmostEqual(g[key][index],(plus-minus)/(2*eps),places=7)
        carry=h.copy()
        for t in range(0,512,128):
            _,carry,_=loss_gradient(w,x[t:t+128],y[t:t+128],valid[t:t+128],carry,weights,False)
        np.testing.assert_array_equal(carry,end)
        self.assertEqual(np.count_nonzero(g['wh']*(1-MASK)),0)

    def test_batch_decisions_match_online(self):
        streams=[transaction('i2c',8100000+i,i) for i in range(2)]
        w=initial_weights(47);_,kinds=dev_predictions(w,batch(streams),np.ones(8))
        for i,s in enumerate(streams):
            rx=StreamReceiver(w)
            for t,line in enumerate(s['lines']):
                rx.step(line,t);self.assertEqual(rx.last_class,int(kinds[t,i]))

    def test_integer_step_against_scalar_arithmetic(self):
        # A scalar MAC/rounding oracle exercises the actual 32-node implementation.
        w=initial_weights(29);rx=StreamReceiver(w,'quantized')
        rng=np.random.default_rng(730);state=[0]*32
        from work.model.stream_reservoir import LineFeatures
        encoder=LineFeatures()
        for t,line in enumerate(rng.integers(0,2,(512,2))):
            x=list(map(int,encoder.step(line,True)));q=rx.q
            proposal=[]
            for i in range(32):
                drive=sum(int(q['wx'][i,j])*x[j] for j in range(6))+(int(q['b'][i])<<14)
                drive+=sum(int(q['wh'][i,j])*state[j] for j in range(32))
                index=max(-2048,min(2048,(drive+(1<<17))>>18))+2048
                proposal.append(int(rx.lut[index]))
            state=[max(-16384,min(16384,((32768-int(rx.leaks[i]))*state[i]+int(rx.leaks[i])*proposal[i]+(1<<14))>>15)) for i in range(32)]
            logits=[sum(int(q['wo'][k,i])*state[i] for i in range(32))+(int(q['bo'][k])<<14) for k in range(8)]
            rx.step(line,t)
            np.testing.assert_array_equal(rx.state,state);np.testing.assert_array_equal(rx.logits,logits)

    def test_optimizer_resume_exact(self):
        w=initial_weights(11);m,v=({k:np.zeros_like(a) for k,a in w.items()} for _ in range(2))
        grad={k:np.ones_like(a)*.001 for k,a in w.items()};grad['wh']*=MASK
        adam_step(w,grad,m,v,1)
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'state.npz';save_optimizer(file,w,m,v,np.zeros((12,32)),1,1)
            w2,m2,v2,meta=restore_optimizer(file)
            self.assertEqual(meta['next_epoch'],2)
            adam_step(w,grad,m,v,2);adam_step(w2,grad,m2,v2,2)
            for a,b in ((w,w2),(m,m2),(v,v2)):
                for k in a:np.testing.assert_array_equal(a[k],b[k])

    def test_live_i2c_reference_and_deadlines(self):
        for low,high in ((8,8),(12,12),(8,12),(12,8)):
            case=dict(name='test',payload=bytes(range(16)),seed=8290000,low=low,high=high,valid=True)
            metrics,result=score_case('i2c',case,EdgeReference(delay=2))
            self.assertTrue(metrics['passes']);self.assertEqual(metrics['bytes']['recovered'],16)
            self.assertEqual(metrics['response_latency']['maximum'],3)
            self.assertTrue(result['peer'].stretches)


if __name__=='__main__':unittest.main()
