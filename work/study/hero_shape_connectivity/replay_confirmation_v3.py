"""Generate or evaluate a v3 confirmation using only its frozen implementation."""
import argparse,importlib,json,sys
from pathlib import Path
from .run import ROOT,digest


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['generate','evaluate']);ap.add_argument('--label',required=True);ap.add_argument('--workers',type=int,default=6);ap.add_argument('--arithmetic',default='float,quantized,no_recurrence,no_feedback');a=ap.parse_args()
    out=(ROOT/'runs/connectivity01/confirmations'/a.label).resolve();frozen=json.loads((out/'freeze.json').read_text())
    for name,expected in frozen['source_hashes'].items():assert digest(out/'source'/name)==expected,('frozen source changed',name)
    for entry in frozen['entries']:assert digest(out/entry['weight_path'])==entry['weight_sha256'],('frozen weights changed',entry['weight_path'])
    sys.path.insert(0,str(out));module=importlib.import_module('source.confirm_v3')
    if a.action=='generate':module.generate_v3(out)
    else:module.evaluate_v3(out,a.workers,a.arithmetic)
