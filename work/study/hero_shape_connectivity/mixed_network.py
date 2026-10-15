"""Generic mixed-cell streaming kernel; no protocol logic or timing counters."""
import ctypes
from pathlib import Path
import subprocess
import numpy as np
ROOT=Path(__file__).parent
_library=None


def compile_kernel():
    target=ROOT/'build'/'mixed_kernel.so';target.parent.mkdir(exist_ok=True)
    temp=target.with_suffix('.new.so')
    subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(ROOT/'mixed_kernel.cpp'),'-o',str(temp)],check=True)
    temp.replace(target);return target


def run(shape,p,x,y=None,cw=None,h=None,backward=False,readout_only=False,quantize=False):
    global _library
    if _library is None:_library=ctypes.CDLL(str(ROOT/'build'/'mixed_kernel.so'))
    x=np.ascontiguousarray(x,dtype=np.float64);p=np.ascontiguousarray(p,dtype=np.float64)
    y=None if y is None else np.ascontiguousarray(y,dtype=np.int32)
    cw=np.ones(6) if cw is None else np.ascontiguousarray(cw,dtype=np.float64)
    h=np.zeros(shape.n) if h is None else np.array(h,dtype=np.float64,copy=True)
    logits=np.empty((len(x),6));grad=np.zeros_like(p);dh=np.zeros(shape.n)
    gs=shape.gate_src;gd=shape.gate_dst;gn=shape.gate_nodes
    common=[shape.src,shape.dst,shape.delay,gs,gd,gn,shape.leaks,p,x]
    sizes=[len(x),shape.n,len(shape.src),len(gs),len(gn)]
    if quantize:
        if backward:raise ValueError('integer inference only')
        table=np.rint(np.tanh(np.arange(-2048,2049)/256)*4096).astype(np.int32)
        f=_library.fixed_sequence;f.argtypes=[ctypes.c_int]*5+[ctypes.c_void_p]*12;f.restype=None
        f(*sizes,*[a.ctypes.data for a in common+[h,logits,table]])
        return 0.,h,logits,grad,dh
    f=_library.sequence;f.argtypes=[ctypes.c_int]*5+[ctypes.c_void_p]*15+[ctypes.c_int]*2;f.restype=ctypes.c_double
    arrays=common+[y,cw,h,logits,grad,dh]
    loss=f(*sizes,*[None if a is None else a.ctypes.data for a in arrays],int(backward),int(readout_only))
    return loss,h,logits,grad,dh
