"""Rebuild an honest six-seed progress view without declaring qualification."""
import json
from pathlib import Path
import numpy as np
from .run import ROOT
from .shapes import make_shape,cost,SEEDS
from .report import diagram
from .train import key,write_json


def report(root):
    records=[];graphs={}
    for directory in sorted((root/'models').glob('*/*/*/*')):
        blocks=sorted(directory.glob('block_*.json'))
        if not blocks:continue
        row=json.loads(blocks[-1].read_text());records.append(row)
        graphs[row['shape']]=row['construction']
    costs={name:cost(make_shape(**kwargs)) for name,kwargs in graphs.items()}
    write_json(root/'all_shape_costs.json',costs)
    primary=make_shape(**json.loads((ROOT/'wider_both2_candidate.json').read_text())[0]).name
    current=[]
    for profile in ('uart_n','uart_e'):
        chosen=[]
        for seed in SEEDS:
            options=[r for r in records if r['shape']==primary and r['profile']==profile and r['seed']==seed and r.get('development_distribution')=='precision_v2']
            if options:chosen.append(max(options,key=lambda r:key(r['selected'])))
        passes=sum(r['selected']['message_accuracy']==1 and not any(r['selected'][k] for k in ('boundary_errors','invalid_accepted','background_accepted')) for r in chosen)
        current.append(f'{profile}: {passes}/{len(chosen)}')
    lines=['# UART research progress','',
        '**Historical development ledger; these results are not fresh confirmation.** Current qualification is recorded in [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md).','',
        'The independently confirmed clocked resource result is in [REPORT.md](REPORT.md). This page preserves the development stages and their failures, separately from later full-profile confirmation.','',
        'On the earlier corrected2,304-group development suite, the primary64-node registered graph reaches **'+', '.join(current)+'**. The enlarged8,864-group suite exposes additional failures; see [CURRENT_FINDINGS.md](CURRENT_FINDINGS.md). This earlier same-seed checkpoint portfolio is not a matched topology ranking or fresh confirmation. Distributions below remain separate.','',
        '## Best available development checkpoints','',
        'Selection across recipes is exploratory. It uses worst-condition complete-message recovery first, followed by overall recovery and errors, exactly as the training selector does. Recipes and exposure differ; this table is not a matched architectural comparison. Missing seeds remain missing.','',
        '| Shape | Profile | Seeds available | Exact-message range | All messages exact | Entire development suite passes |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    shortlist=[];best_records=[]
    for name in sorted(graphs):
        if 'feedback' in name:continue
        if not any(part in name for part in ('_top1','_both1','_both2')):continue
        shortlist.append(name)
        for profile in ('uart_n','uart_e'):
            selected=[]
            for seed in SEEDS:
                options=[r for r in records if r['shape']==name and r['profile']==profile and r['seed']==seed and r.get('development_distribution','original')=='original']
                if options:
                    best=max(options,key=lambda r:key(r['selected']));selected.append(best);best_records.append(best)
            if not selected:continue
            values=[r['selected']['message_accuracy'] for r in selected]
            exact=sum(v==1 for v in values)
            passed=sum(r['selected']['message_accuracy']==1 and r['selected']['boundary_errors']==0 and r['selected']['invalid_accepted']==0 and r['selected']['background_accepted']==0 for r in selected)
            lines.append(f'| {name} | {profile} | {len(selected)}/6 | {100*min(values):.2f}–{100*max(values):.2f}% | {exact}/{len(selected)} | {passed}/{len(selected)} |')
    write_json(root/'best_development_checkpoints.json',best_records)
    extended=[r for r in records if r.get('development_distribution')=='extended']
    if extended:
        selected_extended=[]
        for identity in sorted({(r['shape'],r['profile'],r['seed']) for r in extended}):
            choices=[r for r in extended if (r['shape'],r['profile'],r['seed'])==identity]
            selected_extended.append(max(choices,key=lambda r:key(r['selected'])))
        write_json(root/'best_extended_development_checkpoints.json',selected_extended)
        write_json(root/'all_extended_development_trials.json',extended)
        lines+=['','## Extended development coverage','',
            'This independently generated development distribution adds long continuous payloads and cold mid-frame startup. Scores remain separate from original development and confirmation. Selection across recorded recipes is exploratory; it is not a matched comparison.','',
            '| Shape | Profile | Seeds | Exact-message range | Entire suite passes | Failing seeds |',
            '| --- | --- | ---: | ---: | ---: | --- |']
        for name,profile in sorted({(r['shape'],r['profile']) for r in selected_extended}):
            group=[r for r in selected_extended if (r['shape'],r['profile'])==(name,profile)]
            values=[r['selected']['message_accuracy'] for r in group]
            fails=[r['seed'] for r in group if not (r['selected']['message_accuracy']==1 and r['selected']['boundary_errors']==0 and r['selected']['invalid_accepted']==0 and r['selected']['background_accepted']==0)]
            lines.append(f"| {name} | {profile} | {len(group)}/6 | {100*min(values):.2f}–{100*max(values):.2f}% | {len(group)-len(fails)}/{len(group)} | {','.join(map(str,fails)) or 'none'} |")
        lines+=['','Selected recipes, epochs, conditions and source histories are in `best_extended_development_checkpoints.json`; all latest recipe results, including failed controls, are in `all_extended_development_trials.json`.','']
    lines+=['','Every selected checkpoint, recipe, six-seed failure and exposure count is recorded in `runs/connectivity01/best_development_checkpoints.json`. No missing profile or failed seed is silently counted as a pass.','',
        '## Causal findings','',
        '- A single ring inlet with registered feedback can learn substantial UART reception; the corresponding no-feedback control remained near zero under the paired auxiliary-training recipe.',
        '- Four upstream sources at the same ring inlet improve some initializations, especially with returns from both rings, but six-seed reliability remains unresolved.',
        '- In wider-inlet/both-return seed11 at 600 epochs, 20 extra events occur half a bit period from valid samples even though the auxiliary heads identify the correct phase at those ticks. That motivates the paired extra-return experiment; it is not a proof that the node count is insufficient.',
        '- A generic pulse-rearm diagnostic does not fix those isolated extra events. Its output policy was not adopted.',
        '- Leak learning and independent training banks are separately recorded recipe comparisons. Auxiliary timing heads are training tools only; deployed inference retains the same nine generic features, neural states and six event logits.','',
        '- Fixed middle-ring gains improve several seeds that struggled when those gains were trained. The declared portfolio gives every seed both off-chip recipes and retains its own selected weights. This changes the fitting program, not the physical graph.','',
        '## Resource limits','',
        'All physical graph costs are in `runs/connectivity01/all_shape_costs.json`. Counts include input, recurrent, return, inter-layer and readout connections. Learned weights/biases, leak storage, state banks, activation LUT and arithmetic are separate. The known numeric-storage subtotal excludes unsynthesized assembler/control and preprocessing/divider registers; it is not a measured silicon total. The confirmed 23.62% MAC reduction becomes 20.98% when the unchanged leak multiplications are included, and only 4.47% in the known numeric-storage subtotal because the shared LUT dominates. Wire length, placement, timing closure and area remain unmeasured.','',
        ]
    verified=[r for r in records if r.get('development_distribution')=='precision_v2']
    if verified:
        selected=[]
        for identity in sorted({(r['shape'],r['profile'],r['seed']) for r in verified}):
            selected.append(max((r for r in verified if (r['shape'],r['profile'],r['seed'])==identity),key=lambda r:key(r['selected'])))
        write_json(root/'best_verified_development_checkpoints.json',selected)
        lines+=['## Corrected broad development suite','',
            'Version 2 verifies every valid payload after an explicit observable cold-start synchronization interval. These are development results, not fresh confirmation. Interrupted version-1 precision and margin trials remain preserved and cannot establish an architecture limit. See [CONFIRMATIONS.md](CONFIRMATIONS.md) for the startup oracle audit.','',
            '| Shape | Profile | Completed seeds | All development gates pass | Remaining seed failures |','| --- | --- | ---: | ---: | --- |']
        for name,profile in sorted({(r['shape'],r['profile']) for r in selected}):
            rows=[r for r in selected if (r['shape'],r['profile'])==(name,profile)]
            fail=[r['seed'] for r in rows if not (r['selected']['message_accuracy']==1 and r['selected']['boundary_errors']==0 and r['selected']['invalid_accepted']==0 and r['selected']['background_accepted']==0)]
            lines.append(f"| {name} | {profile} | {len(rows)}/6 | {len(rows)-len(fail)}/{len(rows)} | {','.join(map(str,fail)) or 'none'} |")
        lines+=['','Exact conditions, selected recipes, checkpoints and exposure histories are in `best_verified_development_checkpoints.json`. Pending seeds are not counted as successful.','']
    fresh=root/'confirmations'/'uart_fixed01'
    confirmed=[json.loads(p.read_text()) for p in sorted((fresh/'results').glob('*/*/float_*/summary.json'))]
    if confirmed:
        lines+=['## First fresh UART confirmation: failed','',
            'The 600-epoch fixed-ring configurations were frozen before generating family 211000000. This first snapshot has float replay only; later float/integer replays are listed in CONFIRMATIONS.md. Its UART midstream payload contract was subsequently found invalid, so the whole suite cannot establish qualification. The numeric valid-timing counts below remain preserved, and no seed passed even the original replay. These samples are never reused for training.','',
            '| Seed | Valid timing messages exact | Worst valid condition | Boundary errors, all cases | Entire suite passes |',
            '| ---: | ---: | ---: | ---: | --- |']
        for r in confirmed:
            valid=[c for c in r['conditions'] if c['valid_messages']>=1000]
            lines.append(f"| {r['seed']} | {sum(c['exact_messages'] for c in valid)}/{sum(c['valid_messages'] for c in valid)} | {100*min(c['message_accuracy'] for c in valid):.2f}% | {sum(c['boundary_errors'] for c in r['conditions'])} | {r['pass_all']} |")
        lines+=['','Rare long-message and corner errors, exact-boundary failures, and startup/recovery failures all remain visible. New training/development families 223000000/224000000 address those coverage gaps; future confirmation must use a different fresh family.','']
    lines+=['## Return-path topology diagrams','']
    for name in shortlist:
        if 'port_fanin4' not in name:continue
        sh=make_shape(**graphs[name]);path=root/'figures'/f'{name}.png';diagram(sh,path)
        lines.extend([f'![{name}](runs/connectivity01/figures/{name}.png)',''])
    (ROOT/'PROGRESS.md').write_text('\n'.join(lines).rstrip()+'\n')
    print('Updated ongoing UART progress:',len(best_records),'selected development records; no new qualification claim.')

if __name__=='__main__':report(ROOT/'runs'/'connectivity01')
