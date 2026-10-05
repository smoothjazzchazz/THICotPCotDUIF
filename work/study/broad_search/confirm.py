"""Freeze once, confirm once, or replay saved inputs without new evidence.

python -m work.study.broad_search.confirm freeze
python -m work.study.broad_search.confirm run --directory <printed-directory>
python -m work.study.broad_search.confirm replay --directory <printed-directory>
"""
import argparse
import gzip
from work.study.shared.broad import *
from work.study.shared.resources import resources
from work.study.shared.comparison import collect_states, train_and_select, evaluate, emit_events, select_reference
from work.study.shared.signals import SignalStream, run_length_predictions
from work.study.mixed_leaks.mixed_leaks import mixed_candidates
from work.study.delay_chains.delay_chains import delay_candidates
from work.study.delay_chains.run_delay_chains import development_streams
from work.model.reservoir_model import ReservoirReceiver


def baseline_configs():
    for name,c in mixed_candidates():
        yield 'mixed_'+name,c
    for name,c in delay_candidates():
        if name in ('age_chain','level_chain'):
            yield name,c


def point_failures(results):
    failures=[]
    for condition,m in results.items():
        limits=(.95,.95,.95,.5) if condition=='clean' else ((.8,.8,.8,4) if condition=='aggregate' else (.75,.65,.65,6))
        for key,limit in zip(('event_precision','event_recall','unknown_recall'),limits[:3]):
            if m[key]<limit:failures.append(f'{condition}: {key} {m[key]:.6f} < {limit}')
        if m['false_events_per_1000_ticks']>limits[3]:failures.append(f'{condition}: false-event limit')
        if m['p95_latency_ticks'] is None or m['p95_latency_ticks']>5:failures.append(f'{condition}: latency limit')
    return failures


def freeze():
    # Confirmation seeds are never used by any development runner.
    previous=list((ROOT/'results/broad-confirmation').glob('*/test_streams.json.gz'))
    attempt=len(previous)+1
    if attempt>3:raise ValueError('Three confirmation attempts exhausted; objective remains incomplete')
    source=sorted((ROOT/'results/quantized-memory').glob('*/validation.json'))[-1]
    selected=next(r for r in json.loads(source.read_text()) if r['config']['nodes']==20 and r.get('bits')==8)
    # Pick the compact candidate on development, before looking at confirmation.
    if point_failures(selected['metrics']) or not selected['probes']['eligible']:
        raise ValueError('Candidate is not development-eligible')
    train,val=development_streams()
    c,r=selected['config'],selected['readout']
    validation=metrics(val,collect(val,c),r)
    if min(validation[k] for k in ('event_precision','event_recall','unknown_recall'))<.8:
        raise ValueError('Original validation requirements failed after quantization')
    training=training_diagnostics(c,collect(train,c))
    if not training['eligible']:raise ValueError('Training dynamics failed')
    seeds=[750000000+attempt*1000000+b*1000+i*100+j for b in range(12) for i in range(4) for j in range(2)]
    # Includes manifests, so a reserved attempt cannot silently be reused.
    for p in (ROOT/'results').rglob('*.json'):
        contents=p.read_text()
        if any(str(s) in contents for s in seeds):
            raise ValueError(f'Reserved confirmation seed already recorded in {p}')
    out=reserve('broad-confirmation','confirmation',{'attempt':attempt,'seeds':seeds,'patterns':48})
    save(out/'status.json',{'status':'preparing freeze; no confirmation inputs generated','attempt':attempt})
    baselines={}
    for name,config in baseline_configs():
        ts,vs=[collect_states(s,config) for s in train],[collect_states(s,config) for s in val]
        methods=train_and_select(train,ts,val,vs,config,include_reference=False)
        baselines[name]={'config':config.to_dict(),'methods':methods}
        print('freeze baseline',name,flush=True)
    float_source=next(row for row in json.loads(source.read_text()) if row['config']['nodes']==20 and row.get('bits','absent') is None)
    frozen={'schema':1,'attempt':attempt,'created_utc':datetime.now(timezone.utc).isoformat(),
            'seeds':seeds,'patterns':48,'source_sha256':sources(),
            'acceptance_plan_sha256':hashlib.sha256((ROOT/'broad_search/PLAN.md').read_bytes()).hexdigest(),
            'development_source':str(source),'development_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'candidate':selected,'float_control':float_source,'baselines':baselines,'reference':select_reference(val),
            'original_validation_quantized':validation,'training_diagnostics':training,
            'selection_reason':'20-sample 8-bit variant passes development/probes and uses fewer features and coefficient bits than 24-sample variants',
            'bootstrap_seed':20261005,'bootstrap_draws':10000,'confidence_level':1-.05/3}
    save(out/'freeze.json',frozen)
    save(out/'status.json',{'status':'frozen; no confirmation inputs generated','freeze_sha256':hashlib.sha256((out/'freeze.json').read_bytes()).hexdigest()})
    print(out,flush=True)


