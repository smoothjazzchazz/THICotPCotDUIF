"""Reproduce the confirmed clocked comparison in a new, isolated directory."""
import argparse
import json
from pathlib import Path
from .run import ROOT,launch,batch
from .confirm import freeze,generate,evaluate
from .shapes import SEEDS


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--confirmation-seed-family',type=int,default=191000000);a=ap.parse_args()
    if not a.output.exists():launch(a.output)
    elif not (a.output/'environment.json').exists():raise ValueError('existing directory is not a recorded study run')
    candidates=json.loads((ROOT/'cost_candidates.json').read_text());profiles=('i2c','spi0','spi1','spi2','spi3')
    batch(a.output,candidates,SEEDS,profiles,30,a.workers,'matched','clocked30')
    batch(a.output,candidates,SEEDS,('spi1',),60,a.workers,'matched','startup60')
    out=a.output/'confirmations'/'clocked_reproduction'
    if not out.exists():freeze(a.output,'clocked_reproduction',candidates,a.confirmation_seed_family,profiles=profiles)
    else:
        if json.loads((out/'freeze.json').read_text())['seed_family']!=a.confirmation_seed_family:raise ValueError('confirmation family differs')
    generate(out);evaluate(out,a.workers,'float,quantized,no_recurrence')

if __name__=='__main__':main()
