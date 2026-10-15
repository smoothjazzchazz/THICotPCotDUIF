"""Add known-idle cold startup and independently started error/recovery streams."""
from .run import ROOT,digest
from .data import save,conditions
from .vendor.data import Builder
from .shapes import features
from .train import write_json


def generate(root):
    folder=root/'data_startup_modes'
    for pi,profile in enumerate(('uart_n','uart_e')):
        for i in range(256):
            base=folder/profile/f'idle_{i:03d}'
            if base.with_suffix('.json').exists():continue
            b=Builder(profile,341000000+pi*100000+i*100)
            for j in range(8):
                size=64 if j==0 and i%11==0 else int(b.rng.integers(1,9))
                payload=b.rng.integers(0,256,size).tolist()
                if i%5==0:payload=[(0,255,85,170)[i//5%4]]*size
                b.message(payload,conditions(profile)[(i+j)%7])
            s=b.finish();s['x']=features(s['lines'])[0];s['seed']=341000000+pi*100000+i*100;save(base,s)
        for i in range(64):
            base=folder/profile/f'errors_{i:03d}'
            if base.with_suffix('.json').exists():continue
            b=Builder(profile,342000000+pi*100000+i*100);errors=['framing','break']+(['parity'] if profile=='uart_e' else [])
            for j in range(8):
                b.message([int(b.rng.integers(256))],invalid=errors[(i+j)%len(errors)])
                b.message(b.rng.integers(0,256,4).tolist(),conditions(profile)[(i+j)%7])
                if j==3:b.idle(4096)
            s=b.finish();s['x']=features(s['lines'])[0];s['seed']=342000000+pi*100000+i*100;save(base,s)
        print('Both startup modes and error-stream coverage ready',profile,flush=True)
    write_json(folder/'manifest.json',dict(training_families=[341000000,342000000],development='unchanged verified precision_v2',
        files={str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'}))

if __name__=='__main__':generate(ROOT/'runs'/'connectivity01')
