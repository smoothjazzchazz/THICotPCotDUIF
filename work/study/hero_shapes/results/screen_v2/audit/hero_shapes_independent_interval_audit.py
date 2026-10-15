import itertools,json
from pathlib import Path
from work.study.hero_shapes.models import simulate
from work.study.hero_shapes.stimuli import FAMILIES,expand_runs,known_matches
root=Path('work/study/hero_shapes/results/screen_v2')
results=[]
for family,definition in FAMILIES.items():
    config=json.loads((root/family/'stream_intervals/config.json').read_text())
    variants=[]
    for label,template in definition['templates'].items():
        for scale in definition['scales']:
            nominal=tuple(n*scale for n in template)
            for delta in itertools.product((-1,0,1),repeat=len(nominal)):
                variants.append((tuple(n+d for n,d in zip(nominal,delta)),label,'all_jitter'))
            for index in range(len(nominal)):
                for delta in (-2,2):
                    runs=list(nominal);runs[index]+=delta
                    if min(runs)<2 or any(n>=20 for n in runs[1::2]):continue
                    assert not known_matches(family,runs)
                    variants.append((tuple(runs),None,'one_run_outside_envelope'))
            variants.extend([( (2,2)+nominal,None,'prefix'),(nominal+(2,2),None,'suffix'),(nominal+(19,)+nominal,None,'missing_delimiter')])
    counts={};failures=[]
    for chunk_start in range(0,len(variants),64):
        chunk=variants[chunk_start:chunk_start+64]
        samples=[0]*24;expected=[]
        for runs,label,condition in chunk:
            raw_start=len(samples);samples+=expand_runs(runs);raw_end=len(samples);samples += [0]*24
            expected.append((label,condition,raw_start+2,raw_end+21,runs))
        trace=simulate(samples,config)
        events=[r['event'] for r in trace if r['event']]
        if len(events)!=len(expected): failures.append(dict(reason='event_count',expected=len(expected),observed=len(events)))
        for event,(label,condition,start,end,runs) in zip(events,expected):
            counts[condition]=counts.get(condition,0)+1
            if (event.class_id,event.start_tick,event.decision_tick)!=(label,start,end):
                failures.append(dict(reason='event',runs=runs,condition=condition,expected=[label,start,end],observed=vars(event)))
    cold_count=0
    for template in definition['templates'].values():
        for scale in definition['scales']:
            burst=expand_runs(tuple(n*scale for n in template))
            for cut in range(len(burst)):
                remaining=burst[cut:];recovery_start=len(remaining)+24
                samples=remaining+[0]*24+expand_runs(definition['templates'][0])+[0]*24
                events=[r['event'] for r in simulate(samples,config) if r['event']]
                early=[e for e in events if e.decision_tick<recovery_start and e.class_id is not None]
                recovery=[e for e in events if e.start_tick==recovery_start+2 and e.class_id==0]
                cold_count+=1
                if early or len(recovery)!=1:failures.append(dict(reason='startup',cut=cut,scale=scale,events=[vars(e) for e in events]))
    results.append(dict(family=family,config_threshold=config['minimum_score'],config_margin=config['minimum_margin'],counts=counts,startup_cut_cases=cold_count,failures=failures))
Path('/tmp/hero_shapes_independent_interval_audit.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
assert all(not row['failures'] for row in results)
