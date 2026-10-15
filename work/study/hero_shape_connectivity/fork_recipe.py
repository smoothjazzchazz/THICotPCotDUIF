"""Copy resumable optimizer histories into a new, explicitly named recipe trial."""
import argparse
import json
from pathlib import Path
import shutil
from .shapes import make_shape
from .train import write_json
from .run import ROOT,digest


def fork(root,candidates,source,dest,profiles,seeds):
    for kwargs in candidates:
        shape=make_shape(**kwargs)
        for profile in profiles:
            for seed in seeds:
                src=root/'models'/source/shape.name/profile/str(seed)
                dst=root/'models'/dest/shape.name/profile/str(seed)
                if dst.exists():raise ValueError(('destination exists',str(dst)))
                history=[json.loads(l) for l in (src/'history.jsonl').read_text().splitlines()]
                checkpoint=src/f"epoch_{history[-1]['epoch']:04d}.npz"
                shutil.copytree(src,dst)
                write_json(dst/'fork_provenance.json',dict(source=str(src),epoch=history[-1]['epoch'],
                    source_checkpoint_sha256=digest(checkpoint),source_history_sha256=digest(src/'history.jsonl'),
                    reason='matched lower-learning-rate rescue; exact p, Adam moments, steps and exposure retained'))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidates',type=Path,required=True)
    ap.add_argument('--source',default='matched');ap.add_argument('--dest',default='low_lr')
    ap.add_argument('--profiles',default='uart_n,uart_e');ap.add_argument('--seeds',default='11,29,47')
    a=ap.parse_args();fork(ROOT/'runs'/'connectivity01',json.loads(a.candidates.read_text()),a.source,a.dest,a.profiles.split(','),list(map(int,a.seeds.split(','))))
