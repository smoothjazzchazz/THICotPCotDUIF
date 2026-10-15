"""Common external event interface for flat and factorized generic readouts."""
import numpy as np
from .vendor.network import run as flat_run,pulses,events
from .head_network import run as head_run
from .gated_network import run as gated_run
from .leak_network import run as leak_run
from .focal_network import run as focal_run
from .shapes import features


def run(shape,*args,**kwargs):
    if getattr(shape,'mixed',False):
        from .mixed_network import run as mixed_run
        if kwargs.pop('focal',False) or kwargs.pop('learn_leaks',False):raise ValueError('mixed pilot uses the declared ordinary event objective')
        return mixed_run(shape,*args,**kwargs)
    if kwargs.pop('focal',False):
        if kwargs.pop('learn_leaks',False):raise ValueError('combined focal/leak gradients are not implemented')
        if getattr(shape,'gated',False) or getattr(shape,'head','flat')!='flat':raise ValueError('focal training requires plain flat-head nodes')
        return focal_run(shape,*args,**kwargs)
    if kwargs.pop('learn_leaks',False):
        if getattr(shape,'gated',False) or getattr(shape,'head','flat')!='flat':raise ValueError('leak-gradient diagnostic requires plain flat-head nodes')
        return leak_run(shape,*args,**kwargs)
    if getattr(shape,'gated',False):return gated_run(shape,*args,**kwargs)
    if getattr(shape,'head','flat')=='flat':return flat_run(shape,*args,**kwargs)
    loss,h,z,g,dh=head_run(shape,*args,**kwargs)
    event=z[:,0]>0;kind=z[:,2:].argmax(1)+2
    kind=np.where(kind==2,np.where(z[:,1]>0,2,1),kind)
    kind=np.where(event,kind,0)
    # The scorer consumes only argmax classes. Raw head logits remain in head_run.
    classes=np.zeros_like(z);classes[np.arange(len(z)),kind]=1
    return loss,h,classes,g,dh


class Receiver:
    def __init__(self,shape,parameters):
        self.shape,self.p=shape,parameters;self.state=np.zeros(shape.n)
        self.previous=None;self.ages=None;self.tick=0;self.last_kind=0

    def samples(self,lines):
        x,self.previous,self.ages=features(lines,self.previous,self.ages)
        _,self.state,z,_,_=run(self.shape,self.p,x,h=self.state);kinds=z.argmax(1)
        out=events(pulses(kinds,self.last_kind),self.tick)
        self.last_kind=int(kinds[-1]);self.tick+=len(lines);return out
