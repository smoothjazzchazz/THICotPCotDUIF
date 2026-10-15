"""Keep enlarged-development readout diagnostics separate from earlier scores."""
import json
from .run import ROOT
from .train import key,write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';rows=[]
    lines=['# Enlarged-development boundary refinement','',
        'Ongoing training diagnostic, not fresh confirmation or a topology ranking. All original precision_v2 cases remain; four independent1000-message timing cases add to6304 valid groups per UART profile. Family361000000 is development only. The failed full_shape_v2a confirmation remains untouched.','',
        'Only the existing STOP affine row changes. Causal state transitions and the other five output rows are fixed. All seeds use their own recorded source. Sources already passing the enlarged suite receive zero additional training.','',
        '| Profile | Seed | Completed rounds | Source exact /6304 | Source boundaries | Selected exact /6304 | Selected boundaries | Full enlarged suite passes |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for folder in sorted((root/'models'/'phase_stop_margin_v4').glob('*/*/*')):
        history=folder/'history.jsonl'
        if not history.exists():continue
        h=[json.loads(s) for s in history.read_text().splitlines()];original=h[0];selected=max((r for r in h if 'dev_loss' in r),key=key)
        blocks=sorted(folder.glob('block_*.json'));done=bool(blocks);b=json.loads(blocks[-1].read_text()) if blocks else None
        passed=done and selected['message_accuracy']==1 and not any(selected[k] for k in ('boundary_errors','invalid_accepted','background_accepted'))
        row=dict(profile=folder.parent.name,seed=int(folder.name),completed=done,round=h[-1]['epoch'],source=original,selected=selected,pass_enlarged=passed,block=str(blocks[-1]) if blocks else None)
        rows.append(row)
        lines.append(f"| {row['profile']} | {row['seed']} | {b['epochs'] if done else str(h[-1]['epoch'])+' (running)'} | {original['exact_messages']} | {original['boundary_errors']} | {selected['exact_messages']} | {selected['boundary_errors']} | {passed} |")
    lines+=['','Every round preserves training support, solver status, parameters and exposure. Zero retained training violations does not imply zero independent errors, nor prove that a different state representation cannot work. Selected cached-readout results must agree with full scalar receiver replay.','',
        'No confirmation gate, timing tolerance, pulse policy, invalid-rejection rule or six-seed criterion has changed. Enlarged scores are not directly compared with earlier2304-group development scores.','']
    write_json(root/'corner_refinement_progress.json',rows);(ROOT/'CORNER_REFINEMENT.md').write_text('\n'.join(lines).rstrip()+'\n')
