"""Mixed-memory gradients, constant-gate equivalence and integer streaming."""
import unittest
import numpy as np
from .shapes import make_shape,initialize,cost
from .runtime import run

KW=dict(code='srr',sizes=(16,16,16),routing='port_firstlast4',feedback='both2',leaks=(1.,1.,.125))


class MixedContracts(unittest.TestCase):
    def test_first_layer_gate_control_and_gradients(self):
        kw={**KW,'leaks':(.5,1.,.125)};a=make_shape(**kw);b=make_shape(**kw,cell='mixed_first')
        pa=initialize(a,11);pb=initialize(b,11);rng=np.random.default_rng(519)
        x=rng.normal(size=(23,9));y=rng.integers(0,6,23,dtype=np.int32);h=rng.normal(0,.1,48)
        np.testing.assert_allclose(run(a,pa,x,h=h)[2],run(b,pb,x,h=h)[2],atol=1e-14)
        self.assertEqual(cost(b)['nodes'],64);self.assertEqual(cost(b)['macs_per_tick'],696)
        self.assertEqual(b.gate_nodes.tolist(),b.groups[0]);e=len(b.src);n=b.n;ge=len(b.gate_src)
        pb[e+n:e+n+ge]=rng.normal(0,.2,ge);out=run(b,pb,x,y,h=h,backward=True)
        for i in (0,e+n,e+n+ge-1,e+n+ge,len(pb)-7):
            pp=pb.copy();pm=pb.copy();pp[i]+=1e-5;pm[i]-=1e-5
            fd=(run(b,pp,x,y,h=h)[0]-run(b,pm,x,y,h=h)[0])/2e-5
            self.assertAlmostEqual(fd,out[3][i],places=7)
        for quant in (False,True):
            all_=run(b,pb,x,h=h,quantize=quant);left=run(b,pb,x[:7],h=h,quantize=quant);right=run(b,pb,x[7:],h=left[1],quantize=quant)
            np.testing.assert_array_equal(all_[2],np.r_[left[2],right[2]])

    def test_cost_and_proposal_control_equivalence(self):
        a=make_shape(**KW);b=make_shape(**KW,cell='mixed_last');pa=initialize(a,11);pb=initialize(b,11)
        self.assertEqual(cost(a)['macs_per_tick'],600);self.assertEqual(cost(a)['parameters'],654)
        self.assertEqual(cost(b)['macs_per_tick'],696);self.assertEqual(cost(b)['parameters'],766)
        self.assertEqual(cost(b)['nodes'],64);self.assertEqual(cost(b)['stored_states'],48)
        rng=np.random.default_rng(919);x=rng.normal(size=(51,9));h=rng.normal(0,.1,48)
        ra=run(a,pa,x,h=h);rb=run(b,pb,x,h=h)
        np.testing.assert_allclose(ra[1],rb[1],atol=1e-14);np.testing.assert_allclose(ra[2],rb[2],atol=1e-14)
        for g in b.groups[1:]:
            self.assertEqual(sum(s in g and d in g for s,d in zip(b.src,b.dst)),16)

    def test_all_parameter_kinds_gradient_and_chunk_causality(self):
        s=make_shape(**KW,cell='mixed_last');p=initialize(s,29);rng=np.random.default_rng(181)
        e=len(s.src);n=s.n;ge=len(s.gate_src);p[e+n:e+n+ge]=rng.normal(0,.2,ge)
        x=rng.normal(size=(19,9));y=rng.integers(0,6,19,dtype=np.int32);h=rng.normal(0,.1,n);cw=np.arange(1.,7.)
        a=run(s,p,x,y,cw,h,backward=True)
        for i in (0,e-1,e,e+n-1,e+n,e+n+17,e+n+ge,len(p)-7,len(p)-1):
            pp=p.copy();pm=p.copy();pp[i]+=1e-5;pm[i]-=1e-5
            fd=(run(s,pp,x,y,cw,h)[0]-run(s,pm,x,y,cw,h)[0])/2e-5
            self.assertAlmostEqual(fd,a[3][i],places=7)
        for i in (0,16,32,47):
            hp=h.copy();hm=h.copy();hp[i]+=1e-5;hm[i]-=1e-5
            fd=(run(s,p,x,y,cw,hp)[0]-run(s,p,x,y,cw,hm)[0])/2e-5
            self.assertAlmostEqual(fd,a[4][i],places=7)
        for quant in (False,True):
            whole=run(s,p,x,h=h,quantize=quant)
            left=run(s,p,x[:7],h=h,quantize=quant);right=run(s,p,x[7:],h=left[1],quantize=quant)
            np.testing.assert_array_equal(whole[2],np.r_[left[2],right[2]])
            np.testing.assert_array_equal(whole[1],right[1])
        ro=run(s,p,x,y,cw,h,backward=True,readout_only=True)
        np.testing.assert_array_equal(ro[3][:-6*n-6],0)
        np.testing.assert_array_equal(ro[3][-6*n-6:],a[3][-6*n-6:])

    def test_integer_reference(self):
        self._integer_reference('mixed_last',KW)
        self._integer_reference('mixed_first',{**KW,'leaks':(.5,1.,.125)})
        self._integer_reference('parent64_gated8',dict(code='srr',sizes=(24,16,16),routing='port_fanin4',feedback='both2',leaks=(.95,1.,.125)))

    def _integer_reference(self,cell,kw):
        s=make_shape(**kw,cell=cell);p=initialize(s,47);rng=np.random.default_rng(717)
        p[len(s.src)+s.n:len(s.src)+s.n+len(s.gate_src)]=rng.normal(0,.1,len(s.gate_src))
        x=rng.normal(size=(13,9));e=len(s.src);n=s.n;g=e+n;gb=g+len(s.gate_src);o=gb+len(s.gate_nodes)
        rnd=lambda v,d: (v+d//2)//d if v>=0 else -((-v+d//2)//d)
        quant=lambda v: np.where(v>=0,np.floor(v*4096+.5),np.ceil(v*4096-.5)).astype(np.int64)
        w=quant(p);xx=quant(x);old=np.zeros(n,dtype=np.int64);table=np.rint(np.tanh(np.arange(-2048,2049)/256)*4096).astype(np.int64)
        trace=[]
        for row in xx:
            now=np.zeros(n,dtype=np.int64)
            for i in range(n):
                z=int(w[e+i])*4096
                for k,(src,dst,delay) in enumerate(zip(s.src,s.dst,s.delay)):
                    if dst==i:z+=int(w[k])*int(row[-1-src] if src<0 else old[src] if delay else now[src])
                gate=int(round(s.leaks[i]*4096))
                if i in s.gate_nodes:
                    gz=int(w[gb+s.gate_nodes.tolist().index(i)])*4096
                    for k,(src,dst) in enumerate(zip(s.gate_src,s.gate_dst)):
                        if dst==i:gz+=int(w[g+k])*int(old[src])
                    gate=rnd(4096+int(table[max(0,min(4096,rnd(gz,131072)+2048))]),2)
                a=int(table[max(0,min(4096,rnd(z,65536)+2048))]);now[i]=max(-32768,min(32767,rnd((4096-gate)*int(old[i])+gate*a,4096)))
            trace.append([(int(w[o+6*n+k])*4096+sum(int(w[o+k*n+i])*int(now[i]) for i in range(n)))/16777216 for k in range(6)])
            old=now
        result=run(s,p,x,quantize=True)
        np.testing.assert_array_equal(result[2],trace);np.testing.assert_array_equal(result[1],old/4096)

if __name__=='__main__':unittest.main()
