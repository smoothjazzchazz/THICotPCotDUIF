"""Off-chip UART auxiliary targets. Never imported by inference/runtime modules."""
import numpy as np


def timing_targets(lines,profile,progress_mode='uniform'):
    if profile not in ('uart_n','uart_e'):raise ValueError('training-only UART diagnostic')
    if progress_mode not in ('uniform','stop_interval'):raise ValueError(progress_mode)
    out=np.zeros((3,len(lines)),dtype=np.int32)
    previous=1;active=False;blocked=False;high_run=16;start=-1
    for t,row in enumerate(lines):
        v=int(row[0]);high_run=high_run+1 if v else 0
        if blocked and high_run>=16:blocked=False
        if not active and not blocked and previous and not v:active=True;start=t
        if active:
            age=t-start;out[:,t]=[1+age%4,1+(age//4)%4,1+min(3,age//48)]
            if progress_mode=='stop_interval':
                out[2,t]=1+int(age>=48)+int(age>=96)+int(age>=(160 if profile=='uart_e' else 144))
            if age==7 and v:active=False
            last=167 if profile=='uart_e' else 151
            if age==last:active=False;blocked=not bool(v)
        elif blocked:out[:,t]=5
        previous=v
    return out


def inlet_targets(lines,profile):
    """Training-only ring-inlet polarity, plus unchanged coarse/progress labels."""
    out=timing_targets(lines,profile);previous=1;active=False;blocked=False;high_run=16;start=-1
    for t,row in enumerate(lines):
        v=int(row[0]);high_run=high_run+1 if v else 0
        if blocked and high_run>=16:blocked=False
        if not active and not blocked and previous and not v:active=True;start=t
        out[0,t]=int(active and (t-start)%16==1)
        if active:
            age=t-start
            if age==7 and v:active=False
            if age==(167 if profile=='uart_e' else 151):active=False;blocked=not bool(v)
        previous=v
    return out
