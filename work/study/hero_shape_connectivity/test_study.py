"""Physical graph, timing coverage, gradient and continuous inference contracts."""
import unittest
import numpy as np
from .shapes import make_shape,initialize,historical_shape,features
from .vendor.network import run,Receiver,pulses,events
from .data import build,conditions
from .runtime import run as runtime_run,Receiver as RuntimeReceiver


class Contracts(unittest.TestCase):
    def test_observable_cold_sync_payload_contract(self):
        from .precision_data_v2 import cold
        from .startup_audit import mismatches
        for profile in ('uart_n','uart_e'):
            for seed in (31911,31929,31947):
                s=cold(profile,seed,3)
                self.assertEqual(s['observable_sync_high_ticks'],256)
                self.assertEqual(mismatches(s),[])

    def test_distributed_inlets_equal_cost(self):
        from .shapes import cost
        kw=dict(code='srr',sizes=(24,16,24),feedback='both2')
        base=make_shape(**kw,routing='port_fanin4');spread=make_shape(**kw,routing='port_distfast4');wide=make_shape(**kw,routing='port_fastfanin16')
        self.assertEqual(cost(spread)['macs_per_tick'],cost(wide)['macs_per_tick'])
        self.assertEqual(len(spread.src)-len(base.src),12)
        old=set(zip(base.src,base.dst,base.delay))
        for sh in (spread,wide):self.assertTrue(old<=set(zip(sh.src,sh.dst,sh.delay)))
        incoming=lambda sh:{int(d) for s,d in zip(sh.src,sh.dst) if s in sh.groups[0] and d in sh.groups[1]}
        self.assertEqual(len(incoming(spread)),4);self.assertEqual(len(incoming(wide)),1)

    def test_edge_reallocation_preserves_fixed_routes(self):
        from .shapes import cost
        kw=dict(code='srr',sizes=(24,16,24),routing='port_fanin4',feedback='both2')
        base=make_shape(**kw);thin=make_shape(**kw,first_fanin=2)
        one=make_shape(**{**kw,'feedback':'both1'})
        self.assertEqual(cost(thin)['macs_per_tick'],cost(one)['macs_per_tick'])
        self.assertEqual(len(base.src)-len(thin.src),48)
        base_edges=set(zip(base.src,base.dst,base.delay));new_edges=set(zip(thin.src,thin.dst,thin.delay))
        self.assertTrue(new_edges<=base_edges)
        self.assertTrue(all(s in base.groups[0] and d in base.groups[0] and s!=d for s,d,t in base_edges-new_edges))
        for d in thin.groups[0]:self.assertEqual(sum(s in thin.groups[0] and dd==d for s,dd,t in new_edges),2)

    def test_focal_gradient_and_identical_forward(self):
        sh=make_shape('srr',feedback='both2');p=initialize(sh,29);rng=np.random.default_rng(124)
        x=rng.normal(size=(19,9));y=rng.integers(0,6,19,dtype=np.int32);cw=np.array([1.,2.,3.,4.,5.,6.])
        a=runtime_run(sh,p,x,y,cw,backward=True,focal=True,learn_leaks=False);b=runtime_run(sh,p,x,y,cw,backward=True)
        np.testing.assert_array_equal(a[1],b[1]);np.testing.assert_array_equal(a[2],b[2])
        for i in (0,29,len(sh.src),len(sh.src)+sh.n+7,len(p)-6,len(p)-1):
            pp=p.copy();pm=p.copy();pp[i]+=1e-5;pm[i]-=1e-5
            fd=(runtime_run(sh,pp,x,y,cw,focal=True)[0]-runtime_run(sh,pm,x,y,cw,focal=True)[0])/2e-5
            self.assertAlmostEqual(fd,a[3][i],places=6)

    def test_bounded_development_and_startup_scoring(self):
        from .train import evaluate_stream
        from .data import metrics
        from .vendor.data import reference_labels,assemble
        sh=make_shape('srr',feedback='both2');p=initialize(sh,11)
        d=build('uart_n',94123,ticks=9000)
        a=run(sh,p,d['x'],d['labels']);loss,z=evaluate_stream(sh,p,d,np.ones(6))
        np.testing.assert_array_equal(z,a[2]);self.assertAlmostEqual(loss,a[0],places=12)
        cut=d['groups'][0]['start']+37;lines=d['lines'][cut:];labels=reference_labels(lines,'uart_n')
        truth,rejected=assemble(events(labels),'uart_n');groups=[{**g,'start':g['start']-cut,'end':g['end']-cut} for g in d['groups'][1:]]
        truncated=dict(lines=lines,labels=labels,truth=truth,groups=groups,profile='uart_n',startup_ambiguous_until=groups[0]['start'])
        score=metrics(truncated,labels)
        self.assertEqual(score['boundary_errors'],0);self.assertEqual(score['background_accepted'],0);self.assertEqual(score['message_accuracy'],1)

    def test_leak_gradient_and_ordinary_inference_agreement(self):
        rng=np.random.default_rng(531);sh=make_shape('srr',feedback='top1');p=initialize(sh,11)
        x=rng.normal(size=(31,9));y=rng.integers(0,6,31,dtype=np.int32)
        a=runtime_run(sh,p,x,y,backward=True,learn_leaks=True)
        b=runtime_run(sh,p,x,y,backward=True)
        for i in (0,1,2,3):np.testing.assert_array_equal(a[i],b[i])
        for node in (25,45,63):
            old=sh.leaks[node];sh.leaks[node]=old+1e-5;lp=runtime_run(sh,p,x,y)[0]
            sh.leaks[node]=old-1e-5;lm=runtime_run(sh,p,x,y)[0];sh.leaks[node]=old
            self.assertAlmostEqual((lp-lm)/2e-5,a[4][sh.n+node],places=6)

    def test_gated_accounting_gradient_and_causality(self):
        rng=np.random.default_rng(811)
        for schedule in ('registered','current'):
            sh=make_shape('srr',schedule,cell='gated');p=initialize(sh,11)
            self.assertEqual(sh.n,32);self.assertEqual(sh.config()['nodes'],64)
            self.assertEqual(len(p),2*len(sh.src)+8*sh.n+6)
            x=rng.normal(size=(17,9));y=rng.integers(0,6,17,dtype=np.int32);h=rng.normal(0,.1,sh.n)
            _,_,whole,g,dh=runtime_run(sh,p,x,y,h=h,backward=True)
            indices=[0,len(sh.src)+2,2*len(sh.src)+1,2*len(sh.src)+sh.n+1,len(p)-1]
            for j in indices:
                pp=p.copy();pm=p.copy();pp[j]+=1e-5;pm[j]-=1e-5
                fd=(runtime_run(sh,pp,x,y,h=h)[0]-runtime_run(sh,pm,x,y,h=h)[0])/2e-5
                self.assertAlmostEqual(fd,g[j],places=7)
            hp=h.copy();hm=h.copy();hp[3]+=1e-5;hm[3]-=1e-5
            fd=(runtime_run(sh,p,x,y,h=hp)[0]-runtime_run(sh,p,x,y,h=hm)[0])/2e-5
            self.assertAlmostEqual(fd,dh[3],places=7)
            _,hh,left,_,_=runtime_run(sh,p,x[:7],h=h);right=runtime_run(sh,p,x[7:],h=hh)[2]
            np.testing.assert_array_equal(whole,np.r_[left,right])

    def test_factorized_head_gradient_and_online(self):
        rng=np.random.default_rng(5);sh=make_shape('srr',head='factor');p=initialize(sh,11)
        x=rng.normal(size=(23,9));y=rng.integers(0,6,23,dtype=np.int32)
        g=runtime_run(sh,p,x,y,backward=True)[3]
        for j in (0,17,len(sh.src),len(p)-1,len(p)-6,len(p)-5):
            pp=p.copy();pm=p.copy();pp[j]+=1e-5;pm[j]-=1e-5
            fd=(runtime_run(sh,pp,x,y)[0]-runtime_run(sh,pm,x,y)[0])/2e-5
            self.assertAlmostEqual(fd,g[j],places=7)
        s=build('uart_n',913,ticks=1024);rx=RuntimeReceiver(sh,p)
        a=rx.samples(s['lines'][:417])+rx.samples(s['lines'][417:])
        b=events(pulses(runtime_run(sh,p,s['x'])[2].argmax(1)))
        self.assertEqual(a,b)

    def test_baseline_is_identical(self):
        for schedule in ('registered','current'):
            a=make_shape('sss',schedule);b=historical_shape('stack3_'+schedule,64)
            for field in ('src','dst','delay','leaks'):np.testing.assert_array_equal(getattr(a,field),getattr(b,field))

    def test_actual_closed_ring_and_common_routes(self):
        base=make_shape('sss')
        for code in ('srr','ssr','srs','rsr'):
            sh=make_shape(code)
            for kind,nodes in zip(code,sh.groups):
                edges=[(int(s),int(d)) for s,d in zip(sh.src,sh.dst) if s in nodes and d in nodes]
                if kind=='r':
                    self.assertEqual(len(edges),len(nodes));self.assertTrue(all(s!=d for s,d in edges))
                    for i in nodes:
                        self.assertEqual(sum(s==i for s,d in edges),1);self.assertEqual(sum(d==i for s,d in edges),1)
                    succ=dict(edges);visited=set();i=nodes[0]
                    for _ in nodes:visited.add(i);i=succ[i]
                    self.assertEqual(visited,set(nodes));self.assertEqual(i,nodes[0])
            group={i:g for g,nodes in enumerate(sh.groups) for i in nodes}
            routes=lambda a:{(int(s),int(d),int(t)) for s,d,t in zip(a.src,a.dst,a.delay) if s<0 or group[int(s)]!=group[int(d)]}
            self.assertEqual(routes(base),routes(sh))

    def test_distinct_self_skip_shapes(self):
        for code,multiplicity in [('rrr',1),('hhh',2),('kkk',4)]:
            sh=make_shape(code)
            for nodes in sh.groups:self.assertEqual(sum(s in nodes and d in nodes for s,d in zip(sh.src,sh.dst)),len(nodes)*multiplicity)

    def test_gradient_and_causality(self):
        rng=np.random.default_rng(9)
        for schedule in ('current','registered'):
            sh=make_shape('srr',schedule);p=initialize(sh,11);x=rng.normal(size=(20,9));y=rng.integers(0,6,20,dtype=np.int32)
            _,_,full,g,_=run(sh,p,x,y,backward=True)
            for j in (0,100,len(sh.src),len(p)-1):
                pp=p.copy();pm=p.copy();pp[j]+=1e-5;pm[j]-=1e-5
                numerical=(run(sh,pp,x,y)[0]-run(sh,pm,x,y)[0])/2e-5
                self.assertAlmostEqual(g[j],numerical,places=7)
            _,h,left,_,_=run(sh,p,x[:7]);right=run(sh,p,x[7:],h=h)[2]
            np.testing.assert_array_equal(full,np.r_[left,right])
            other=x.copy();other[7:]*=-1
            np.testing.assert_array_equal(full[:7],run(sh,p,other)[2][:7])

    def test_training_coverage_and_online(self):
        for profile in ('uart_n','uart_e','i2c','spi0','spi1','spi2','spi3'):
            s=build(profile,831,ticks=32768)
            self.assertTrue(set(conditions(profile))<={g['condition'] for g in s['groups'] if g['valid']})
            if profile=='spi1':
                sh=make_shape();p=initialize(sh,11);online=Receiver(sh,p);out=[]
                for t in range(0,1024,37):out+=online.samples(s['lines'][t:min(t+37,1024)])
                pred=run(sh,p,s['x'][:1024])[2].argmax(1)
                self.assertEqual(out,events(pulses(pred)))

if __name__=='__main__':unittest.main()
