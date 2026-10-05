"""Transparent operation/storage counts; these are NOT synthesis estimates."""
import math
import numpy as np
from work.study.shared.broad import build


def resources(config, readout):
    model=build(config); features=len(model.step(0)); n=len(model.state)
    family=config['family']
    precision=config.get('bits',64)
    connections=operations=0
    if family=='polynomial':
        # Signed samples are one bit after startup. A validity counter (or mask)
        # reproduces the initial zeros; use the conservative per-sample mask here.
        precision=64 if config.get('input') == 'age' else 1; connections=n-1
        products=features-n
        operations=n+products
        extra=8 if config.get('input') == 'age' else n
        detail={'sample_moves':n,'pair_products':products,'product_implementation':'floating multiplication' if precision==64 else 'XNOR after startup', 'extra_state_bits':extra}
    elif family=='ca':
        precision=1;connections=3*n;operations=3*n+len(model.sites);extra=0
        detail={'local_rule_lookups':n,'input_overwrites':len(model.sites)}
    elif family=='delay':
        connections=n+1;operations=n+6;extra=0
        detail={'delay_moves':n-1,'scalar_nonlinearities':1,'scalar_multiply_adds':6}
    elif family=='modular':
        connections=int(np.count_nonzero(model.weights))+int(np.count_nonzero(model.inputs))
        operations=connections*2+n*4;extra=8
        detail={'multiply_adds':connections,'nonlinearities':n,'feature_state_bits':extra,
                'topology_weight_parameters':connections}
    else:
        precision=config['reservoir']['state_bits'];extra=8
        connections=sum(w!=0 for row in config['reservoir']['recurrent_taps']+config['reservoir']['feature_taps'] for _,w in row)
        operations=connections*2+3*n
        detail={'weighted_taps':connections,'leak_and_clip':n,'feature_state_bits':extra}
    weights=np.asarray(readout['weights']);bias=np.asarray(readout['bias'])
    parameters=weights.size+bias.size
    coefficient_bits=readout.get('coefficient_bits',64)
    accumulator=None
    if 'coefficient_bits' in readout and family=='polynomial':
        bound=int(np.max(np.abs(weights).sum(axis=0)+np.abs(bias)))
        accumulator=max(2,1+math.ceil(math.log2(bound+1)))
        detail['max_abs_score_bound']=bound
    return {'status':'analytical accounting only; no RTL synthesis or clock estimate',
            'state_entries':n,'bits_per_entry':precision,'dynamic_state_bits':n*precision+extra,
            'connections':connections,'state_operations_per_tick':operations,
            'feature_count':features,'feature_materialization_bits':features*precision,
            'readout_parameters':parameters,'readout_parameter_bits':parameters*coefficient_bits,
            'readout_mac_per_tick':weights.size,'readout_accumulator_bits':accumulator,
            'stabilizer_state_bits_estimate':24,'pipeline_latency':'No modeled pipeline; measured emission latency includes M only',
            'detail':detail}
