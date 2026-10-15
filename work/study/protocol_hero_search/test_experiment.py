"""Meaningful isolation, gradient, timing and assembly checks before fitting."""
import unittest
import numpy as np
from .shapes import VARIANTS,PROFILES,make_shape,initialize,features
from .network import run,Receiver,events,pulses
from .data import Builder,corpus,assemble,score,reference_labels


class Contracts(unittest.TestCase):
    def test_generic_feature_timers_against_scalar(self):
        lines=np.random.default_rng(371).integers(0,2,(1024,3),dtype=np.uint8)
        lines[100:600]=1;previous=np.ones(3);ages=np.full(3,256.);expected=[]
        for row in lines:
            edge=row.astype(float)-previous
            ages=np.where(edge!=0,0,np.minimum(256,ages+1))
            expected.append(np.r_[row.astype(float)*2-1,edge,ages/256]);previous=row.copy()
        np.testing.assert_array_equal(features(lines)[0],expected)
        a,p,h=features(lines[:413]);b,_,_=features(lines[413:],p,h)
        np.testing.assert_array_equal(np.r_[a,b],expected)

    def test_gradients_all_schedules(self):
        rng=np.random.default_rng(13)
        x=rng.normal(size=(19,9));y=rng.integers(0,6,19,dtype=np.int32)
        for variant in VARIANTS:
            sh=make_shape(variant,32);p=initialize(sh,11);h=rng.normal(0,.1,32)
            _,_,_,grad,dh=run(sh,p,x,y,h=h,backward=True)
            for k in rng.choice(len(p),16,replace=False):
                pp=p.copy();pm=p.copy();pp[k]+=1e-5;pm[k]-=1e-5
                fd=(run(sh,pp,x,y,h=h)[0]-run(sh,pm,x,y,h=h)[0])/2e-5
                self.assertAlmostEqual(fd,grad[k],places=6,msg=f'{variant} parameter {k}')
            hp=h.copy();hm=h.copy();hp[3]+=1e-5;hm[3]-=1e-5
            fd=(run(sh,p,x,y,h=hp)[0]-run(sh,p,x,y,h=hm)[0])/2e-5
            self.assertAlmostEqual(fd,dh[3],places=6)

    def test_fixed_masks(self):
        for v in VARIANTS:
            for n in (32,48,64):
                sh=make_shape(v,n)
                self.assertEqual(sh.config(),make_shape(v,n).config())
                self.assertEqual(sum(map(len,sh.groups)),n)
                self.assertTrue(all(s<d for s,d,z in zip(sh.src,sh.dst,sh.delay) if s>=0 and z==0))

    def test_causal_prefix_and_online_chunks(self):
        lines=corpus('uart_n',319,ticks=2048)['lines'];cut=1133
        x=features(lines)[0]
        for v in VARIANTS:
            sh=make_shape(v,32);p=initialize(sh,29)
            _,h,whole,_,_=run(sh,p,x)
            _,ha,a,_,_=run(sh,p,x[:cut]);_,hb,b,_,_=run(sh,p,x[cut:],h=ha)
            np.testing.assert_array_equal(whole,np.r_[a,b]);np.testing.assert_array_equal(h,hb)
            rx=Receiver(sh,p);ea=rx.samples(lines[:cut])+rx.samples(lines[cut:])
            self.assertEqual(ea,events(pulses(whole.argmax(1))))
            changed=lines.copy();changed[cut:]=1-changed[cut:]
            alt=run(sh,p,features(changed)[0])[2]
            np.testing.assert_array_equal(whole[:cut],alt[:cut])

    def test_every_byte_corners_and_oracle_payload(self):
        for profile in PROFILES:
            for condition in (['nominal','minus','plus','jitter','minus_jitter','plus_jitter']
                              if profile.startswith('uart') else ['nominal','duty','pauses','phase']):
                b=Builder(profile,173);b.message(list(range(256)),condition)
                s=b.finish();r=score(s,s['labels'])
                self.assertEqual(r['exact_messages'],1)
                self.assertEqual(r['false_events'],0)

    def test_malformed_recovery_and_repeated_start(self):
        for profile in PROFILES:
            b=Builder(profile,379)
            errors=['framing','break']+(['parity'] if profile=='uart_e' else []) if profile.startswith('uart') else ['partial']
            for invalid in errors:
                b.message([81],invalid=invalid);b.message([0,255,85,170],condition='repeated' if profile=='i2c' else 'nominal')
            s=b.finish();r=score(s,s['labels'])
            self.assertEqual(r['invalid_accepted'],0)
            self.assertEqual(r['exact_messages'],len(errors))

    def test_repeated_bit_occurrences(self):
        e=events(pulses([0,1,1,0,1,0,1]))
        self.assertEqual([a['bit'] for a in e],[0,0,0])
        self.assertEqual([a['decision_tick'] for a in e],[1,4,6])

    def test_readout_only_frozen(self):
        sh=make_shape('parallel_current',48);p=initialize(sh,47)
        x=features(corpus('spi0',1001,ticks=512)['lines'])[0]
        y=np.zeros(len(x),dtype=np.int32)
        grad=run(sh,p,x,y,backward=True,readout_only=True)[3]
        self.assertTrue(np.all(grad[:len(sh.src)+sh.n]==0))
        self.assertGreater(np.linalg.norm(grad[len(sh.src)+sh.n:]),0)

    def test_label_prefix_causality(self):
        for profile in PROFILES:
            s=corpus(profile,101,ticks=4096)
            for cut in (19,300,1171):
                np.testing.assert_array_equal(s['labels'][:cut],reference_labels(s['lines'][:cut],profile))

    def test_integer_replay_against_independent_scalar_math(self):
        def nearest(v,d):return (v+d//2)//d if v>=0 else -((-v+d//2)//d)
        for variant in VARIANTS:
            sh=make_shape(variant,32);p=initialize(sh,131)
            p=np.rint(p*4096)/4096
            lines=np.random.default_rng(21).integers(0,2,(17,3),dtype=np.uint8)
            x=features(lines)[0];w=np.rint(p*4096).astype(np.int64)
            alpha=np.rint(sh.leaks*4096).astype(np.int64)
            lut=np.rint(np.tanh(np.arange(-2048,2049)/256)*4096).astype(np.int64)
            state=np.zeros(sh.n,dtype=np.int64);logits=[];E=len(sh.src);N=sh.n
            for row in x:
                now=np.zeros(N,dtype=np.int64);qx=np.rint(row*4096).astype(np.int64)
                for i in range(N):
                    z=int(w[E+i])*4096
                    for e in np.flatnonzero(sh.dst==i):
                        s=int(sh.src[e]);value=int(qx[-1-s]) if s<0 else int(state[s] if sh.delay[e] else now[s])
                        z+=int(w[e])*value
                    address=max(0,min(4096,nearest(z,65536)+2048))
                    now[i]=nearest(int((4096-alpha[i])*state[i]+alpha[i]*lut[address]),4096)
                out=[(int(w[E+7*N+k])*4096+sum(int(w[E+N+k*N+i])*int(now[i]) for i in range(N)))/16777216 for k in range(6)]
                logits.append(out);state=now
            _,h,actual,_,_=run(sh,p,x,quantize=True)
            np.testing.assert_array_equal(actual,logits)
            np.testing.assert_array_equal(h,state/4096)

if __name__=='__main__':unittest.main()
