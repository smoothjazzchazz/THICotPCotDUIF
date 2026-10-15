"""Additional independent development coverage for rare UART timing boundaries."""
from .run import ROOT,digest
from .vendor.data import Builder
from .shapes import features
from .data import save
from .startup_audit import mismatches
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01'/'data_corner_dev_v4';root.mkdir(exist_ok=True)
    for pi,profile in enumerate(('uart_n','uart_e')):
        for ci,condition in enumerate(('jitter','minus_jitter','plus_jitter','gaps')):
            base=root/profile/condition
            if base.with_suffix('.json').exists():continue
            seed=361000000+pi*1000000+ci*10000;b=Builder(profile,seed)
            for i in range(1000):
                if i==0:payload=b.rng.integers(0,256,1024).tolist()
                elif i==1:payload=list(range(256))
                elif i<6:payload=[(0,255,85,170)[i-2]]*64
                elif i%100==0:payload=b.rng.integers(0,256,128).tolist()
                else:payload=b.rng.integers(0,256,int(b.rng.integers(1,9))).tolist()
                b.message(payload,condition)
            s=b.finish();s['seed']=seed;s['x']=features(s['lines'])[0]
            assert not mismatches(s)
            save(base,s);print(profile,condition,'ready',flush=True)
    write_json(root/'manifest.json',dict(seed_family=361000000,role='additional development only; never claimed as fresh confirmation',
        scoring='retain every existing precision_v2 case and add these four timing cases; same exact messages/boundaries and rejection rules',
        files={str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file() and p.name!='manifest.json'}))
