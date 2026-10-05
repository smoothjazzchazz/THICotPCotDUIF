"""Independent development conditions, mechanism ablations, topology replication."""
import argparse
from work.study.shared.broad import *
from work.study.delay_chains.run_delay_chains import development_streams


def configs():
    for n in (20,24,28,32,40):
        yield {'family':'polynomial','nodes':n,'degree':2}, True
    for degree, explicit in ((1,True),(2,False)):
        yield {'family':'polynomial','nodes':24,'degree':degree}, explicit
    for seed in (31,32,33):
        for mode in ('single','parallel','stacked','coupled','specialized'):
            yield {'family':'modular','nodes':32,'structure':'ring','seed':seed,'mode':mode}, True
    for bits in (4,6,8):
        yield {'family':'modular','nodes':32,'structure':'ring','seed':31,'bits':bits}, True
    for leak in (.2,.8):
        yield {'family':'modular','nodes':32,'structure':'ring','seed':31,'leak':leak}, True
    yield {'family':'modular','nodes':32,'structure':'ring','seed':31,'nonlinearity':'clip'}, True


def main():
    train,val=development_streams()
    dev=development()
    out=reserve('broader-validation','validation',list(configs()))
    save(out/'datasets.json',{'train':[asdict(s) for s in train], 'validation':[asdict(s) for s in val], 'stress':{k:[asdict(s) for s in ss] for k,ss in dev.items()}})
    records=[]
    for c,explicit in configs():
        r=select(train,collect(train,c),val,collect(val,c),explicit)
        result={k:metrics(ss,collect(ss,c),r) for k,ss in dev.items()}
        allstreams=sum(dev.values(),[])
        result['aggregate']=metrics(allstreams,collect(allstreams,c),r)
        p=probe(c,r)
        row={'config':c,'explicit':explicit,'readout':r,'probes':p,'metrics':result}
        records.append(row);save(out/'validation.json',records)
        print(c,'explicit',explicit,'probe',p['eligible'], {k:[round(m[x],3) for x in ('event_precision','event_recall','unknown_recall','event_f1')] for k,m in result.items()},flush=True)
    print(out)

if __name__=='__main__':main()
