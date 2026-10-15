"""Freeze a completed source and inspect its failed development pulse contexts."""
import argparse,json
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .data import load
from .runtime import pulses
from .train import evaluate_stream,write_json


def inspect(source,out):
    b=json.loads(source.read_text());sh=make_shape(**b['construction']);a=np.load(b['checkpoint']);sh.leaks=a['leaks'];root=ROOT/'runs/connectivity01'
    out.mkdir(parents=True,exist_ok=False);rows=[]
    write_json(out/'source.json',dict(block=str(source),block_sha256=digest(source),checkpoint=b['checkpoint'],checkpoint_sha256=digest(b['checkpoint']),script_sha256=digest(__file__)))
    for case in b['selected']['cases']:
        if case['exact_messages']==case['valid_messages'] and not any(case[k] for k in ('boundary_errors','invalid_accepted','background_accepted')):continue
        prefix,name=case['case'].split('_',1)
        base={'original':root/'data_precision_v2'/b['profile']/'dev','corner':root/'data_corner_dev_v4'/b['profile'],'startup':root/'data_startup_dev_v5'/b['profile']}[prefix]/name
        s=load(base);_,z=evaluate_stream(sh,a['p'],s,np.array(b['class_weights']));k=z.argmax(1);pred=pulses(k)
        ticks=np.flatnonzero((pred!=s['labels'])&(np.arange(len(k))>=s.get('startup_ambiguous_until',0)))
        contexts=[]
        for t in ticks[:24]:
            near=[g for g in s['groups'] if g['start']-32<=t<=g['end']+32]
            start=max(0,int(t)-4);end=min(len(k),int(t)+5)
            contexts.append(dict(tick=int(t),expected=int(s['labels'][t]),predicted=int(pred[t]),raw_class=int(k[t]),previous_raw_class=int(k[t-1]) if t else 0,
                groups=near,window_start=start,features=s['x'][start:end].tolist(),labels=s['labels'][start:end].tolist(),pulses=pred[start:end].tolist(),logits=z[start:end].tolist()))
        rows.append(dict(case=case['case'],data_sha256=digest(base.with_suffix('.npz')),score=case,pulse_errors=len(ticks),first_contexts=contexts))
        np.savez_compressed(out/(case['case']+'.npz'),ticks=ticks,expected=s['labels'][ticks],predicted=pred[ticks],logits=z[ticks])
    write_json(out/'result.json',dict(profile=b['profile'],seed=b['seed'],shape=sh.name,failed_cases=rows))
    print(json.dumps([dict(case=r['case'],errors=r['pulse_errors'],first=[(c['tick'],c['expected'],c['predicted']) for c in r['first_contexts'][:5]]) for r in rows]))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--label',required=True);a=ap.parse_args()
    inspect(a.source,ROOT/'runs/connectivity01/diagnostics'/a.label)
