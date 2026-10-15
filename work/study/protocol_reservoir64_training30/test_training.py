import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from work.model.stream_reservoir import StreamReceiver, initial_weights, features
from work.study.protocol_reservoir64.training import batch, loss_gradient
from work.study.protocol_reservoir64.simulation import run_i2c as original_i2c
from work.study.protocol_reservoir64.test_experiment import EdgeReference
from .simulation import run_i2c
from .data import transaction, cases
from .training import dev_predictions, adam_step, save_optimizer, restore_optimizer
from .audit import gradient_check


class TrainingTests(unittest.TestCase):
    def test_full_window_gradients_and_continuous_state(self):
        gradient_check()

    def test_batched_dev_decisions_match_online_receiver(self):
        streams = [transaction('uart_e', 8000001+i, i) for i in range(2)]
        w = initial_weights(47)
        _, kinds = dev_predictions(w,batch(streams),np.ones(8))
        for i,s in enumerate(streams):
            receiver = StreamReceiver(w)
            for t,line in enumerate(s['lines']):
                receiver.step(line,t)
                self.assertEqual(receiver.last_class,kinds[t,i])

    def test_seeded_peer_preserves_original_path(self):
        for delay in (0,2):
            a = original_i2c(b'\x00\xff\x55\xaa', EdgeReference(delay), jitter=True, malformed=True)
            b = run_i2c(b'\x00\xff\x55\xaa', EdgeReference(delay), jitter=True, malformed=True,peer_seed=90123)
            for key in ('lines','enables','peer_drives'):
                np.testing.assert_array_equal(a[key],b[key])
            self.assertEqual(a['events'],b['events'])
            self.assertEqual(a['peer'].read,b['peer'].read)
            self.assertEqual(a['tx'].applied,b['tx'].applied)

    def test_optimizer_restore_exact_continuation(self):
        w = initial_weights(11)
        m,v = ({k:np.zeros_like(a) for k,a in w.items()} for _ in range(2))
        rng = np.random.default_rng(188)
        grad = {k:rng.normal(0,.001,a.shape) for k,a in w.items()}
        grad['wh'] *= (w['wh'] != 0)
        adam_step(w,grad,m,v,1)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'resume.npz'
            save_optimizer(path,w,m,v,np.ones((12,64)),1,1)
            restored,m2,v2,meta = restore_optimizer(path)
            self.assertEqual(meta['next_epoch'],2)
            adam_step(w,grad,m,v,2); adam_step(restored,grad,m2,v2,2)
            for k in w:
                np.testing.assert_array_equal(w[k],restored[k])
                np.testing.assert_array_equal(m[k],m2[k])
                np.testing.assert_array_equal(v[k],v2[k])

    def test_boundary_and_malformed_label_coverage(self):
        for profile in ('uart_n','uart_e','i2c'):
            counts = np.zeros(8,dtype=int)
            for i in range(18):
                stream = transaction(profile,8100000+i,i)
                counts += np.bincount(stream['labels'],minlength=8)
            self.assertGreater(counts[3],0)
            self.assertGreater(counts[4],0)
            if profile.startswith('uart'): self.assertGreater(counts[6],0)

    def test_full_development_exchange_seeds_disjoint(self):
        seeds = [c['seed'] for p in ('uart_n','uart_e','i2c') for c in cases(p,'dev')]
        self.assertEqual(len(seeds),len(set(seeds)))
        self.assertTrue(all(2000000<=s<3000000 for s in seeds))


if __name__=='__main__': unittest.main()
