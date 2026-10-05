"""Render saved evidence; never fit models or generate confirmation waveforms."""
import argparse
import gzip
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from work.study.shared.broad import ROOT, save, reserve, build, digest
from work.study.shared.resources import resources


def label(c):
    if c['family']=='legacy':return c['name']
    fields=('family','nodes','degree','structure','rule','mode','seed','coupling','leak','bits','input','nonlinearity')
    return ' '.join(str(c[k]) for k in fields if k in c)


def ledger():
    groups=[('broad-screen','screen.json'),('broader-validation','validation.json'),('jitter-training','validation.json'),('quantized-memory','validation.json'),('memory-ablations','validation.json')]
    entries=[];lines=['# Experiment ledger','','All rows are saved, including failed and repeated configurations. Screening and','validation are development evidence; only the separately frozen confirmation','is new confirmation evidence. F1 values are not comparable across dataset groups.','']
    for group,filename in groups:
        for file in sorted((ROOT/'results'/group).glob('*/'+filename)):
            records=json.loads(file.read_text())
            lines+=['## '+group+' / '+file.parent.name,'',f'[Saved records](../results/{group}/{file.parent.name}/{filename})','', '| Configuration / readout | F1 | P / R / unknown | Outcome and reason |','| --- | ---: | --- | --- |']
            for i,row in enumerate(records):
                c=row['config'];r=row['readout'];p=row['probes']
                metrics=row.get('metrics',{}).get('aggregate',r['validation'])
                if 'event_f1' not in metrics:metrics=metrics['aggregate']
                reasons=[]
                if not p['decisions']['all_reset_ticks_correct']:reasons.append('nominal reset decisions')
                if p['decisions']['minimum_continuous_recall']<.9:reasons.append('prefix/offset decisions')
                if max(p['initial_tail_gaps'])>1/32:reasons.append('initial-state residue')
                if any(min(m['cross_min'])<=1e-12 for m in p['memory']):reasons.append('memory collision')
                if min(metrics[k] for k in ('event_precision','event_recall','unknown_recall'))<.8:reasons.append('P/R/unknown below .80')
                if 'metrics' in row:
                    from work.study.broad_search.confirm import point_failures
                    reasons+=point_failures(row['metrics'])
                status='rejected' if reasons else 'promising'
                entry={'run':str(file.parent),'index':i,'config':c,'purpose':json.loads((file.parent/'manifest.json').read_text())['purpose'],
                       'outcome':status,'reasons':reasons,'metrics':metrics,'resources':resources(c,r),
                       'explicit_unknown':row.get('explicit',7 in r['class_ids']), 'augmentation':row.get('augmentation'),
                       'coefficient_bits':row.get('bits',r.get('coefficient_bits'))}
                entries.append(entry)
                description=label(c)
                if 'augmentation' in row:description+=' aug='+str(row['augmentation'])
                if 'explicit' in row:description+=' explicit='+str(row['explicit'])
                if 'bits' in row:description+=' readout='+str(row['bits'])
                vals=' / '.join(f'{metrics[k]*100:.1f}%' for k in ('event_precision','event_recall','unknown_recall'))
                reason=', '.join(dict.fromkeys(reasons)) if reasons else 'passes this development screen; not confirmation'
                lines.append(f'| {description} | {metrics["event_f1"]*100:.1f}% | {vals} | {status}: {reason} |')
            lines.append('')
    return entries,lines


