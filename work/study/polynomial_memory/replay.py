"""Load the study recognizer and consume binary samples from a text file/stdin.

Whitespace and commas are ignored. Each remaining 0/1 is one causal tick.
Outputs JSON events; class 2 is background and class 7 is unknown.
"""
import argparse
import json
from pathlib import Path
import sys
from work.study.shared.broad import Receiver


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,default=Path(__file__).with_name('compact_20_q8.json'))
    parser.add_argument('--input',type=Path)
    args=parser.parse_args()
    data=json.loads(args.config.read_text())
    receiver=Receiver(data['config'],data['readout'])
    text=args.input.read_text() if args.input else sys.stdin.read()
    for token in text:
        if token.isspace() or token==',':continue
        if token not in '01':raise ValueError('Expected only binary samples, whitespace or commas')
        event=receiver.step(int(token))
        if event is not None:print(json.dumps({**event,'emit_tick':receiver.tick-1}))

if __name__=='__main__':main()
