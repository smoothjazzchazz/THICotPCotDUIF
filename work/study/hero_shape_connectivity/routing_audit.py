"""Constructive information-delay counterexample for last-layer-only readout."""
from pathlib import Path
import numpy as np
from .shapes import make_shape,initialize,features
from .vendor.network import run
from .vendor.data import reference_labels
from .train import write_json


def audit(root):
    # SPI1: CS falls at 10, launch edge rises at 14, data changes at 18,
    # sample edge falls at 19. Both waveforms have legal one-tick setup.
    a=np.tile([0,1,0],(32,1)).astype(np.uint8);a[10:30,1]=0;a[14:19,0]=1
    b=a.copy();b[18:30,2]=1
    labels_a=reference_labels(a,'spi1');labels_b=reference_labels(b,'spi1')
    assert labels_a[19]==1 and labels_b[19]==2
    rows=[]
    for schedule in ('registered','current'):
        sh=make_shape('srr',schedule);p=initialize(sh,11)
        states=[]
        for lines in (a,b):
            x=features(lines)[0];h=np.zeros(sh.n);trace=[]
            for row in x:
                _,h,_,_,_=run(sh,p,row[None,:],h=h);trace.append(h.copy())
            states.append(np.array(trace))
        distances=[float(np.linalg.norm(states[0][19,g]-states[1][19,g])) for g in sh.groups]
        if schedule=='registered':assert distances[-1]==0 and distances[0]>0
        rows.append(dict(schedule=schedule,sample_tick=19,first_data_difference=18,layer_distances=distances,
            implication='registered last-layer-only cannot distinguish these bit labels at this exact decision tick; all-node readout is not subject to that bound'))
        np.savez_compressed(root/'diagnostics'/f'routing_{schedule}.npz',lines_a=a,lines_b=b,labels_a=labels_a,labels_b=labels_b,states_a=states[0],states_b=states[1])
    write_json(root/'diagnostics'/'routing_counterexample.json',rows)

if __name__=='__main__':audit(Path(__file__).parent/'runs'/'connectivity01')
