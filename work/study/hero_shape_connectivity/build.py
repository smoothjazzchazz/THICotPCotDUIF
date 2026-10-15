"""Build the local CPU kernels required by the complete study test suite."""
from .vendor.network import compile_kernel as plain
from .head_network import compile_kernel as head
from .gated_network import compile_kernel as gated
from .leak_network import compile_kernel as leaks
from .readout_probe import compile_kernel as trace
from .focal_network import compile_kernel as focal
from .mixed_network import compile_kernel as mixed
from .mixed_trajectory import compile_kernel as mixed_trace

if __name__=='__main__':
    for compile_one in (plain,head,gated,leaks,trace,focal,mixed,mixed_trace):compile_one()
    print('All study kernels built; no fast-math.')