def evaluate_baseline(streams, entry):
    config=ReservoirConfig(**entry['config'])
    states=[collect_states(s,config) for s in streams]
    # Vectorized cached-state scoring; legacy step semantics and settings unchanged.
    predictions={}
    for name,setting in entry['methods'].items():
        receiver=ReservoirReceiver.from_dict(setting['receiver'])
        if name=='hamming':
            sc=[-np.not_equal((x>=0)[:,None,:], np.asarray(receiver.readout.prototypes)[None,:,:]).sum(axis=2) for x in states]
        else:
            values=[(x>=0).astype(float) if name=='linear_bits' else x/receiver.readout.scale for x in states]
            sc=[x@np.asarray(receiver.readout.weights).T+receiver.readout.bias for x in values]
        predictions[name]=[choose_classes(x,receiver.readout.class_ids,receiver.decision) for x in sc]
    return predictions


def summarize(streams, predictions, hold):
    result={}
    for i,k in enumerate(CONDITIONS):
        indices=[b*8+i*2+j for b in range(12) for j in range(2)]
        result[k]=measure([streams[j] for j in indices],[predictions[j] for j in indices],hold)[0]
    result['aggregate']=measure(streams,predictions,hold)[0]
    blocks=[measure(streams[b*8:(b+1)*8],predictions[b*8:(b+1)*8],hold)[0] for b in range(12)]
    return result,blocks


