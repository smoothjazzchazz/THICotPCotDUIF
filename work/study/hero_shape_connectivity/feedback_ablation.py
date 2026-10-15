"""Separate contributions of added fast/slow return routes after fitting."""
import json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,SEEDS
from .data import load,metrics
from .train import evaluate_stream,write_json


def analyze(root):
    output=root/'diagnostics'/'return_ablation01';output.mkdir(parents=True,exist_ok=True)
    kwargs=json.loads((ROOT/'wider_both2_candidate.json').read_text())[0];sh=make_shape(**kwargs)
    d=load(root/'data'/'uart_n'/'dev');rows=[]
    for seed in SEEDS:
        block=root/'models'/'phase_portfolio'/sh.name/'uart_n'/str(seed)/'block_0300.json'
        if not block.exists():raise ValueError('complete all six source fits first')
    for seed in SEEDS:
        result=output/f'{seed}.json'
        if result.exists():rows.extend(json.loads(result.read_text()));continue
        block=root/'models'/'phase_portfolio'/sh.name/'uart_n'/str(seed)/'block_0300.json'
        b=json.loads(block.read_text());model=np.load(b['checkpoint']);sh.leaks=model['leaks'].copy();group={node:g for g,nodes in enumerate(sh.groups) for node in nodes}
        selected=[]
        for ablation,removed_group in [('full',None),('remove_second_fast',1),('remove_second_slow',2)]:
            p=model['p'].copy();indices=[]
            if removed_group is not None:
                nodes=sh.groups[removed_group]
                for i,(s,dst) in enumerate(zip(sh.src,sh.dst)):
                    if s>=0 and group[int(dst)]==0 and group[int(s)]==removed_group:
                        j=sh.groups[0].index(int(dst))
                        if s==nodes[(j+len(nodes)//4)%len(nodes)]:indices.append(i)
                if len(indices)!=24:raise AssertionError(indices)
                p[indices]=0
            _,z=evaluate_stream(sh,p,d,np.ones(6));scores=metrics(d,z.argmax(1))
            selected.append(dict(seed=seed,profile='uart_n',ablation=ablation,zeroed_edges=len(indices),metrics=scores,
                source_checkpoint=b['checkpoint'],source_sha256=digest(b['checkpoint']),interpretation='post-fit causal ablation only; not a retrained pruned shape'))
        write_json(result,selected);rows.extend(selected)
        print(seed,[(r['ablation'],r['metrics']['message_accuracy'],r['metrics']['boundary_errors']) for r in selected],flush=True)
    write_json(output/'summary.json',rows)

if __name__=='__main__':analyze(ROOT/'runs'/'connectivity01')
