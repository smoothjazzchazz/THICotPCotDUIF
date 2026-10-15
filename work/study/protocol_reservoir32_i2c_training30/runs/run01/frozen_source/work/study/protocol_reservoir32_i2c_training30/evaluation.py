"""Paired fresh final I2C cases for reduced and frozen original receiver sizes."""
import json
import shutil
from pathlib import Path
import numpy as np
from .receiver import StreamReceiver, load_weights, NODES, MASK
from work.model.stream_reservoir import StreamReceiver as Receiver64, load_weights as load64
from work.study.protocol_reservoir64_training30.metrics import score_case, aggregate
from work.study.protocol_reservoir64.evaluation import save_trace
from .data import cases,load_config
from .training import write_json


def evaluate_job(job):
    output,size,variant,mode,control=job;output=Path(output)
    loader,receiver=(load_weights,StreamReceiver) if size==32 else (load64,Receiver64)
    folder=output/'models/i2c'/variant if size==32 else output/'baseline64'/variant
    w,metadata=loader(folder/'selected.npz');config=load_config(output,'i2c')
    name=f'n{size}_{variant}_{mode}_{control}'
    directory=output/'final/conditions'/name;directory.mkdir(parents=True,exist_ok=True)
    rows=[]
    for case in cases('i2c','final'):
        if control!='trained' and case['name'] not in ('phrase','every_byte','repeated_patterns'):continue
        path=directory/f"{case['name']}.json"
        if path.exists():rows.append(json.loads(path.read_text()));continue
        rx=receiver(w,mode,margin=config['decision_margin'],control=control)
        metrics,result=score_case('i2c',case,rx,config)
        row=dict(condition=case['name'],valid=case['valid'],stimulus_seed=case['seed'],**metrics)
        if control=='trained' and case['name'] in ('phrase','fast_clock','malformed_recovery','idle_and_disturbance'):
            trace_root=output/'final/traces'/f'n{size}_{variant}'
            dest=trace_root/f"i2c_{mode}_{metadata['seed']}_{case['name']}"
            if dest.exists():shutil.rmtree(dest) # Only interrupted, uncommitted condition traces.
            save_trace(trace_root,'i2c',mode,metadata['seed'],case,result,metrics)
        write_json(path,row);rows.append(row)
        print(json.dumps(dict(model=name,condition=case['name'],exact=metrics['bytes']['exact'],
            recovered=metrics['bytes']['recovered'],event_errors=metrics['symbols']['totals']['errors'],passes=metrics['passes'])),flush=True)
    record=dict(nodes=size,variant=variant,seed=metadata['seed'],mode=mode,control=control,
        selected_epoch=metadata['epoch'],qualified=all(r['passes'] for r in rows if r['valid']),
        summary=aggregate(rows),conditions=rows)
    write_json(output/'final'/f'{name}.json',record)
    return name


def costs():
    return dict(architectures=[dict(nodes=n,recurrent_connections=4*n,density=4/n,
        learned_coefficients=n*6+4*n+n+8*n+8,packed_int16_coefficient_bytes=2*(19*n+8),
        packed_int16_state_double_buffer_bytes=n*4,sparse_MAC_per_tick=18*n,
        actual_dense_numpy_MAC_per_tick=n*6+n*n+8*n,leak_products=2*n,nonlinear_evaluations=n,
        packed_fixed_leak_bytes=2*n,packed_recurrent_index_bits=4*n*(5 if n==32 else 6)) for n in (32,64)],
        unchanged=dict(input_features=6,event_classes=8,packed_tanh_lut_bytes=8194,
            i2c_storage_bytes=4096,scheduled_command_capacity=512,packed_scheduler_bytes=12800,
            setup_deadline_ticks=6,clock_low_high_ticks=[8,12],physical_clock_hz=None),
        notes=['Logical packing estimates; NumPy actually retains dense float64 and int64 coefficient arrays.',
               'The integer LUT is int64 in NumPy (32776 bytes); scratch, logs and Python overhead are not a hardware storage model.',
               'Controller, previous levels, edge ages, timestamps and last decision remain unchanged.',
               'One update per abstract tick is assumed; no hardware schedule, silicon frequency, area or power was measured.'])


def evaluate(output,workers):
    from .run import VARIANTS,parallel,sha
    final=output/'final';final.mkdir(exist_ok=True)
    generated=[dict(c,payload=list(c['payload'])) for c in cases('i2c','final')]
    if (final/'cases.json').exists():assert json.loads((final/'cases.json').read_text())==generated
    else:write_json(final/'cases.json',generated)
    jobs=[(str(output),n,v,m,'trained') for n in (32,64) for v in VARIANTS for m in ('float','quantized')]
    jobs += [(str(output),32,'seed_11',m,c) for m in ('float','quantized') for c in ('disabled','no_recurrence')]
    parallel(evaluate_job,jobs,workers)
    records=[json.loads((final/f'n{n}_{v}_{m}_{c}.json').read_text()) for _,n,v,m,c in jobs]
    qualified={str(n):all(r['qualified'] for r in records if r['nodes']==n and r['control']=='trained'
                       and r['variant'].startswith('seed_')) for n in (32,64)}
    write_json(final/'summary.json',dict(qualification_by_node_count=qualified,
        models=[{k:r[k] for k in ('nodes','variant','seed','mode','control','selected_epoch','qualified','summary')} for r in records]))
    write_json(final/'cost.json',costs())
    write_json(final/'scope.json',dict(protocol='i2c',uart_training_and_evaluation=False,usb_fit_steps=0,
        usb_status='excluded; no UART qualification or required protocol sources'))
    write_json(final/'manifest.json',{str(p.relative_to(final)):sha(p) for p in sorted(final.rglob('*'))
                                   if p.is_file() and p.name!='manifest.json'})
