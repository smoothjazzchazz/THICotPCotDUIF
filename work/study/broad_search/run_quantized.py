"""Quantization and matched legacy training controls on development only."""
from work.study.shared.broad import *
from work.study.shared.resources import resources
from work.study.broad_search.run_robust import robust_select
from work.study.delay_chains.run_delay_chains import development_streams
from work.study.delay_chains.delay_chains import delay_candidates


def main():
    source=sorted((ROOT/'results/jitter-training').glob('*/validation.json'))[-1]
    candidates=[r for r in json.loads(source.read_text()) if r['augmentation'] and r['explicit'] and r['config']['nodes'] in (20,24)]
    groups=development(36000000,24,48)
    original,val=development_streams();train=original+sum(development(33000000,8).values(),[])
    selection={'original':val,**development(34000000,6)}
    out=reserve('quantized-memory','validation',{'source':str(source),'source_hash':hashlib.sha256(source.read_bytes()).hexdigest(),'bits':[8,10,12,16]})
    save(out/'datasets.json',{k:[asdict(s) for s in ss] for k,ss in groups.items()})
    rows=[]
    for record in candidates:
        c=record['config'];xs={k:collect(ss,c) for k,ss in groups.items()}
        for bits in (None,8,10,12,16):
            r=record['readout'] if bits is None else quantize(record['readout'],bits)
            result={k:metrics(ss,xs[k],r) for k,ss in groups.items()}
            result['aggregate']=metrics(sum(groups.values(),[]),sum(xs.values(),[]),r)
            p=probe(c,r)
            row={'config':c,'readout':r,'probes':p,'metrics':result,'resources':resources(c,r), 'bits':bits}
            rows.append(row);save(out/'validation.json',rows)
            print(c['nodes'],bits,'probe',p['eligible'],{k:[round(m[x],3) for x in ('event_precision','event_recall','unknown_recall','event_f1')] for k,m in result.items()},flush=True)
    for name,config in delay_candidates():
        c={'family':'legacy','name':name,'reservoir':config.to_dict(),'nodes':16}
        r=robust_select(train,collect(train,c),selection,{k:collect(ss,c) for k,ss in selection.items()})
        xs={k:collect(ss,c) for k,ss in groups.items()}
        result={k:metrics(ss,xs[k],r) for k,ss in groups.items()}
        result['aggregate']=metrics(sum(groups.values(),[]),sum(xs.values(),[]),r)
        p=probe(c,r)
        row={'config':c,'readout':r,'probes':p,'metrics':result,'resources':resources(c,r)}
        rows.append(row);save(out/'validation.json',rows)
        print(name,'augmented explicit','probe',p['eligible'], {k:[round(m[x],3) for x in ('event_precision','event_recall','unknown_recall','event_f1')] for k,m in result.items()},flush=True)
    print(out)

if __name__=='__main__':main()
