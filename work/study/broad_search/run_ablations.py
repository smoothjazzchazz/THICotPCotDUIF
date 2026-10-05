"""Matched mechanism controls for the compact 20-sample candidate."""
from work.study.shared.broad import *
from work.study.broad_search.run_robust import robust_select
from work.study.delay_chains.run_delay_chains import development_streams
from work.study.shared.resources import resources


def main():
    train,val=development_streams();train+=sum(development(33000000,8).values(),[])
    groups={'original':val,**development(34000000,6)}
    check=development(36000000,24,48)
    variants=[({'family':'polynomial','nodes':20,'degree':1},True),
              ({'family':'polynomial','nodes':20,'degree':2},False),
              ({'family':'polynomial','nodes':20,'degree':2,'input':'age'},True)]
    out=reserve('memory-ablations','validation',variants);rows=[]
    for c,explicit in variants:
        r=robust_select(train,collect(train,c),groups,{k:collect(ss,c) for k,ss in groups.items()},explicit)
        xs={k:collect(ss,c) for k,ss in check.items()}
        result={k:metrics(ss,xs[k],r) for k,ss in check.items()}
        result['aggregate']=metrics(sum(check.values(),[]),sum(xs.values(),[]),r)
        p=probe(c,r)
        row={'config':c,'explicit':explicit,'readout':r,'metrics':result,'probes':p,'resources':resources(c,r)}
        rows.append(row);save(out/'validation.json',rows)
        print(c,explicit,'probe',p['eligible'],{k:[round(m[x],3) for x in ('event_precision','event_recall','unknown_recall','event_f1')] for k,m in result.items()},flush=True)
    source=sorted((ROOT/'results/quantized-memory').glob('*/validation.json'))[-1]
    row=next(r for r in json.loads(source.read_text()) if r['config']['nodes']==20 and r.get('bits','not') is None)
    c=row['config'];xs={k:collect(ss,c) for k,ss in check.items()}
    for bits in (4,6):
        r=quantize(row['readout'],bits)
        result={k:metrics(ss,xs[k],r) for k,ss in check.items()}
        result['aggregate']=metrics(sum(check.values(),[]),sum(xs.values(),[]),r)
        p=probe(c,r)
        rows.append({'config':c,'readout':r,'bits':bits,'metrics':result,'probes':p,'resources':resources(c,r)});save(out/'validation.json',rows)
        print('bits',bits,'probe',p['eligible'],result['aggregate'],flush=True)
    print(out)

if __name__=='__main__':main()
