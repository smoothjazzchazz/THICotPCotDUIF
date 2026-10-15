"""Integer arithmetic development diagnostic, separate from confirmation."""
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .confirm import infer
from .data import load,metrics
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';folder=root/'quant_development'/'profile_fresh120';folder.mkdir(parents=True,exist_ok=True)
    for kwargs in json.loads((ROOT/'phase_route_candidates.json').read_text()):
        sh=make_shape(**kwargs)
        for profile in ('uart_n','uart_e'):
            dev=load(root/'data_extended'/profile/'dev')
            for seed in SEEDS:
                out=folder/f'{sh.name}_{profile}_{seed}.json'
                if out.exists():continue
                blocks=sorted((root/'models'/'phase_profile_fresh'/sh.name/profile/str(seed)).glob('block_*.json'))
                b=json.loads(blocks[-1].read_text());a=np.load(b['checkpoint']);sh.leaks=a['leaks'].copy()
                p=np.rint(a['p']*4096)/4096;pred=infer(sh,p,dev['x'],True);score=metrics(dev,pred)
                row=dict(shape=sh.name,profile=profile,seed=seed,arithmetic='Q3.12 integer',source_block=str(blocks[-1]),
                    checkpoint_sha256=digest(b['checkpoint']),float_selected=b['selected'],integer=score,
                    qualification=False,distribution='extended development; not fresh confirmation')
                write_json(out,row);print(json.dumps(dict(shape=sh.name,profile=profile,seed=seed,
                    exact=score['message_accuracy'],boundary=score['boundary_errors'])),flush=True)
