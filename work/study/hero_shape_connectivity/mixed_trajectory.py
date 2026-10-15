"""Fixed causal state extraction for existing mixed proposal/gate models."""
import ctypes,subprocess
from pathlib import Path
import numpy as np
from .runtime import run
ROOT=Path(__file__).parent
_library=None


def compile_kernel():
    target=ROOT/'build/mixed_state_kernel.so';target.parent.mkdir(exist_ok=True);temp=target.with_suffix('.new.so')
    subprocess.run(['g++','-O3','-std=c++17','-shared','-fPIC',str(ROOT/'mixed_state_kernel.cpp'),'-o',str(temp)],check=True);temp.replace(target)


def trajectory(sh,p,x):
    global _library
    if _library is None:_library=ctypes.CDLL(str(ROOT/'build/mixed_state_kernel.so'))
    f=_library.mixed_states;f.argtypes=[ctypes.c_int]*5+[ctypes.c_void_p]*10;f.restype=None
    states=np.zeros((len(x)+1,sh.n));x=np.ascontiguousarray(x,dtype=np.float64);p=np.ascontiguousarray(p,dtype=np.float64)
    gs,gd,gn=sh.gate_src,sh.gate_dst,sh.gate_nodes;arrays=(sh.src,sh.dst,sh.delay,gs,gd,gn,sh.leaks,p,x,states)
    f(len(x),sh.n,len(sh.src),len(gs),len(gn),*[a.ctypes.data for a in arrays])
    assert np.array_equal(states[-1],run(sh,p,x)[1]),'mixed trace differs from deployed recurrence'
    return states[1:]


if __name__=='__main__':compile_kernel()
