"""Strict confirmation accounting; partial-profile success is never full success."""
import csv
import json
from .run import ROOT
from .shapes import PROFILES,SEEDS
from .train import write_json


def summarize(root):
    outcomes=[];conditions=[]
    audit=json.loads((root/'startup_payload_audit.json').read_text()) if (root/'startup_payload_audit.json').exists() else {'cases':[]}
    for comparison in sorted((root/'confirmations').iterdir()):
        if not (comparison/'freeze.json').exists():continue
        freeze=json.loads((comparison/'freeze.json').read_text())
        policy=comparison/'startup_semantics.json'
        v3=policy.exists() and json.loads(policy.read_text()).get('version')==3
        joint_file=comparison/'joint_qualification.json'
        joint_result=json.loads(joint_file.read_text()) if joint_file.exists() else None
        topology=json.loads((comparison/'topologies.json').read_text()) if (comparison/'topologies.json').exists() else {}
        records=[json.loads(p.read_text()) for p in (comparison/'results').glob('*/*/*/summary.json')]
        for r in records:
            for c in r['conditions']:conditions.append(dict(comparison=comparison.name,shape=r['shape'],**c))
        for shape in sorted({e['shape'] for e in freeze['entries']}):
            for arithmetic in ('float','quantized'):
                selected=[r for r in records if r['shape']==shape and r['arithmetic']==arithmetic]
                per_profile={}
                for profile in PROFILES:
                    rows=[r for r in selected if r['profile']==profile]
                    invalid_reference=[c for c in audit['cases'] if c['profile']==profile and c['mismatches'] and '/confirmations/'+comparison.name+'/data/' in c['path']]
                    per_profile[profile]=dict(evaluated=len(rows),passed=sum(r['pass_all'] for r in rows),
                        failed_seeds=[r['seed'] for r in rows if not r['pass_all']],
                        missing_seeds=sorted(set(SEEDS)-{r['seed'] for r in rows}),
                        reference_payload_contract_valid=not bool(invalid_reference))
                    if v3:
                        cell=per_profile[profile];cell['fresh_passed']=cell['passed']
                        combined=[] if joint_result is None else [r for r in joint_result['per_seed'] if (r['shape'],r['profile'],r['arithmetic'])==(shape,profile,arithmetic)]
                        cell['passed']=sum(r['joint_pass'] for r in combined)
                        cell['failed_seeds']=[r['seed'] for r in combined if not r['joint_pass']]
                        cell['missing_joint_seeds']=sorted(set(SEEDS)-{r['seed'] for r in combined})
                        cell['joint_fresh_regression_required']=True
                joint=[seed for seed in SEEDS if all(any(r['profile']==p and r['seed']==seed and r['pass_all'] for r in selected) for p in PROFILES)]
                qualifies=all(v['evaluated']==6 and v['passed']>=5 and v['reference_payload_contract_valid'] for v in per_profile.values())
                if v3:
                    joint=[] if joint_result is None else [s for s in SEEDS if all(any(r['shape']==shape and r['profile']==p and r['seed']==s and r['arithmetic']==arithmetic and r['joint_pass'] for r in joint_result['per_seed']) for p in PROFILES)]
                    qualifies=qualifies and joint_result is not None
                outcomes.append(dict(comparison=comparison.name,shape=shape,arithmetic=arithmetic,
                    physical_sha256=topology.get(shape,{}).get('physical_sha256',shape),
                    mandatory_profiles=list(PROFILES),per_profile=per_profile,joint_all_profile_passing_seeds=joint,
                    qualified=qualifies,scope='all seven mandatory profiles, all original gates, at least five of six per profile; v3 requires same seeds across fresh and prior regression; missing results never pass'))
    write_json(root/'qualification_summary.json',outcomes)
    if conditions:
        with (root/'all_confirmation_conditions.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in conditions for k in r)));w.writeheader();w.writerows(conditions)
    print('Full float-qualified physical shapes:',len({r['physical_sha256'] for r in outcomes if r['arithmetic']=='float' and r['qualified']}))

if __name__=='__main__':summarize(ROOT/'runs'/'connectivity01')