def boundary(config):
    """Post-selection diagnostic only, same deterministic duration grid as before."""
    records=[]
    for known,unknown in (((3,8),(8,8)),((8,3),(3,3))):
        for gap in range(1,6):
            for second in range(known[1]-2,known[1]+3):
                for shift in (-2,0,2):
                    states=[]
                    for first in (known[0]+shift,unknown[0]+shift):
                        levels=[0]*20+[1]*first+[0]*gap+[1]*second+[0]*4
                        m=build(config);x=np.asarray([m.step(u) for u in levels])
                        states.append(x[-4:,:config['nodes']])
                    distances=np.abs(states[0]-states[1]).sum(axis=1).tolist()
                    records.append({'known':known,'unknown':unknown,'first_shift':shift,'gap':gap,'second':second,'raw_state_distances':distances})
    return {'purpose':'post-selection limitation diagnostic; no retuning','cases':records,'cases_with_collision':sum(min(r['raw_state_distances'])==0 for r in records)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--confirmation',type=Path,required=True);args=parser.parse_args()
    confirmation=args.confirmation
    d=json.loads((confirmation/'metrics.json').read_text());f=json.loads((confirmation/'freeze.json').read_text())
    out=reserve('research-report','reproducibility',{'confirmation':str(confirmation),'dataset_sha256':d['dataset_sha256']})
    entries,lines=ledger()
    lines+=['## Confirmation attempts','','| Attempt | Outcome | Evidence |','| --- | --- | --- |']
    for path in sorted((ROOT/'results/broad-confirmation').glob('*/status.json')):
        status=json.loads(path.read_text());lines.append(f'| {status.get("attempt", "reserved")} | {status["status"]} | [Saved status](../results/broad-confirmation/{path.parent.name}/status.json) |')
    (ROOT/'broad_search/LEDGER.md').write_text('\n'.join(lines)+'\n')
    save(out/'ledger.json',entries)
    b=boundary(f['candidate']['config']);save(out/'boundary.json',b)
    legacy_resources={}
    for name,entry in f['baselines'].items():
        c=entry['config'];n=len(c['leak_shifts'])
        connections=sum(w!=0 for row in c['recurrent_taps']+c['feature_taps'] for _,w in row)
        for method,setting in entry['methods'].items():
            r=setting['receiver']['readout'];classes=len(r['class_ids'])
            parameters=classes*n if method=='hamming' else classes*(n+1)
            legacy_resources[name+'/'+method]={'state_bits':n*c['state_bits'],'feature_state_bits':8,
                'active_weighted_connections':connections,'reservoir_operations_per_tick_estimate':2*connections+3*n,
                'readout_parameters':parameters,'readout_parameter_bits':parameters*(1 if method=='hamming' else 64),
                'readout_operations_per_tick':classes*n,'readout_operation':'XOR/popcount input bits' if method=='hamming' else 'floating MAC',
                'median_latency_ticks':d['metrics'][name+'/'+method]['aggregate']['median_latency_ticks'],
                'status':'analytical accounting, not synthesis'}
    save(out/'resources.json',{'candidate':d['resources'],'historical_baselines':legacy_resources,
         'reference':{'state':'Python unbounded counters; no declared hardware widths','operations':'constant number of run updates; two three-term absolute-distance comparisons on pair completion','template_parameters':6,'status':'no synthesis or hardware bit-width claim'},
         'development':[{k:e[k] for k in ('run','index','config','resources')} for e in entries]})
    portable_readout={k:v for k,v in f['candidate']['readout'].items() if k!='validation'}
    model={'schema':1,'config':f['candidate']['config'],'readout':portable_readout, 'confirmation':str(confirmation), 'freeze_sha256':d['freeze_sha256'],'status':d['outcome']}
    # This portable load file is a source configuration; metrics stay under results/.
    save(ROOT/'polynomial_memory/compact_20_q8.json',model)
    with gzip.open(confirmation/'test_streams.json.gz','rt') as file:streams=json.load(file)
    with gzip.open(confirmation/'traces.json.gz','rt') as file:traces=json.load(file)
    best=d['uncertainty']['point_strongest_legacy']
    keys=['candidate',best,'level_chain/hamming','age_chain/linear_bits','mixed_uniform0/linear_full','run_length']
    names=['20-sample NGRC, int8','Mixed leaks, full','Level chain, Hamming','Age chain, sign-linear','Selected short memory','Run-length reference']
    fig,ax=plt.subplots(figsize=(10,4.8))
    x=np.arange(len(keys));width=.24
    for i,(metric,name) in enumerate([('event_f1','Known-event F1'),('event_precision','Known-event precision'),('unknown_recall','Unknown tick recall')]):
        ax.bar(x+(i-1)*width,[d['metrics'][k]['aggregate'][metric] for k in keys],width,label=name)
    ax.set_xticks(x,names,rotation=13,ha='right');ax.set_ylim(0,1.08);ax.set_ylabel('Fraction');ax.legend(ncol=3,loc='upper center');ax.grid(axis='y',alpha=.2)
    ax.set_title('Frozen confirmation: 4,608 patterns, identical streams for every listener')
    fig.tight_layout();fig.savefig(out/'comparison.png',dpi=160);fig.savefig(out/'comparison.svg');plt.close(fig)
    # Predetermined first mixed stream, not a favorable example chosen after scoring.
    index=6;s=streams[index];length=240;t=np.arange(length)
    fig,axes=plt.subplots(4,1,figsize=(11,6),sharex=True,gridspec_kw={'height_ratios':[1,1,1,2]})
    axes[0].step(t,s['levels'][:length],where='post');axes[0].set_ylabel('Pin')
    axes[1].step(t,s['targets'][:length],where='post',label='Intended');axes[1].step(t,traces['predictions']['candidate'][index][:length],where='post',alpha=.7,label='Prediction');axes[1].set_ylabel('Class');axes[1].legend(loc='upper right',ncol=2)
    scores=np.asarray(traces['candidate_scores'][index])[:length]
    for j,cls in enumerate(f['candidate']['readout']['class_ids']):axes[2].plot(t,scores[:,j],label=str(cls))
    axes[2].set_ylabel('Int score');axes[2].legend(loc='upper right',ncol=4)
    state=np.asarray(traces['candidate_states'][index])[:length,:20]
    axes[3].imshow(state.T,aspect='auto',interpolation='nearest',origin='lower',extent=[0,length,0,20],cmap='coolwarm',vmin=-1,vmax=1)
    axes[3].set_ylabel('Delay slot');axes[3].set_xlabel('Tick')
    fig.suptitle('First mixed-condition confirmation stream (fixed selection), first 240 ticks')
    fig.tight_layout();fig.savefig(out/'trace.png',dpi=160);fig.savefig(out/'trace.svg');plt.close(fig)
    (out/'waveform.txt').write_text(''.join(map(str,s['levels']))+'\n')
    representative={'seed':s['seed'],'levels':s['levels'],'targets':s['targets'],'windows':s['windows'],
                    'predictions':traces['predictions']['candidate'][index], 'scores':traces['candidate_scores'][index],
                    'raw_delay_states':np.asarray(traces['candidate_states'][index])[:,:20].tolist()}
    save(out/'representative_trace.json',representative)
    print(out,flush=True)
    print('ledger entries',len(entries),'boundary collisions',b['cases_with_collision'],len(b['cases']))

if __name__=='__main__':main()
