"""Fresh/regression intersection and independently cold eight-group contracts."""
import unittest
import json
import tempfile
from pathlib import Path
import numpy as np
from .confirm_v3 import startup_case,joint_summary,prepare_regression
from .confirm import remove_feedback
from .run import ROOT,digest
from .shapes import SEEDS,PROFILES,make_shape


class ConfirmationV3Contracts(unittest.TestCase):
    def test_multiple_regressions_keep_colliding_cases_and_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);sources=[]
            for label,value in [('old',b'old-waveform'),('failed',b'new-waveform')]:
                data=root/label/'data';data.mkdir(parents=True)
                (data/'uart_n_nominal.npz').write_bytes(value)
                (data/'uart_n_nominal.json').write_text('{"metadata":"'+label+'"}')
                (data/'manifest.json').write_text(json.dumps([dict(name='uart_n_nominal',profile='uart_n',condition='nominal',kind='valid',required_messages=1000)]))
                sources.append(dict(label=label,path=str(data.parent),data_hashes={p.name:digest(p) for p in data.iterdir()}))
            out=root/'new';policy=dict(regression_sources=sources,regression_source=sources[0]['path'],regression_data_hashes=sources[0]['data_hashes'])
            config=dict(entries=[dict(weight_path='weights/model.npz')])
            prepare_regression(out,config,policy)
            manifest=json.loads((out/'regression/data/manifest.json').read_text())
            self.assertEqual([r['name'] for r in manifest],['old__uart_n_nominal','failed__uart_n_nominal'])
            self.assertEqual([r['condition'] for r in manifest],['old__nominal','failed__nominal'])
            self.assertEqual(sum(r['required_messages'] for r in manifest),2000)
            for item in sources:
                for suffix in ('.npz','.json'):
                    self.assertEqual(digest(out/'regression/data'/f"{item['label']}__uart_n_nominal{suffix}"),item['data_hashes']['uart_n_nominal'+suffix])
            freeze=json.loads((out/'regression/freeze.json').read_text())
            self.assertEqual(freeze['entries'][0]['weight_path'],'../weights/model.npz')
            self.assertFalse(freeze['data_generated_after_freeze'])
            prepare_regression(out,config,policy)
            (root/'failed/data/uart_n_nominal.npz').write_bytes(b'changed')
            with self.assertRaises(AssertionError):prepare_regression(out,config,policy)

    def test_feedback_control_keeps_only_forward_routes_and_constant_gates(self):
        for file in ('wider_both2_candidate.json','readout_dense_candidate.json','mixed_first_candidates.json','gate_eight_candidates.json'):
            for kw in json.loads((ROOT/file).read_text()):
                sh=make_shape(**kw);p=np.ones(sh.parameters);q,removed=remove_feedback(sh,p)
                groups={n:g for g,nodes in enumerate(sh.groups) for n in nodes}
                for i,(s,d) in enumerate(zip(sh.src,sh.dst)):
                    self.assertEqual(q[i],int(s<0 or groups[int(s)]<groups[int(d)]))
                if getattr(sh,'mixed',False):
                    start=len(sh.src)+sh.n;end=start+len(sh.gate_src)
                    self.assertFalse(q[start:end].any());self.assertTrue(q[end:end+len(sh.gate_nodes)].all())
                self.assertTrue(p.all());self.assertTrue(q[-6:].all())

    def test_startup_payloads_and_scoring_boundary(self):
        for profile in ('uart_n','uart_e'):
            for mode in ('idle','midframe'):
                s=startup_case(profile,11951,mode,3)
                self.assertEqual(sum(g['valid'] for g in s['groups']),8)
                if mode=='midframe':
                    self.assertEqual(s['observable_sync_high_ticks'],256)
                    self.assertGreater(s['startup_ambiguous_until'],256)
                else:self.assertNotIn('startup_ambiguous_until',s)

    def test_same_five_seeds_must_pass_both_suites(self):
        fresh=[];old=[]
        for arithmetic in ('float','quantized'):
            for profile in PROFILES:
                for seed in SEEDS:
                    base=dict(shape='test',profile=profile,seed=seed,arithmetic=arithmetic)
                    fresh.append(dict(**base,pass_all=seed!=SEEDS[0]))
                    old.append(dict(**base,pass_all=seed!=SEEDS[1] if arithmetic=='float' else seed!=SEEDS[0]))
        result=joint_summary(fresh,old)['per_shape']
        self.assertFalse(result['test/float']['qualified'])
        self.assertEqual(set(result['test/float']['passes'].values()),{4})
        self.assertTrue(result['test/quantized']['qualified'])
        self.assertEqual(set(result['test/quantized']['passes'].values()),{5})
        with self.assertRaises((KeyError,ValueError)):joint_summary(fresh,old[:-1])


if __name__=='__main__':unittest.main()
