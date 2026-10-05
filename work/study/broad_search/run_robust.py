"""Diagnose jitter misses with matched training/threshold controls."""
from work.study.shared.broad import *
from work.study.delay_chains.run_delay_chains import development_streams


def robust_select(train, ts, groups, gs, explicit=True):
    val=sum(groups.values(),[]); vs=sum(gs.values(),[])
    best=key=None
    for ridge in (.0001,.001,.01,.1,1.):
        r=fit(train,ts,ridge,explicit)
        sc=scores(vs,r)
        for floor in (0,.2,.4,.6):
            for margin in (0,.1,.2):
                pred=[choose_classes(x,r['class_ids'],DecisionRule(floor,margin)) for x in sc]
                for hold in (1,2,3):
                    result={}; start=0
                    for k,ss in groups.items():
                        result[k]=measure(ss,pred[start:start+len(ss)],hold)[0];start+=len(ss)
                    result['aggregate']=measure(val,pred,hold)[0]
                    ratios=[]
                    for k,m in result.items():
                        limits=(.95,.95,.95) if k=='clean' else ((.8,.8,.8) if k in ('original','aggregate') else (.75,.65,.65))
                        ratios.extend(m[x]/limit for x,limit in zip(('event_precision','event_recall','unknown_recall'),limits))
                    rank=(min(1.,min(ratios)),result['aggregate']['event_f1'],result['aggregate']['unknown_recall'])
                    if key is None or rank>key:
                        key=rank;best={**r,'floor':floor,'margin':margin,'hold':hold,'validation':result}
    return best


def main():
    original,val=development_streams()
    augmentation=sum(development(33000000,8).values(),[])
    groups={'original':val,**development(34000000,6)}
    check=development(35000000,12)
    configurations=[(n,aug,True) for n in (20,24,28,32) for aug in (False,True)] + [(24,True,False)]
    out=reserve('jitter-training','validation',{'configurations':configurations,'hypothesis':'Missing ±2 timing cases in training causes jitter misses; compare augmented and original training under identical threshold selection.'})
    save(out/'datasets.json',{'original':[asdict(s) for s in original],'augmentation':[asdict(s) for s in augmentation], 'selection':{k:[asdict(s) for s in v] for k,v in groups.items()}, 'check':{k:[asdict(s) for s in v] for k,v in check.items()}})
    records=[]
    for n,aug,explicit in configurations:
        c={'family':'polynomial','nodes':n,'degree':2}
        train=original+augmentation if aug else original
        r=robust_select(train,collect(train,c),groups,{k:collect(ss,c) for k,ss in groups.items()},explicit)
        result={k:metrics(ss,collect(ss,c),r) for k,ss in check.items()}
        result['aggregate']=metrics(sum(check.values(),[]),collect(sum(check.values(),[]),c),r)
        p=probe(c,r)
        row={'config':c,'augmentation':aug,'explicit':explicit,'readout':r,'probes':p,'metrics':result}
        records.append(row);save(out/'validation.json',records)
        print(n,'aug',aug,'explicit',explicit,'probe',p['eligible'],{k:[round(m[x],3) for x in ('event_precision','event_recall','unknown_recall','event_f1')] for k,m in result.items()},flush=True)
    print(out)

if __name__=='__main__':main()
