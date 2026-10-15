"""Shared streaming receiver; profile logic never enters the recurrent kernel."""
import ctypes
from pathlib import Path
import subprocess
import numpy as np
from .shapes import features

ROOT = Path(__file__).parent
_library = None


def compile_kernel():
    target = ROOT/'build'/'kernel.so'
    target.parent.mkdir(exist_ok=True)
    temporary=target.with_suffix('.new.so')
    subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(ROOT/'kernel.cpp'),'-o',str(temporary)],check=True)
    temporary.replace(target)
    return target


def kernel():
    global _library
    if _library is None:
        _library = ctypes.CDLL(str(ROOT/'build'/'kernel.so'))
        _library.sequence.restype = ctypes.c_double
        _library.sequence.argtypes = [ctypes.c_int]*3+[ctypes.c_void_p]*12+[ctypes.c_int]*3
    return _library.sequence


def run(shape,p,x,y=None,cw=None,h=None,backward=False,readout_only=False,quantize=False):
    x=np.ascontiguousarray(x,dtype=np.float64)
    y=None if y is None else np.ascontiguousarray(y,dtype=np.int32)
    cw=np.ones(6) if cw is None else np.ascontiguousarray(cw,dtype=np.float64)
    h=np.zeros(shape.n) if h is None else np.array(h,dtype=np.float64,copy=True)
    logits=np.empty((len(x),6)); grad=np.zeros_like(p); dh=np.zeros(shape.n)
    if quantize:
        if backward:raise ValueError('fixed-point replay is inference only')
        kernel()
        table=np.rint(np.tanh(np.arange(-2048,2049)/256)*4096).astype(np.int32)
        f=_library.fixed_sequence
        f.argtypes=[ctypes.c_int]*3+[ctypes.c_void_p]*10;f.restype=None
        arrays=[shape.src,shape.dst,shape.delay,shape.leaks,p,x,h,logits,table]
        f.argtypes=[ctypes.c_int]*3+[ctypes.c_void_p]*9
        f(len(x),shape.n,len(shape.src),*[a.ctypes.data for a in arrays])
        return 0.,h,logits,grad,dh
    arrays=[shape.src,shape.dst,shape.delay,shape.leaks,p,x,y,cw,h,logits,grad,dh]
    # Twelve pointer arguments are kept explicit to make the ABI auditable.
    f=kernel()
    f.argtypes=[ctypes.c_int]*3+[ctypes.c_void_p]*12+[ctypes.c_int]*3
    loss=f(len(x),shape.n,len(shape.src),*[None if a is None else a.ctypes.data for a in arrays],int(backward),int(readout_only),int(quantize))
    return loss,h,logits,grad,dh


def pulses(kinds,previous=0):
    kinds=np.asarray(kinds,dtype=np.int32)
    return np.where(kinds!=np.r_[previous,kinds[:-1]],kinds,0).astype(np.int32)


def events(kinds,offset=0):
    # Event occurrence and bit value are distinct. A NONE separates repeated bits.
    return [dict(kind=int(k),bit=int(k-1) if k in (1,2) else None,
                 observation_tick=int(t+offset),decision_tick=int(t+offset))
            for t,k in enumerate(kinds) if k]


class Receiver:
    def __init__(self,shape,parameters):
        self.shape,self.p=shape,parameters
        self.state=np.zeros(shape.n);self.previous=None;self.ages=None;self.tick=0;self.last_kind=0

    def samples(self,lines):
        x,self.previous,self.ages=features(lines,self.previous,self.ages)
        _,self.state,logits,_,_=run(self.shape,self.p,x,h=self.state)
        kinds=logits.argmax(1)
        out=events(pulses(kinds,self.last_kind),self.tick)
        self.last_kind=int(kinds[-1]);self.tick+=len(lines)
        return out
