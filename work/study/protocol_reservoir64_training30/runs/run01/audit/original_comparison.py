"""Summarize old and fresh final evidence with explicit condition denominators."""
import csv,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
old=root.parents[2]/'protocol_reservoir64/runs/run01'
rows=[]
for profile in ('uart_n','uart_e','i2c'):
 for seed in (11,29,47):
  for mode in ('float','quantized'):
   pair=[]
   for name,directory in (('original',old),('training30',root)):
    record=json.loads((directory/'final'/f'{profile}_seed_{seed}_{mode}.json').read_text())
    valid=[r for r in record['conditions'] if r['valid']]
    totals={k:sum(r['symbols']['totals'][k] for r in valid) for k in ('correct','expected','emitted','false_known','false_invalid','errors')}
    by_kind={k:sum(r['symbols']['by_kind'][k]['correct'] for r in valid)/max(1,sum(r['symbols']['by_kind'][k]['expected'] for r in valid)) for k in ('START','STOP','BIT0','BIT1')}
    fit=json.loads((directory/'models'/profile/f'seed_{seed}/fit.json').read_text())
    pair.append(dict(run=name,profile=profile,seed=seed,mode=mode,selected_epoch=fit['best_epoch'],
       exact_cases=sum(r['bytes']['exact'] for r in valid),strict_cases=sum(r['passes'] for r in valid),cases=len(valid),
       exact_case_bytes=sum(r['bytes']['recovered'] for r in valid if r['bytes']['exact']),
       total_output_bytes=sum(r['bytes']['recovered'] for r in valid),
       overall_event_recall=totals['correct']/max(1,totals['expected']),
       overall_event_precision=totals['correct']/max(1,totals['emitted']),
       boundary_recall=by_kind,totals=totals))
   rows.extend(pair)
(root/'analysis/original_comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows: print(r['run'],r['profile'],r['seed'],r['mode'],r['exact_cases'],r['strict_cases'],r['overall_event_recall'],r['total_output_bytes'])
