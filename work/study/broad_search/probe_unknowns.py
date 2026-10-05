"""Fixed post-selection open-set limitation probe; never used for tuning."""
from dataclasses import asdict
import json
from work.study.shared.broad import ROOT, collect, predict, reserve, save
from work.study.shared.comparison import measure
from work.study.shared.signals import SignalStream


def main():
    model=json.loads((ROOT/'polynomial_memory/compact_20_q8.json').read_text())
    pairs=[(1,1),(12,12),(14,14),(3,12),(12,3),(6,12),(12,6)]
    levels=[0]*20;targets=[2]*20;windows=[]
    for rest in (12,20):
        for first,second in pairs:
            pulse=[1]*first+[0]*3+[1]*second
            levels+=pulse;targets += [2]*len(pulse)
            start=len(levels);levels += [0]*rest;targets += [7]*4+[2]*(rest-4)
            windows.append({'start':start,'end':start+4,'class_id':7,'pair':[first,second]})
    stream=SignalStream(-1,levels,targets,windows,0,0)
    out=reserve('unseen-unknown-probe','validation',{'purpose':'Post-selection limitation probe; outside confirmation distribution; no retuning','pairs':pairs,'rest':[12,20],'model':model})
    xs=collect([stream],model['config']);pred=predict(xs,model['readout'])
    metrics,events=measure([stream],pred,model['readout']['hold'])
    rows=[{'pair':w['pair'],'predictions':pred[0][w['start']:w['end']].tolist()} for w in windows]
    save(out/'probe.json',{'stream':asdict(stream),'metrics':metrics,'events':events,'windows':rows,'predictions':pred[0].tolist()})
    print(out);print(metrics);print(rows)

if __name__=='__main__':main()
