"""Derive qualifications and traceable demonstration configurations from frozen evidence."""
import csv,json,shutil
from pathlib import Path
from .run import ROOT,digest
from .shapes import PROFILES
from .train import write_json


def display_name(shape):
    if shape.endswith('readout16_fanin32_fast'):return 'Reduced readout (32 inputs/unit)'
    if shape.endswith('readout16_dense'):return 'Dense readout (48 inputs/unit)'
    return shape


def report():
    root=ROOT/'runs/connectivity01';qualified={};condition_rows=[];failures=[]
    for folder in sorted((root/'confirmations').iterdir()):
        result=folder/'joint_qualification.json'
        if not result.exists():continue
        joint=json.loads(result.read_text());frozen=json.loads((folder/'freeze.json').read_text());topologies=json.loads((folder/'topologies.json').read_text())
        for name,score in joint['per_shape'].items():
            if not name.endswith('/float') or not score['qualified']:continue
            shape=name.rsplit('/',1)[0];top=topologies[shape];qid=top['physical_sha256'];qscore=joint['per_shape'].get(shape+'/quantized',{})
            row=dict(shape=shape,physical_sha256=qid,confirmation=folder.name,seed_family=frozen['seed_family'],float=score,quantized=qscore,resources=top['configuration']['resources'],topology=top)
            old=qualified.get(qid)
            # For one physical graph, retain the strongest qualifying snapshot;
            # break equal repeatability in favor of its later independent audit.
            rank=lambda r:(min(r['float']['passes'].values()),sum(r['float']['passes'].values()),r['seed_family'])
            if old is None or rank(row)>rank(old):qualified[qid]=row
        for scope,base in [('fresh',folder),('regression',folder/'regression')]:
            ledger=json.loads((base/'ledger.json').read_text());assert len(ledger['completed'])==ledger['total']
            for entry in ledger['completed']:
                for condition in entry['conditions']:
                    condition_rows.append(dict(confirmation=folder.name,scope=scope,shape=entry['shape'],**condition))
                    if not condition['pass'] and entry['arithmetic'] in ('float','quantized'):
                        failures.append(dict(confirmation=folder.name,scope=scope,shape=entry['shape'],profile=entry['profile'],seed=entry['seed'],arithmetic=entry['arithmetic'],condition=condition['condition'],exact_messages=condition['exact_messages'],valid_messages=condition['valid_messages'],boundary_errors=condition['boundary_errors'],invalid_accepted=condition['invalid_accepted'],background_accepted=condition['background_accepted']))
    rows=sorted(qualified.values(),key=lambda r:(-min(r['float']['passes'].values()),r['resources']['macs_per_tick'],r['resources']['known_numeric_storage_bytes'],r['resources']['activation_depth']))
    for name,table in [('qualified_per_condition_v3.csv',condition_rows),('qualification_failures_v3.csv',failures)]:
        if table:
            with (root/name).open('w') as f:
                fields=list(dict.fromkeys(k for row in table for k in row));writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(table)
    lines=['# Independently confirmed physical shapes','',f'**{len(rows)} distinct physical shape(s) qualify under the unchanged float gates.** '+('The search for two is not finished.' if len(rows)<2 else 'Both required shapes are established.'),'',
        'Qualification requires the same five of six training seeds per profile to pass every fresh condition and the prior failure regression. Every complete message and boundary must be exact, with no extra accepted messages on the declared invalid/background suite. Float and Q3.12 are scored separately. Numeric weight/leak variants are not counted as additional shapes.','',
        '| Shape | UART 8N1 | UART 8E1 | I2C | SPI0 | SPI1 | SPI2 | SPI3 | MACs/sample | Parameters |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for index,row in enumerate(rows,1):
        counts=row['float']['passes'];c=row['resources'];lines.append(f"| {index}. {display_name(row['shape'])} | "+' | '.join(f'{counts[p]}/6' for p in PROFILES)+f" | {c['macs_per_tick']} | {c['parameters']} |")
    for index,row in enumerate(rows,1):
        folder=root/'confirmations'/row['confirmation'];frozen=json.loads((folder/'freeze.json').read_text());joint=json.loads((folder/'joint_qualification.json').read_text());shape=row['shape']
        passes={p:sorted(r['seed'] for r in joint['per_seed'] if r['shape']==shape and r['profile']==p and r['arithmetic']=='float' and r['joint_pass']) for p in PROFILES}
        common=set.intersection(*(set(passes[p]) for p in PROFILES));demo=root/'qualified_demonstrations_v3'/row['confirmation']/row['physical_sha256'][:12];demo.mkdir(parents=True,exist_ok=True);entries=[]
        for profile in PROFILES:
            seed=min(common or set(passes[profile]));e=next(e for e in frozen['entries'] if (e['shape'],e['profile'],e['seed'])==(shape,profile,seed));source=folder/e['weight_path'];target=demo/(profile+'.npz')
            assert digest(source)==e['weight_sha256']
            if target.exists():assert digest(target)==digest(source)
            else:shutil.copy2(source,target)
            quantized_pass=next(r['joint_pass'] for r in joint['per_seed'] if (r['shape'],r['profile'],r['seed'],r['arithmetic'])==(shape,profile,seed,'quantized'))
            entries.append(dict(profile=profile,seed=seed,weight_file=target.name,weight_sha256=digest(target),construction=e['construction'],configured_leaks=e['configured_leaks'],float_joint_pass=True,quantized_joint_pass=quantized_pass))
        write_json(demo/'manifest.json',dict(shape=shape,physical_sha256=row['physical_sha256'],confirmation=row['confirmation'],frozen_source=str((folder/'source').resolve()),entries=entries,selection='lowest seed that jointly passes every profile, if available; otherwise lowest passing seed per profile; demonstration configurations, not production weights'))
        write_json(demo/'topology.json',row['topology']);row['demonstration_directory']=str(demo)
        q=row['quantized'];counts=q.get('passes',{});lines += ['',f'## {index}. {display_name(shape)}','',f'Exact configuration: `{shape}`.','',
            f"Frozen confirmation: `{row['confirmation']}`, fresh family {row['seed_family']}. Q3.12 qualification: **{'passes' if q.get('qualified') else 'does not pass'}**; counts in profile order UART-N, UART-E, I2C, SPI0–3: "+', '.join(f'{counts.get(p,0)}/6' for p in PROFILES)+'.','',
            'Remaining float seed failures: '+('; '.join(f"{p}: "+','.join(map(str,sorted(set((11,29,47,71,101,131))-set(passes[p])))) for p in PROFILES if len(passes[p])<6) or 'none')+'.','',
            'Remaining Q3.12 seed failures: '+('; '.join(f"{p}: "+','.join(str(r['seed']) for r in joint['per_seed'] if (r['shape'],r['profile'],r['arithmetic'])==(shape,p,'quantized') and not r['joint_pass']) for p in PROFILES if counts.get(p,0)<6) or 'none')+'.','',
            f"[Fixed topology and demonstration weights](runs/connectivity01/qualified_demonstrations_v3/{row['confirmation']}/{row['physical_sha256'][:12]}/manifest.json). These are separately learned protocol configurations of one fixed physical graph. Every other seed, including failures, remains in the frozen confirmation.",'',
            f"![Actual directed connections](runs/connectivity01/figures/{shape}.png)",'',
            '```sh',f'OPENBLAS_NUM_THREADS=1 "$PY" -B -m work.study.hero_shape_connectivity.replay_confirmation_v3 evaluate --label {row["confirmation"]} --workers 6','```']
    lines+=['','Set `PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python` and run from the repository root. Replay imports each confirmation’s immutable source and verifies its hashes. Replaying an existing family reproduces evidence; it does not create new independent evidence.','',
        '[Per-condition results, both arithmetic modes and diagnostic controls](runs/connectivity01/qualified_per_condition_v3.csv); [all qualification failures](runs/connectivity01/qualification_failures_v3.csv); [training trials and failed continuations](runs/connectivity01/training_trials.csv).','',
        '[ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md) gives equations, routes, operation counts, modeled storage, scheduling and exclusions. [READOUT_ROUTING_COMPARISON.md](READOUT_ROUTING_COMPARISON.md) explains the paired physical-edge reduction and retained training failures. [PAIRED_READOUT_RESULT.md](PAIRED_READOUT_RESULT.md) applies the preregistered cost/recovery threshold to all six paired seeds. [FOLLOWUPS.md](FOLLOWUPS.md) preserves the hypotheses and practical thresholds; [COVERAGE_V10.md](COVERAGE_V10.md) explains the startup-coverage finding; [REPRODUCE.md](REPRODUCE.md) gives training/resume commands and source manifests.','',
        'This establishes the declared receive-model tests at known nominal speed with a shared divider and separate protocol weights. It does not establish RTL, routed area/frequency, electrical compliance, on-chip training or a complete waveform-response system. USB/Ethernet extensions are untested. `clock_hz=0`; no reference-design project gate is changed.']
    write_json(root/'qualified_shapes_v3.json',dict(physical_shape_count=len(rows),rank_order=rows,criterion='worst-profile float repeatability, then modeled computation/storage and activation depth; distinct literal physical definitions'))
    (ROOT/'QUALIFIED_SHAPES.md').write_text('\n'.join(lines).rstrip()+'\n');print('Qualified physical shapes',len(rows))


if __name__=='__main__':report()
