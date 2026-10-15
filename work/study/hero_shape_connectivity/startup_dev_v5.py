"""Independent development coverage of the two already-trained startup modes."""
from .run import ROOT,digest
from .data import save,conditions
from .vendor.data import Builder
from .shapes import features
from .startup_audit import mismatches
from .train import write_json


def generate(root):
    folder=root/'data_startup_dev_v5'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for mode,count,family in [('idle',256,371000000),('errors',64,372000000)]:
            for i in range(count):
                base=folder/profile/f'{mode}_{i:03d}'
                if base.with_suffix('.json').exists():continue
                seed=family+pi*100000+i*100;b=Builder(profile,seed)
                errors=['framing','break']+(['parity'] if profile=='uart_e' else [])
                for j in range(8):
                    if mode=='errors':
                        b.message([int(b.rng.integers(256))],invalid=errors[(i+j)%len(errors)])
                        payload=b.rng.integers(0,256,4).tolist()
                    else:
                        size=64 if j==0 and i%11==0 else int(b.rng.integers(1,9))
                        payload=b.rng.integers(0,256,size).tolist()
                        if i%5==0:payload=[(0,255,85,170)[i//5%4]]*size
                    b.message(payload,conditions(profile)[(i+j)%7])
                    if mode=='errors' and j==3:b.idle(4096)
                s=b.finish();s['x']=features(s['lines'])[0];s['seed']=seed
                assert not mismatches(s),'declared payload differs from independent parser'
                save(base,s)
        print('Independent startup development ready',profile,flush=True)
    write_json(folder/'manifest.json',dict(development_families=[371000000,372000000],
        training='unchanged families341000000/342000000; no confirmation examples used',
        valid_groups_per_profile=2560,files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}))

if __name__=='__main__':generate(ROOT/'runs'/'connectivity01')
