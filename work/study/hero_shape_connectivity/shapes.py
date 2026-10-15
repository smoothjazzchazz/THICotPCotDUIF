"""Actual physical graphs; unchanged routes come from the historical mask."""
from dataclasses import replace
import hashlib
import json
import numpy as np
from .vendor.shapes import Shape, make_shape as historical_shape, features, SEEDS, PROFILES


def make_shape(code='srr', schedule='registered', sizes=(24,20,20), direction=1,
               routing='baseline', injection='first', readout='all', leaks=(1.,.5,.125),head='flat',cell='plain',feedback='none',bridge='none',first_fanin=4):
    if cell in ('parent64_plain56','parent64_gated8'):
        from .mixed_shape import MixedFirstEightShape
        if not (code=='srr' and schedule=='registered' and tuple(sizes)==(24,16,16) and routing=='port_fanin4' and injection=='first' and readout=='all' and head=='flat' and feedback=='both2' and bridge=='none' and first_fanin==4 and direction==1):
            raise ValueError('parent64 truncation uses the explicitly paired primary graph')
        base=make_shape(code,schedule,(24,16,24),direction,routing,injection,readout,leaks,head,feedback=feedback)
        edges=[(int(s),int(d),int(t)) for s,d,t in zip(base.src,base.dst,base.delay) if s<56 and d<56]
        edges.append((55,40,1));edges.sort(key=lambda e:(e[1],e[0],e[2]));a=np.array(edges,dtype=np.int32)
        groups=[base.groups[0],base.groups[1],list(range(40,56))]
        cls=Shape if cell=='parent64_plain56' else MixedFirstEightShape
        name=base.name.replace('24-16-24','24-16-16')+'_'+cell
        sh=cls(name,56,groups,a[:,0].copy(),a[:,1].copy(),a[:,2].copy(),base.leaks[:56].copy())
        if cell=='parent64_gated8' and any(not 0<sh.leaks[i]<1 for i in sh.gate_nodes):raise ValueError('gated initial leak must lie strictly inside(0,1)')
        return sh
    if cell in ('readout16_dense','readout16_fanin8','readout16_fanin32','readout16_fanin32_fast'):
        from .readout_shape import augment
        if tuple(sizes)!=(16,16,16) or schedule!='registered' or head!='flat' or routing!='port_firstlast4':
            raise ValueError('readout pilot uses the declared registered 16+16+16 backbone')
        base=make_shape(code,schedule,sizes,direction,routing,injection,readout,leaks,head,feedback=feedback,bridge=bridge,first_fanin=first_fanin)
        return augment(base,cell.removeprefix('readout16_'))
    if cell in ('mixed_last','mixed_first'):
        from .mixed_shape import MixedShape,MixedFirstShape
        if tuple(sizes)!=(16,16,16) or schedule!='registered' or head!='flat' or routing!='port_firstlast4':
            raise ValueError('mixed pilot is the explicitly specified registered 16+16+16-state graph')
        base=make_shape(code,schedule,sizes,direction,routing,injection,readout,leaks,head,feedback=feedback,bridge=bridge,first_fanin=first_fanin)
        cls=MixedShape if cell=='mixed_last' else MixedFirstShape
        gated_group=base.groups[2 if cell=='mixed_last' else 0]
        if any(not 0<base.leaks[i]<1 for i in gated_group):raise ValueError('initial gate leak must be strictly between0 and1')
        return cls(base.name+'_'+cell,base.n,base.groups,base.src,base.dst,base.delay,base.leaks)
    if cell=='gated':
        if bridge!='none' or first_fanin!=4:raise ValueError('bridge/fan-in comparison is defined for plain nodes')
        from .gated_shape import GatedShape
        if any(n%2 for n in sizes) or head!='flat':raise ValueError('gated sizes count proposal+gate nodes and must be even; flat head only')
        base=make_shape(code,schedule,tuple(n//2 for n in sizes),direction,routing,injection,readout,leaks,head,feedback=feedback)
        name=base.name.replace('-'.join(str(n//2) for n in sizes),'-'.join(map(str,sizes)))+'_gated'
        return GatedShape(name,base.n,base.groups,base.src,base.dst,base.delay,base.leaks)
    if cell!='plain':raise ValueError(cell)
    if readout!='all':raise ValueError('restricted readout not yet implemented; do not create a cosmetic variant')
    if len(code)!=3 or len(sizes)!=3 or schedule not in ('registered','current'):raise ValueError('three layers and explicit schedule required')
    n=sum(sizes)
    # Generating the full sparse graph first keeps every common route identical.
    base=historical_shape('stack3_'+schedule,n)
    if [len(g) for g in base.groups]!=list(sizes):
        rng=np.random.default_rng(20261012+n)
        ends=np.r_[0,np.cumsum(sizes)]
        groups=[list(range(int(a),int(b))) for a,b in zip(ends[:-1],ends[1:])]
        edges=[]
        for g,nodes in enumerate(groups):
            for i in nodes:
                rec=[i]+rng.choice([j for j in nodes if j!=i],3,replace=False).tolist()
                edges.extend((int(j),i,1) for j in rec)
                if g:edges.extend((int(j),i,int(schedule=='registered')) for j in rng.choice(groups[g-1],4,replace=False))
                else:edges.extend((-1-f,i,0) for f in range(9))
        edges.sort(key=lambda e:(e[1],e[0],e[2]));a=np.array(edges,dtype=np.int32)
        base=Shape('',n,groups,a[:,0].copy(),a[:,1].copy(),a[:,2].copy(),np.ones(n))
    group_of={i:g for g,nodes in enumerate(base.groups) for i in nodes}
    edges=[]
    for s,d,delay in zip(base.src,base.dst,base.delay):
        g=group_of[int(d)]
        if s<0 or group_of[int(s)]!=g or code[g]=='s':edges.append((int(s),int(d),int(delay)))
    for g,(kind,nodes) in enumerate(zip(code,base.groups)):
        if kind=='s':continue
        rng=np.random.default_rng(44000+g+len(nodes))
        perm=rng.permutation(nodes)
        for j,d in enumerate(nodes):
            if kind=='z':sources=[]
            elif kind=='p':sources=[int(perm[j])]
            elif kind=='r':sources=[nodes[(j-direction)%len(nodes)]]
            elif kind=='h':sources=[d,nodes[(j-direction)%len(nodes)]]
            elif kind=='k':sources=[d]+[nodes[(j-direction*k)%len(nodes)] for k in (1,4,9)]
            elif kind=='d':sources=[] if j==0 else [nodes[j-1]]
            else:raise ValueError(kind)
            edges.extend((s,d,1) for s in sorted(set(sources)))
    if first_fanin!=4:
        if code[0]!='s' or first_fanin not in (1,2,3):raise ValueError('first sparse fan-in must be one through four, including self')
        nodes=base.groups[0];keep=set()
        for d in nodes:
            others=sorted(s for s,dd,t in edges if dd==d and s in nodes and s!=d)
            rng=np.random.default_rng([59031,n,d])
            chosen=rng.permutation(others)[:first_fanin-1].tolist()
            keep.update((s,d,1) for s in [d]+chosen)
        edges=[e for e in edges if not (e[0] in nodes and e[1] in nodes) or e in keep]
    if routing!='baseline':
        edges=[e for e in edges if e[0]<0 or group_of[e[0]]==group_of[e[1]]]
        for g in (1,2):
            parents=base.groups[0 if routing=='port_firstlast4' else g-1]
            if routing in ('port_distfast4','port_fastfanin16'):
                inlets=[base.groups[g][k*len(base.groups[g])//4] for k in range(4)] if g==1 and routing=='port_distfast4' else [base.groups[g][0]]
                fanin=16 if g==1 and routing=='port_fastfanin16' else 4
                for d in inlets:
                    edges.extend((parents[k*len(parents)//fanin],d,int(schedule=='registered')) for k in range(fanin))
                continue
            if routing in ('one_port','port_fanin4','port_firstlast4'):
                for k in range(1 if routing=='one_port' else 4):
                    edges.append((parents[k*len(parents)//4],base.groups[g][0],int(schedule=='registered')))
                continue
            for j,d in enumerate(base.groups[g]):
                offsets={'aligned1':(0,), 'aligned4':(0,1,2,3), 'skip4':(0,3,7,11)}[routing]
                edges.extend((parents[(j+k)%len(parents)],d,int(schedule=='registered')) for k in offsets)
    if injection=='all':
        edges.extend((-1-f,i,0) for nodes in base.groups[1:] for i in nodes for f in range(9))
    elif injection in ('lanes_roundrobin','lanes_banks'):
        nodes=base.groups[0]
        if len(nodes)%3:raise ValueError('balanced lane allocation requires first-layer size divisible by three')
        assigned={d:(j%3 if injection=='lanes_roundrobin' else j//(len(nodes)//3)) for j,d in enumerate(nodes)}
        edges=[e for e in edges if e[0]>=0 or (-1-e[0])%3==assigned[e[1]]]
    elif injection!='first':raise ValueError(injection)
    if bridge!='none':
        if routing!='port_fanin4' or bridge not in ('first4','middle4'):raise ValueError('bridge comparison requires four-port routing and first4/middle4')
        parents=base.groups[0 if bridge=='first4' else 1]
        for k in range(4):
            offset=0 if bridge=='first4' else max(1,len(parents)//8)
            edges.append((parents[(k*len(parents)//4+offset)%len(parents)],base.groups[2][0],int(schedule=='registered')))
        if len(set(edges))!=len(edges):raise ValueError('bridge duplicates a physical connection')
    if feedback not in ('none','top1','both1','both2'):raise ValueError(feedback)
    if feedback!='none':
        for j,d in enumerate(base.groups[0]):
            for parent in ([2] if feedback=='top1' else [1,2]):
                nodes=base.groups[parent];edges.append((nodes[j%len(nodes)],d,1))
                if feedback=='both2':edges.append((nodes[(j+len(nodes)//4)%len(nodes)],d,1))
    edges.sort(key=lambda e:(e[1],e[0],e[2]));a=np.array(edges,dtype=np.int32)
    name=f'{code}_{schedule}_'+ '-'.join(map(str,sizes))
    suffix=(('_reverse' if direction==-1 else '')+('_'+routing if routing!='baseline' else '')+
            ('_inject'+injection if injection!='first' else '')+('_read'+readout if readout!='all' else '')+
            ('_leak'+','.join(map(str,leaks)) if tuple(leaks)!=(1.,.5,.125) else ''))
    if head not in ('flat','factor'):raise ValueError(head)
    if head=='factor':suffix+='_factor'
    if feedback!='none':suffix+='_'+feedback
    if bridge!='none':suffix+='_bridge_'+bridge
    if first_fanin!=4:suffix+=f'_firstfanin{first_fanin}'
    sh=Shape(name+suffix,n,base.groups,a[:,0].copy(),a[:,1].copy(),a[:,2].copy(),np.repeat(leaks,sizes))
    sh.head=head
    return sh


def initialize(shape,seed):
    """Edge-keyed draws keep common parameters paired; normalize recurrent radius."""
    if getattr(shape,'nonlinear_readout',False):
        from .readout_shape import initialize as readout_initialize
        return readout_initialize(shape,seed)
    if getattr(shape,'mixed',False):
        from .mixed_shape import initialize as mixed_initialize
        base=Shape(shape.name,shape.n,shape.groups,shape.src,shape.dst,shape.delay,shape.leaks)
        return mixed_initialize(shape,seed,initialize(base,seed))
    if getattr(shape,'gated',False):
        from .gated_shape import initialize as gated_initialize
        base=Shape(shape.name,shape.n,shape.groups,shape.src,shape.dst,shape.delay,shape.leaks)
        return gated_initialize(shape,seed,initialize(base,seed))
    e=len(shape.src);p=np.zeros(shape.parameters)
    group_of={i:g for g,nodes in enumerate(shape.groups) for i in nodes}
    for k,(s,d) in enumerate(zip(shape.src,shape.dst)):
        rng=np.random.default_rng(np.random.SeedSequence([seed,int(s)+16,int(d),14013]))
        p[k]=rng.normal(0,.25 if s<0 else .15)
        if s==d:p[k]=.85+rng.normal(0,.03)
    for nodes in shape.groups:
        matrix=np.zeros((len(nodes),len(nodes)));loc={i:j for j,i in enumerate(nodes)}
        indices=[k for k,(s,d) in enumerate(zip(shape.src,shape.dst)) if s in loc and d in loc]
        for k in indices:matrix[loc[int(shape.dst[k])],loc[int(shape.src[k])]]=p[k]
        radius=max(abs(np.linalg.eigvals(matrix)),default=0.)
        if radius>1e-9:p[indices]*=.95/radius
    rng=np.random.default_rng(seed+87000)
    p[e:e+shape.n]=rng.normal(0,.02,shape.n)
    p[e+shape.n:e+7*shape.n]=rng.normal(0,.1,6*shape.n);p[-6]=1.
    if getattr(shape,'head','flat')=='factor':p[-6]=-1.
    return p


def cost(shape):
    if getattr(shape,'nonlinear_readout',False):
        plain=Shape(shape.name,shape.n,shape.groups,shape.src,shape.dst,shape.delay,shape.leaks)
        d=cost(plain);d.update(stored_states=48,nonlinear_readout_nodes=16,activation_depth=2,
            q12_state_banks_bytes=4*48,leak_configuration_bytes=2*48,
            known_numeric_storage_bytes=2*shape.parameters+4*48+2*48+8194,
            leak_multiplies_per_tick=2*48,modeled_multiplies_per_tick=d['macs_per_tick']+2*48,
            readout_hidden_edges=int(np.count_nonzero(shape.dst>=48)),
            state_storage_note='48 recurrent states physically required; software buffer retains16 unused prior readout values')
        return d
    if getattr(shape,'mixed',False):
        from .mixed_shape import cost as mixed_cost
        return mixed_cost(shape)
    groups={i:g for g,nodes in enumerate(shape.groups) for i in nodes}
    inputs=sum(s<0 for s in shape.src)
    recurrence=sum(s>=0 and groups[int(s)]==groups[int(d)] for s,d in zip(shape.src,shape.dst))
    routes=len(shape.src)-inputs-recurrence
    factor=2 if getattr(shape,'gated',False) else 1
    return dict(nodes=factor*shape.n,stored_states=shape.n,input_edges=int(inputs)*factor,recurrent_edges=int(recurrence)*factor,inter_layer_edges=int(routes)*factor,
        readout_edges=6*shape.n,parameters=shape.parameters,macs_per_tick=factor*len(shape.src)+6*shape.n,
        leak_multiplies_per_tick=2*shape.n,tanh_per_tick=shape.n,q12_parameters_bytes=2*shape.parameters,
        sigmoid_per_tick=shape.n if factor==2 else 0,
        q12_state_banks_bytes=4*shape.n,leak_configuration_bytes=2*shape.n if factor==1 else 0,
        modeled_multiplies_per_tick=factor*len(shape.src)+6*shape.n+2*shape.n,
        known_numeric_storage_bytes=2*shape.parameters+4*shape.n+(2*shape.n if factor==1 else 0)+8194,
        storage_subtotal_excludes='assembler buffers/control, preprocessing/divider registers, routing, and executable software; not total silicon memory or area',
        generic_preprocessing='3 prior levels + 3 capped 9-bit ages + common divider + lane mapping',
        pulse_state_bits=3,activation_lut_bytes=8194,assembler='event-only; up to 1026 bytes plus ACK/boundary state; unsynthesized',
        activation_depth=3 if 'current' in shape.name else 1,
        physical_area='unmeasured; counts are not placement area',clock_hz=0)


def specification(shape,kwargs):
    config=shape.config();config.update(construction=kwargs,resources=cost(shape))
    if getattr(shape,'head','flat')=='factor':config['readout']='six affine outputs: occurrence sign, bit-value sign, argmax bit/start/stop/invalid; unchanged causal event classes'
    config['shape_sha256']=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    return config
