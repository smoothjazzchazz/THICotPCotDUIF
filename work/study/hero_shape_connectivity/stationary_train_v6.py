"""Training-only sustained timing corners, separate from development/confirmation."""
from .run import ROOT,digest
from .data import save
from .vendor.data import Builder
from .shapes import features
from .startup_audit import mismatches
from .train import write_json


def generate(root):
    folder=root/'data_stationary_train_v6'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for ci,condition in enumerate(('jitter','minus_jitter','plus_jitter','gaps')):
            for bank in range(4):
                path=folder/profile/f'{condition}_{bank:02d}';seed=381000000+pi*1000000+ci*10000+bank*1000
                if path.with_suffix('.json').exists():continue
                b=Builder(profile,seed)
                for i in range(1000):
                    if i==0:payload=b.rng.integers(0,256,1024).tolist()
                    elif i==1:payload=list(range(256))
                    elif i<6:payload=[(0,255,85,170)[i-2]]*64
                    elif i%100==0:payload=b.rng.integers(0,256,128).tolist()
                    else:payload=b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist()
                    b.message(payload,condition)
                s=b.finish();s['x']=features(s['lines'])[0];s['seed']=seed
                assert not mismatches(s),'declared payload contract';save(path,s)
                print(profile,condition,bank,len(s['lines']),flush=True)
    write_json(folder/'manifest.json',dict(training_families=[381000000,382000000],development='unchanged and separate',messages_per_profile=16000,
        purpose='sustained corner coverage rather than only interleaved conditions',files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}))

if __name__=='__main__':generate(ROOT/'runs'/'connectivity01')
