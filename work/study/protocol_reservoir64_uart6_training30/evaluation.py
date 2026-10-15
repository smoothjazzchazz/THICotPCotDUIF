"""Final-only independent waveform confirmation; condition files permit resumption."""
import json
from pathlib import Path
from work.model.stream_reservoir import StreamReceiver, load_weights
from work.study.protocol_reservoir64.profiles import load_config
from work.study.protocol_reservoir64.evaluation import save_trace
from .costs import resource_cost
from work.study.protocol_reservoir64.usb_emitter import training_gate
from .data import PROFILES, cases
from .training import SEEDS, write_json
from .metrics import score_case, aggregate


def evaluate_job(job):
    output, profile, variant, mode, control = job
    output = Path(output)
    final = output / 'final'
    directory = final / 'conditions' / f'{profile}_{variant}_{mode}_{control}'
    directory.mkdir(parents=True, exist_ok=True)
    w, metadata = load_weights(output / 'models' / profile / variant / 'selected.npz')
    config = load_config(output, profile)
    seed = metadata['seed']
    rows = []
    for case in cases(profile, 'final'):
        if control != 'trained' and case['name'] not in ('phrase','every_byte','repeated_patterns'):
            continue
        path = directory / f"{case['name']}.json"
        if path.exists():
            rows.append(json.loads(path.read_text()))
            continue
        receiver = StreamReceiver(w, mode, margin=config['decision_margin'], control=control)
        metrics, result = score_case(profile, case, receiver, config)
        row = dict(condition=case['name'], valid=case['valid'], stimulus_seed=case['seed'], **metrics)
        if control == 'trained' and case['name'] in ('phrase','fast_clock','malformed_recovery','idle_and_disturbance','repeated_patterns','gapped_frames'):
            trace_root = final / 'traces' / variant
            destination = trace_root / f"{profile}_{mode}_{seed}_{case['name']}"
            if destination.exists():
                # Only an interrupted, uncommitted condition may have a partial trace.
                import shutil
                shutil.rmtree(destination)
            save_trace(trace_root, profile, mode, seed, case, result, metrics)
        write_json(path, row)
        rows.append(row)
        print(json.dumps(dict(profile=profile, variant=variant, mode=mode, control=control,
            condition=case['name'], exact=metrics['bytes']['exact'], recovered=metrics['bytes']['recovered'],
            symbol_errors=metrics['symbols']['totals']['errors'], passes=metrics['passes'])),flush=True)
    record = dict(profile=profile, variant=variant, seed=seed, selected_epoch=metadata['epoch'], mode=mode,
        control=control, qualified=all(r['passes'] for r in rows if r['valid']),
        summary=aggregate(rows), conditions=rows)
    filename = f'{profile}_{variant}_{mode}' + ('' if control == 'trained' else '_' + control)
    write_json(final / f'{filename}.json',record)
    return filename


def evaluate(output, workers):
    from .run import parallel, sha
    final = Path(output) / 'final'; final.mkdir(exist_ok=True)
    manifest = final / 'cases.json'
    generated = {p:[dict(c,payload=list(c['payload'])) for c in cases(p,'final')] for p in PROFILES}
    if manifest.exists():
        assert json.loads(manifest.read_text()) == generated
    else:
        write_json(manifest,generated)
    jobs = [(str(output),p,v,m,'trained') for p in PROFILES
            for v in [*(f'seed_{s}' for s in SEEDS),'previous_recipe_11'] for m in ('float','quantized')]
    jobs += [(str(output),p,'seed_11',m,c) for p in PROFILES for m in ('float','quantized')
             for c in ('disabled','no_recurrence')]
    parallel(evaluate_job,jobs,workers)
    from .validation import i2c_fresh, cold_idle, final_timing_audit
    final_timing_audit(output)
    i2c_fresh(output)
    cold_idle(output)
    cold = json.loads((final/'cold_idle.json').read_text())
    models = [json.loads((final / f'{p}_{v}_{m}.json').read_text()) for _,p,v,m,c in jobs if c=='trained']
    qualification = {p:all(r['qualified'] and not any(c['false_events'] for c in cold if c['profile']==p and c['variant']==r['variant'] and c['mode']==r['mode']) for r in models if r['profile']==p and r['variant'].startswith('seed_')) for p in PROFILES}
    write_json(final/'summary.json',dict(qualification=qualification, models=[{k:r[k] for k in (
        'profile','variant','seed','selected_epoch','mode','qualified','summary')} for r in models]))
    write_json(final/'usb_status.json',training_gate(all(qualification.values())))
    write_json(final/'cost.json',resource_cost(output))
    write_json(final/'manifest.json',{str(p.relative_to(final)):sha(p) for p in sorted(final.rglob('*'))
                                    if p.is_file() and p.name!='manifest.json'})
