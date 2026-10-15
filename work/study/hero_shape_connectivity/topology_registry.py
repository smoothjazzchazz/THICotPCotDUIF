"""Group literal hardware masks separately from programmable coefficient settings."""
import hashlib,json
from .run import ROOT
from .shapes import make_shape,cost
from .train import write_json


def physical_definition(sh):
    c=cost(sh)
    kind='mixed_tanh_sigmoid' if getattr(sh,'mixed',False) else 'all_gated_tanh' if getattr(sh,'gated',False) else 'leaky_tanh'
    d=dict(cell_equation=kind,proposal_units=sh.n,stored_states=c['stored_states'],head=getattr(sh,'head','flat'),
        generic_input_count=9,event_logits=6,proposal_edges=[list(map(int,e)) for e in zip(sh.src,sh.dst,sh.delay)],
        readout_sources=list(range(sh.n)),proposal_bias_slots=sh.n,output_bias_slots=6,
        leak_capability='programmable coefficients in the same leaky-state equation; numeric settings excluded',
        current_sample_readout_units=int(getattr(sh,'nonlinear_readout',False))*16)
    if getattr(sh,'mixed',False):
        d.update(gate_nodes=sh.gate_nodes.tolist(),gate_edges=[dict(src=int(s),dst=int(t),delay=1) for s,t in zip(sh.gate_src,sh.gate_dst)],gate_bias_slots=len(sh.gate_nodes))
    elif getattr(sh,'gated',False):
        d.update(gate_nodes=list(range(sh.n)),gate_edges=d['proposal_edges'],gate_bias_slots=sh.n)
    return d


def identity(sh):
    return hashlib.sha256(json.dumps(physical_definition(sh),sort_keys=True).encode()).hexdigest()

if __name__=='__main__':
    root=ROOT/'runs/connectivity01';groups={}
    for path in sorted((root/'shapes').glob('*.json')):
        record=json.loads(path.read_text());kw=record.get('construction')
        if kw is None:continue
        sh=make_shape(**kw);key=identity(sh)
        row=groups.setdefault(key,dict(physical_definition=physical_definition(sh),resource_counts=cost(sh),configuration_aliases=[]))
        row['configuration_aliases'].append(dict(name=sh.name,construction=kw,path=str(path)))
    write_json(root/'physical_topologies.json',dict(scope='literal hardware identity under the shared node numbering; different hashes are not a graph-nonisomorphism proof',
        policy='different leak values, weight seeds, protected-training masks or learned weights alone do not create additional physical shapes',groups=groups))
    repeated=[r for r in groups.values() if len(r['configuration_aliases'])>1]
    print('Physical masks',len(groups),'configuration aliases',sum(len(r['configuration_aliases']) for r in groups.values()),'multi-configuration masks',len(repeated))
