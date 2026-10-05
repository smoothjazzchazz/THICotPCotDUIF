"""Small, deliberately non-Cartesian screening, preserving every run."""
import argparse
from work.study.shared.broad import *
from work.study.delay_chains.run_delay_chains import development_streams
from work.study.delay_chains.delay_chains import delay_candidates


def candidates():
    for n in (8,16,32,64,128):
        yield {'family':'modular','nodes':n,'structure':'sparse','seed':31}
    for structure in ('ring','local','skip'):
        yield {'family':'modular','nodes':32,'structure':structure,'seed':31}
    for mode in ('parallel','stacked','coupled','specialized'):
        yield {'family':'modular','nodes':32,'structure':'ring','mode':mode,'seed':31}
    for n in (8,16,32,64,128):
        yield {'family':'polynomial','nodes':n,'degree':1}
    for n in (16,24,32):
        yield {'family':'polynomial','nodes':n,'degree':2}
    for rule in (90,110,150):
        for structure in ('ring','chain'):
            yield {'family':'ca','nodes':64,'rule':rule,'structure':structure,'seed':31,'inputs':4}
    for n in (8,16,32,64):
        yield {'family':'delay','nodes':n,'coupling':.6,'leak':.5}
    for coupling in (0,.3,.9):
        yield {'family':'delay','nodes':32,'coupling':coupling,'leak':.5}
    yield {'family':'delay','nodes':32,'coupling':.6,'leak':1.,'nonlinearity':'sin'}
    for name,c in delay_candidates():
        yield {'family':'legacy','name':name,'reservoir':c.to_dict(),'nodes':16}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--family'); args=parser.parse_args()
    train,val=development_streams()
    configs=[c for c in candidates() if args.family is None or c['family']==args.family]
    out=reserve('broad-screen','screening',configs)
    save(out/'datasets.json', {'training':[asdict(s) for s in train], 'validation':[asdict(s) for s in val]})
    records=[]
    for i,c in enumerate(configs):
        ts,vs=collect(train,c),collect(val,c)
        r=select(train,ts,val,vs)
        p=probe(c,r)
        row={'config':c,'readout':r,'probes':p,'outcome':'promising' if p['eligible'] and min(r['validation'][k] for k in ('event_precision','event_recall','unknown_recall'))>=.8 else 'rejected'}
        records.append(row); save(out/'screen.json',records)
        m=r['validation']
        print(i,c,'P/R/U/F1',*[round(m[k],3) for k in ('event_precision','event_recall','unknown_recall','event_f1')], 'probe',p['eligible'],flush=True)
    print(out,flush=True)

if __name__=='__main__':main()
