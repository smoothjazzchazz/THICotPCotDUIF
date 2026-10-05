"""Post-freeze check of a common finite-width datapath for the binary candidates."""
import numpy as np
from .run import ROOT,read,save
from .models import collect
from .confirmation import check_lock


def main():
    check_lock()
    checked=0
    for name in ('binary_strict','binary_duration'):
        for task in ('pulse','biphase','clockdata','context','transfer'):
            streams=read(ROOT/f'artifacts/confirmation/{task}_streams.json.gz')
            for rep in range(3):
                model=read(ROOT/f'artifacts/frozen/{name}_{task}_{rep}.json')
                r=model['readout']
                w,b=np.asarray(r['weights']),np.asarray(r['bias'])
                assert np.max(np.abs(w))<=127 and np.max(np.abs(b))<=127
                assert 0<=r['floor']<2**17 and 0<=r['margin']<2**17
                # First stream of each condition, first 16 gates; includes noise.
                records=collect([s for s in streams if s['block']==0],model['config'])
                for record in records:
                    for x in record['x'][:16]:
                        assert np.all(np.abs(x)<=1)
                        expected=x@w+b
                        actual=[]
                        for j in range(3):
                            acc=int(b[j])
                            for v,coefficient in zip(x,w[:,j]):
                                acc=(acc+int(v)*int(coefficient))&((1<<18)-1)
                                if acc&(1<<17):
                                    acc-=1<<18
                            actual.append(acc)
                        assert actual==expected.tolist()
                        checked+=1
    save(ROOT/'artifacts/verification/fixed_width.json',{
        'passed':True,'gates_with_explicit_wrapping_accumulation':checked,
        'coefficient_bits':8,'bias_bits':8,'score_bits':18,'margin_difference_bits':19,
        'all_30_frozen_binary_configs_fit':True,'worst_case_absolute_score_bound':601*128,
        'note':'Software integer-width verification and arithmetic bound; no RTL equivalence or formal proof claim.'})
    print(checked,'gate score vectors reproduced with explicit signed 18-bit accumulators')


if __name__=='__main__':
    main()