def verify_streaming(streams, xs, readout, config, expected):
    checkpoints=[]
    for s,x,y in zip(streams,xs,expected):
        receiver=Receiver(*json.loads(json.dumps([config,readout])))
        events=[]
        cuts={1, config['nodes']-1,len(s.levels)//2}
        for tick,u in enumerate(s.levels):
            if tick in cuts:
                receiver=Receiver.restore(json.loads(json.dumps(receiver.snapshot())))
            event=receiver.step(u)
            if not np.array_equal(receiver.state,x[tick]):raise AssertionError('state replay mismatch')
            if receiver.prediction!=y[tick]:raise AssertionError('decision replay mismatch')
            if event:events.append({**event,'emit_tick':tick})
        if events!=emit_events(y,readout['hold']):raise AssertionError('event replay mismatch')
        checkpoints.append({'seed':s.seed,'ticks':len(s.levels),'snapshot_ticks':sorted(cuts)})
    return checkpoints


def uncertainty(blocks, best_name, frozen):
    draws=np.random.default_rng(frozen['bootstrap_seed']).integers(0,12,(frozen['bootstrap_draws'],12))
    def f1(name):
        a=np.array([[m['matched_events'],m['predicted_events'],m['expected_events']] for m in blocks[name]])
        total=a[draws].sum(axis=1)
        return 2*total[:,0]/(total[:,1]+total[:,2])
    def unknown(name):
        a=np.array([[m['confusion'][3][3],sum(m['confusion'][3])] for m in blocks[name]])
        total=a[draws].sum(axis=1);return total[:,0]/total[:,1]
    baseline_names=[k for k in blocks if k not in ('candidate','float_control','run_length')]
    # Select the best baseline separately inside each draw; do not hide competitors.
    difference=f1('candidate')-np.max(np.array([f1(k) for k in baseline_names]),axis=0)
    alpha=.05/3
    def interval(a):return np.quantile(a,[alpha/2,1-alpha/2]).tolist()
    cycle='mixed_cycle3210/linear_full'
    return {'level':1-alpha,'draws':len(draws),'sampling_unit':'independent waveform seed block',
            'f1_gain_over_best_legacy':interval(difference),
            'unknown_gain_over_cycle3210':interval(unknown('candidate')-unknown(cycle)),
            'candidate_f1':interval(f1('candidate')),'candidate_unknown':interval(unknown('candidate')),
            'point_strongest_legacy':best_name,
            'block_f1_range':[min(m['event_f1'] for m in blocks['candidate']),max(m['event_f1'] for m in blocks['candidate'])]}


def execute(out, replay=False):
    frozen=json.loads((out/'freeze.json').read_text())
    for p,expected in frozen['source_sha256'].items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=expected:
            raise ValueError(f'Frozen source changed: {p}')
    freeze_hash=hashlib.sha256((out/'freeze.json').read_bytes()).hexdigest()
    dataset=out/'test_streams.json.gz'
    if replay:
        with gzip.open(dataset,'rt') as f:streams=[SignalStream(**s) for s in json.load(f)]
    else:
        if dataset.exists():raise ValueError('Confirmation already generated; use replay')
        save(out/'status.json',{'status':'confirmation attempt started','attempt':frozen['attempt'],'freeze_sha256':freeze_hash})
        streams=[]
        for index,seed in enumerate(frozen['seeds']):
            condition=list(CONDITIONS.values())[(index%8)//2]
            streams.append(make_stream(seed,frozen['patterns'],*condition))
        with gzip.open(dataset,'wt') as f:json.dump([asdict(s) for s in streams],f)
    c=frozen['candidate']['config'];r=frozen['candidate']['readout']
    xs=collect(streams,c);pred=predict(xs,r)
    predictions={'candidate':pred};holds={'candidate':r['hold']}
    predictions['float_control']=predict(xs,frozen['float_control']['readout'])
    holds['float_control']=frozen['float_control']['readout']['hold']
    for name,entry in frozen['baselines'].items():
        for method,ps in evaluate_baseline(streams,entry).items():
            key=name+'/'+method;predictions[key]=ps
            holds[key]=entry['methods'][method]['receiver']['hold_ticks']
        print('evaluated',name,flush=True)
    ref=frozen['reference'];holds['run_length']=ref['hold_ticks']
    predictions['run_length']=[run_length_predictions(s.levels,ref['tolerance']) for s in streams]
    results={};blocks={}
    for k,ps in predictions.items():results[k],blocks[k]=summarize(streams,ps,holds[k])
    basenames=[k for k in results if k not in ('candidate','float_control','run_length')]
    best=max(basenames,key=lambda k:results[k]['aggregate']['event_f1'])
    ci=uncertainty(blocks,best,frozen)
    failures=point_failures(results['candidate'])
    candidate=results['candidate']['aggregate']
    if candidate['event_f1']<results[best]['aggregate']['event_f1']+.03:failures.append('F1 improvement < .03')
    if ci['f1_gain_over_best_legacy'][0]<=0:failures.append('F1 uncertainty includes zero')
    if ci['unknown_gain_over_cycle3210'][0]<=0:failures.append('Unknown improvement uncertainty includes zero')
    eligible_unknown=[results[k]['aggregate']['unknown_recall'] for k in basenames if results[k]['aggregate']['event_f1']>=.75]
    if eligible_unknown and candidate['unknown_recall']<max(eligible_unknown)-.03:failures.append('Unknown regression versus strong legacy')
    checkpoints=verify_streaming(streams,xs,r,c,pred)
    result={'outcome':'confirmed improvement' if not failures else 'rejected','failures':failures,
            'attempt':frozen['attempt'],'freeze_sha256':freeze_hash,'dataset_sha256':digest([asdict(s) for s in streams]),
            'metrics':results,'blocks':blocks,'uncertainty':ci,'resources':resources(c,r),
            'replay_verified':True,'checkpoint_checks':checkpoints}
    if replay:
        previous=json.loads((out/'metrics.json').read_text())
        if digest(result)!=digest(previous):raise AssertionError('Replay differs from saved confirmation')
        replay_out=reserve('confirmation-replay','reproducibility',{'confirmation':str(out),'freeze_sha256':freeze_hash})
        save(replay_out/'verification.json',{'identical_metrics':True,'all_streams_reloaded':True,'dataset_sha256':result['dataset_sha256']})
        print(replay_out)
    else:
        save(out/'metrics.json',result)
        with gzip.open(out/'traces.json.gz','wt') as f:
            json.dump({'candidate_states':[x.tolist() for x in xs],
                       'candidate_scores':[x.tolist() for x in scores(xs,r)],
                       'predictions':{k:[np.asarray(p).tolist() for p in v] for k,v in predictions.items()},
                       'holds':holds},f)
        save(out/'status.json',{'status':result['outcome'],'attempt':frozen['attempt'],'failures':failures,'freeze_sha256':freeze_hash})
    if hashlib.sha256((out/'freeze.json').read_bytes()).hexdigest()!=freeze_hash:raise AssertionError('Freeze changed')
    print(result['outcome'],failures,'best legacy',best,flush=True)
    print('candidate',results['candidate'],flush=True)
    print('uncertainty',ci,flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run','replay']);parser.add_argument('--directory',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':freeze()
    else:
        if args.directory is None:parser.error('--directory required')
        execute(args.directory,args.action=='replay')

if __name__=='__main__':main()
