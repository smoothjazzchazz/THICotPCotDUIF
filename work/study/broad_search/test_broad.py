import json
import unittest
import numpy as np
from work.study.shared.broad import build, collect, Receiver, fit, predict, quantize
from work.study.shared.comparison import emit_events
from work.study.shared.resources import resources
from work.study.shared.signals import make_stream


class BroadTests(unittest.TestCase):
    def test_polynomial_delay_and_products(self):
        model=build({'family':'polynomial','nodes':3,'degree':2})
        np.testing.assert_array_equal(model.step(1), [1,0,0,0,0,0])
        np.testing.assert_array_equal(model.step(0), [-1,1,0,-1,0,0])
        np.testing.assert_array_equal(model.step(1), [1,-1,1,-1,1,-1])

    def test_delay_flush_and_causal_future(self):
        config={'family':'polynomial','nodes':32,'degree':2}
        a,b=build(config),build(config)
        a.state[:]=1; b.state[:]=-1
        for u in ([1,0,0,1]*8):
            xa,xb=a.step(u),b.step(u)
        np.testing.assert_array_equal(xa,xb)
        s=make_stream(88)
        altered=make_stream(88); altered.levels[100:]=[1-x for x in altered.levels[100:]]
        x,y=collect([s,altered],config)
        np.testing.assert_array_equal(x[:100],y[:100])

    def test_ca_simultaneous_rule90(self):
        m=build({'family':'ca','nodes':4,'rule':90,'inputs':1,'seed':31})
        m.state=np.array([1,0,0,0])
        m.sites=np.array([0])
        # Rule 90 is left XOR right, from the entire previous state.
        np.testing.assert_array_equal(m.step(0),[-1,1,-1,1])

    def test_feedback_reads_old_tail(self):
        m=build({'family':'delay','nodes':3,'coupling':.5,'gain':0,'leak':1})
        m.state=np.array([.1,.2,.6]); m.step(0)
        np.testing.assert_allclose(m.state,[np.tanh(.3),.1,.2])

    def test_explicit_unknown_and_streaming(self):
        config={'family':'polynomial','nodes':8,'degree':2}
        streams=[make_stream(11),make_stream(12)]
        xs=collect(streams,config)
        readout=fit(streams,xs,.01)
        self.assertEqual(readout['class_ids'],[0,1,2,7])
        readout.update(floor=.2,margin=.1,hold=2)
        expected=predict(xs,readout)
        for s,x,y in zip(streams,xs,expected):
            receiver=Receiver(*json.loads(json.dumps([config,readout])))
            for tick,u in enumerate(s.levels):
                receiver.step(u)
                np.testing.assert_array_equal(receiver.state,x[tick])
                self.assertEqual(receiver.prediction,y[tick])

    def test_integer_readout_and_midstream_restore(self):
        c={'family':'polynomial','nodes':24,'degree':2}
        ss=[make_stream(101),make_stream(102)]
        xs=collect(ss,c)
        r=fit(ss,xs,.01);r.update(floor=.2,margin=.1,hold=3)
        q=quantize(r,8)
        self.assertLessEqual(np.max(np.abs(q['weights'])),127)
        pred=predict(xs,q)[0]
        events=[]; receiver=Receiver(c,q)
        for tick,u in enumerate(ss[0].levels):
            if tick in (1,23,111,217):
                receiver=Receiver.restore(json.loads(json.dumps(receiver.snapshot())))
            event=receiver.step(u)
            self.assertEqual(receiver.prediction,pred[tick])
            self.assertTrue(all(isinstance(s,int) for s in receiver.scores))
            if event:events.append({**event,'emit_tick':tick})
        self.assertEqual(events,emit_events(pred,3))
        accounting=resources(c,q)
        bound=accounting['detail']['max_abs_score_bound']
        self.assertLessEqual(max(abs(x) for x in receiver.scores),bound)
        self.assertEqual(accounting['readout_parameters'],4*(24+276+1))


if __name__=='__main__':unittest.main()
