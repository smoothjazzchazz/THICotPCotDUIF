"""Physical budget, retained wiring, gate equivalence and sustained coverage."""
import unittest
from pathlib import Path
import numpy as np
from .shapes import make_shape,initialize,cost
from .runtime import run
from .train import native_v6_long_path

KW=dict(code='srr',schedule='registered',routing='port_fanin4',feedback='both2',leaks=(.95,1.,.125))


class EightGateContracts(unittest.TestCase):
    def test_physical_pair_and_real_closed_rings(self):
        base=make_shape(**KW,sizes=(24,16,24))
        small=make_shape(**KW,sizes=(24,16,16),cell='parent64_plain56')
        gated=make_shape(**KW,sizes=(24,16,16),cell='parent64_gated8')
        edges=lambda s:set(zip(s.src.tolist(),s.dst.tolist(),s.delay.tolist()))
        self.assertEqual(edges(small),{e for e in edges(base) if e[0]<56 and e[1]<56}|{(55,40,1)})
        self.assertEqual(edges(small),edges(gated))
        for group in small.groups[1:]:
            local={e for e in edges(small) if e[0] in group and e[1] in group}
            self.assertEqual(local,{(group[(i-1)%len(group)],d,1) for i,d in enumerate(group)})
        self.assertEqual(gated.gate_nodes.tolist(),list(range(0,24,3)))
        self.assertEqual([cost(s)['nodes'] for s in (base,small,gated)],[64,56,64])
        self.assertEqual([cost(s)['macs_per_tick'] for s in (base,small,gated)],[840,768,816])
        self.assertEqual([cost(s)['parameters'] for s in (base,small,gated)],[910,830,886])

    def test_matched_initial_function_and_gate_gradient(self):
        small=make_shape(**KW,sizes=(24,16,16),cell='parent64_plain56')
        gated=make_shape(**KW,sizes=(24,16,16),cell='parent64_gated8')
        a=initialize(small,11);b=initialize(gated,11);rng=np.random.default_rng(791)
        x=rng.normal(size=(23,9));h=rng.normal(0,.1,56);y=rng.integers(0,6,23,dtype=np.int32)
        np.testing.assert_allclose(run(small,a,x,h=h)[2],run(gated,b,x,h=h)[2],atol=1e-14)
        e=len(gated.src);g=e+gated.n;b[g:g+48]=rng.normal(0,.2,48)
        gradient=run(gated,b,x,y,h=h,backward=True)[3]
        for index in (g,g+47,g+48,g+55):
            plus=b.copy();minus=b.copy();plus[index]+=1e-5;minus[index]-=1e-5
            fd=(run(gated,plus,x,y,h=h)[0]-run(gated,minus,x,y,h=h)[0])/2e-5
            self.assertAlmostEqual(fd,gradient[index],places=7)

    def test_all_sustained_corners_in_first_64_epochs(self):
        paths=[native_v6_long_path(Path('/study'),'uart_n',i) for i in range(1,65)]
        corners=[p.name for p in paths if 'stationary' in str(p)]
        self.assertEqual(len(corners),16)
        self.assertEqual(set(corners),{f'{condition}_{bank:02d}' for condition in ('jitter','minus_jitter','plus_jitter','gaps') for bank in range(4)})
        self.assertEqual(paths[0],Path('/study/data_precision_v2/uart_n/train/long_0001'))


if __name__=='__main__':unittest.main()
