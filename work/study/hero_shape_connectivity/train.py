"""Matched training blocks with complete-message selection and exact resume."""
import json
import time
from pathlib import Path
import numpy as np
from .shapes import make_shape, initialize
from .runtime import run
from .data import load, metrics


def write_json(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def key(row):
    return (min(r['message_accuracy'] for r in row['conditions'].values()),row['message_accuracy'],
            -row['boundary_errors'],-row['invalid_accepted']-row['background_accepted'],-row['false_events'],-row['dev_loss'])


def evaluate_stream(shape,p,data,cw):
    """Continuous inference in bounded-memory chunks, including development."""
    h=np.zeros(shape.n);logits=np.empty((len(data['x']),6));loss=0.
    for start in range(0,len(logits),8192):
        x=data['x'][start:start+8192];y=data['labels'][start:start+8192]
        value,h,z,_,_=run(shape,p,x,y,cw,h);logits[start:start+len(x)]=z;loss+=value*len(x)
    return loss/len(logits),logits


def native_v6_long_path(root,profile,data_epoch):
    """Every fourth post-curriculum epoch exposes a whole sustained corner."""
    if data_epoch%4:
        return root/'data_precision_v2'/profile/'train'/f'long_{data_epoch:04d}'
    index=(data_epoch//4-1)%16
    condition=('jitter','minus_jitter','plus_jitter','gaps')[index%4]
    return root/'data_stationary_train_v6'/profile/f'{condition}_{index//4:02d}'


def fit(job):
    root,kwargs,profile,seed,target,recipe=job;root=Path(root)
    fresh_recipe=recipe in ('phase_fresh','phase_profile_fresh','phase_focal','phase_loss_control','phase_bridge')
    recovery_recipe=recipe in ('phase_recovery','phase_recovery_readout')
    precision_readout=recipe=='phase_precision_readout_v2'
    dual_ring_recipe=recipe in ('phase_dual_ring_v4','phase_dual_refine_v4')
    inlet_recipe=recipe=='phase_inlet_v4'
    native_v6=recipe=='phase_native_v6'
    transfer_v6=recipe=='phase_n_to_e_v6'
    refine_v6=recipe=='phase_native_refine_v6'
    enlarged_recipe=native_v6 or transfer_v6 or refine_v6
    native_recipe=recipe in ('phase_native_v3','phase_dual_ring_v4','phase_inlet_v4','phase_native_v6')
    teacher_recipe=recipe in ('phase_uniform_aux_v4','phase_stop_aux_v4')
    ring_recipe=recipe in ('phase_ring_frozen_v4','phase_ring_release_v4')
    special_refine=recipe in ('phase_dual_refine_v4','phase_inlet_refine_v4')
    coverage_recipe=recipe in ('phase_coverage_v3','phase_native_refine_v3','phase_n_to_e_v3','phase_n_to_e_v6','phase_native_refine_v6') or teacher_recipe or ring_recipe or special_refine
    precision_recipe=recipe in ('phase_precision','phase_precision_v2','phase_precision_readout_v2') or native_recipe or coverage_recipe
    precision_corpus='data_precision_v2' if recipe.endswith(('_v2','_v3','_v4','_v6')) else 'data_precision'
    if enlarged_recipe:
        from .startup_evaluate import evaluate as enlarged_evaluate
    def evaluate_recipe(sh,weights):
        if enlarged_recipe:return enlarged_evaluate(sh,weights,root,profile,cw,None)
        from .precision_data import evaluate
        return evaluate(sh,weights,root,profile,cw,precision_corpus)
    extended_recipe=fresh_recipe or recovery_recipe or precision_recipe or recipe=='phase_extended'
    shape=make_shape(**kwargs);folder=root/'models'/recipe/shape.name/profile/str(seed)
    if getattr(shape,'gated',False) and recipe not in ('matched','low_lr','window1024','balanced','phase_aux'):
        raise ValueError('this initialization/curriculum recipe has not been adapted to gated parameter layout')
    folder.mkdir(parents=True,exist_ok=True)
    data_epoch_offset=json.loads((folder/'warm_start.json').read_text()).get('data_epoch_offset',0) if (folder/'warm_start.json').exists() else 0
    if extended_recipe and not native_recipe and not (folder/'warm_start.json').exists():raise ValueError('extended refinement requires an explicitly recorded same-seed source')
    if (root/'freeze.json').exists():raise ValueError('frozen run cannot train')
    journal=folder/'history.jsonl'
    history=[json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    if history and history[-1]['epoch']>=target:return json.loads((folder/f'block_{target:04d}.json').read_text())
    train={s:load(root/'data'/profile/s) for s in ['clean','patterns']+[f'mixed_{i:02d}' for i in range(12)]}
    if recipe=='phase_rich':
        train={f'mixed_{i:02d}':load(root/'data_rich'/profile/f'mixed_{i:02d}') for i in range(24)}
    dev=load(root/'data'/profile/'dev')
    if extended_recipe:
        train={f'mixed_{i:02d}':load(root/'data_extended'/profile/f'mixed_{i:02d}') for i in range(12)}
        dev=load(root/'data_extended'/profile/'dev')
        if native_recipe:
            for name in ('clean','patterns'):train[name]=load(root/'data'/profile/name)
    curriculum=recipe.startswith('curriculum') or recipe=='circulation'
    if curriculum:
        for name in ('constant','four_patterns','single_bytes','simple_dev','nominal_dev'):
            train[name]=load(root/'data'/profile/name)
    if recipe=='bit_windows':
        from .vendor.network import pulses
        for s in train.values():
            original=s['labels'];expanded=original.copy()
            for t in np.flatnonzero(np.isin(original,[1,2])):
                for dt in (1,2):
                    if t+dt<len(expanded) and original[t+dt]==0:expanded[t+dt]=original[t]
            if not np.array_equal(pulses(expanded),original):raise AssertionError('training hold altered event onsets')
            s['labels']=expanded
    counts=sum((np.bincount(s['labels'],minlength=6) for k,s in train.items() if k.startswith('mixed')),start=np.zeros(6))
    cw=np.minimum(16,np.sqrt(max(counts)/np.maximum(1,counts)));cw[[3,4,5]]*=1.5
    if recipe=='balanced':
        # Diagnose event sparsity without giving the deployed receiver a timer.
        cw=np.minimum(128,max(counts)/np.maximum(1,counts))
        cw/=float(np.dot(cw,counts)/counts.sum())
    p=initialize(shape,seed);m=np.zeros_like(p);v=np.zeros_like(p);epoch=step=exposure=0
    aux=recipe in ('phase_aux','phase_circulation','phase_clock','phase_transfer','phase_leaks','phase_fine','phase_rich','phase_route','phase_ring_fixed','phase_portfolio') or extended_recipe;offset=shape.parameters-6*shape.n-6
    train_aux=aux and recipe not in ('phase_focal','phase_loss_control','phase_recovery','phase_recovery_readout','phase_precision','phase_precision_v2','phase_precision_readout_v2','phase_coverage_v3','phase_native_refine_v3','phase_n_to_e_v3')
    if ring_recipe or special_refine:train_aux=False
    if transfer_v6 or refine_v6:train_aux=False
    learn_leaks=recipe=='phase_leaks';alpha_m=np.zeros(shape.n);alpha_v=np.zeros(shape.n);alpha_step=0
    alpha_mask=np.zeros(shape.n);alpha_mask[shape.groups[-1]]=1
    aux_weights=np.zeros((3,6*shape.n+6));aux_m=np.zeros_like(aux_weights);aux_v=np.zeros_like(aux_weights)
    if aux:
        from .teacher import timing_targets
        if inlet_recipe:
            from .teacher import inlet_targets as timing_targets
        if recipe=='phase_stop_aux_v4':
            from functools import partial
            timing_targets=partial(timing_targets,progress_mode='stop_interval')
        if fresh_recipe:train={}
        if train_aux:
            for s in train.values():s['aux']=timing_targets(s['lines'],profile)
        aux_weights=np.random.default_rng(seed+765000).normal(0,.1,aux_weights.shape)
    if recipe in ('circulation','phase_circulation','phase_clock','phase_ring_fixed') or native_recipe:
        # An unforced positive single-input ring can circulate a pulse. This is
        # initialization only: every physical weight remains trainable.
        for nodes in shape.groups:
            indices=[k for k,(src,dst) in enumerate(zip(shape.src,shape.dst)) if src in nodes and dst in nodes]
            for k in indices:p[k]*=1.05/.95
            if len(indices)==len(nodes) and all(sum(shape.dst[k]==d for k in indices)==1 for d in nodes):
                for k in indices:p[k]=1.05
        p[len(shape.src):len(shape.src)+shape.n]=0.
    trainable=np.ones(len(p))
    if recipe=='phase_clock':
        nodes=shape.groups[1]
        if len(nodes)!=16 or not np.all(shape.leaks[nodes]==1):raise ValueError('phase-clock diagnostic requires its declared 16-node unsmoothed ring')
        for k,(src,dst) in enumerate(zip(shape.src,shape.dst)):
            if src in nodes and dst in nodes:p[k]=np.arctanh(.5)/.5;trainable[k]=0
        for node in nodes[1:]:p[len(shape.src)+node]=0;trainable[len(shape.src)+node]=0
    if recipe=='phase_ring_fixed' or native_recipe:
        nodes=shape.groups[1]
        if len(nodes)!=16 or not np.all(shape.leaks[nodes]==1):raise ValueError('fixed-ring recipe requires 16 unsmoothed middle nodes')
        for k,(src,dst) in enumerate(zip(shape.src,shape.dst)):
            if src in nodes and dst in nodes:trainable[k]=0
        for node in nodes[1:]:trainable[len(shape.src)+node]=0
    if recipe in ('normalized','curriculum_normalized'):
        streams=[s['x'] for k,s in train.items() if k.startswith('mixed')]
        count=sum(len(x) for x in streams);mean=sum(x.sum(0) for x in streams)/count
        variance=sum((x*x).sum(0) for x in streams)/count-mean*mean
        sd=np.sqrt(np.maximum(0,variance));gain=np.where(sd>1e-7,1/np.maximum(sd,.05),1.)
        for k,(src,dst) in enumerate(zip(shape.src,shape.dst)):
            if src<0:
                f=-1-src;p[k]*=gain[f];p[len(shape.src)+dst]-=p[k]*mean[f]
        np.clip(p,-7.99,7.99,out=p)
    lr=.003;window=512
    if recipe=='low_lr':lr=.0003
    if recipe=='window1024':lr=.0003;window=1024
    if recipe=='phase_transfer':lr=.0003
    if recipe=='phase_route':lr=.0003
    if recipe=='phase_portfolio':lr=.0003
    if learn_leaks:lr=.0001
    if recipe in ('phase_fine','phase_rich') or extended_recipe:lr=.0001
    if recipe=='phase_recovery':lr=.00001
    if recipe=='phase_recovery_readout':lr=.001
    if precision_recipe:lr=.00001
    if precision_readout:lr=.001
    if native_recipe:lr=.003
    if coverage_recipe:lr=.0001
    if ring_recipe:lr=.00001
    if recipe in ('phase_n_to_e_v3','phase_n_to_e_v6'):lr=.0003
    if curriculum:lr=.001
    if history:
        epoch=history[-1]['epoch']
        with np.load(folder/f'epoch_{epoch:04d}.npz',allow_pickle=False) as a:
            p=a['p'];m=a['m'];v=a['v'];meta=json.loads(str(a['metadata']))
            if aux:aux_weights=a['aux_weights'];aux_m=a['aux_m'];aux_v=a['aux_v']
            if 'leaks' in a:shape.leaks=a['leaks'].copy()
            if learn_leaks and 'alpha_m' in a:
                alpha_m=a['alpha_m'];alpha_v=a['alpha_v'];alpha_step=int(a['alpha_step'])
        step=meta['step'];exposure=meta['exposure']
    elif (folder/'warm_start.json').exists():
        warm=json.loads((folder/'warm_start.json').read_text())
        with np.load(warm['checkpoint'],allow_pickle=False) as a:
            p=a['p'];m=a['m'];v=a['v'];meta=json.loads(str(a['metadata']))
            if aux:aux_weights=a['aux_weights'];aux_m=a['aux_m'];aux_v=a['aux_v']
            if 'leaks' in a:shape.leaks=a['leaks'].copy()
        step=meta['step'];exposure=0
        if warm.get('reset_optimizer'):
            step=0;m=np.zeros_like(p);v=np.zeros_like(p);aux_m=np.zeros_like(aux_weights);aux_v=np.zeros_like(aux_weights)
        if teacher_recipe:
            # Both paired arms relearn the third auxiliary projection from the
            # same draw; only its declared offline target partition differs.
            aux_weights[2]=np.random.default_rng(seed+876510).normal(0,.1,aux_weights[2].shape)
            aux_m[2]=0;aux_v[2]=0
    if recipe=='phase_portfolio':
        warm=json.loads((folder/'warm_start.json').read_text())
        if warm['retain_frozen_ring']:trainable[np.array(meta['frozen_parameter_indices'],dtype=int)]=0
    if inlet_recipe:
        # A fixed training projection supervises only the driven fast-ring node.
        # Its binary targets and these weights never enter deployed inference.
        aux_weights[0]=0
        aw=aux_weights[0,:-6].reshape(6,shape.n);aw[0,shape.groups[1][0]]=-20;aw[1,shape.groups[1][0]]=20
        aux_weights[0,-4:]=-20;aux_m[0]=0;aux_v[0]=0
    if extended_recipe and not native_recipe:trainable[np.array(meta.get('frozen_parameter_indices',[]),dtype=int)]=0
    if recipe=='phase_recovery_readout':trainable[:offset]=0
    if precision_recipe:
        # Preserve the learned fast circulation, while allowing the surrounding
        # context/recovery network to learn from many independent cold starts.
        trainable[:]=1
        nodes=shape.groups[1]
        for k,(src,dst) in enumerate(zip(shape.src,shape.dst)):
            if src in nodes and dst in nodes:trainable[k]=0
        for node in nodes[1:]:trainable[len(shape.src)+node]=0
    if precision_readout:trainable[:offset]=0
    if recipe=='phase_ring_release_v4':trainable[:]=1
    if dual_ring_recipe:
        for nodes in shape.groups[1:]:
            if not np.all(shape.leaks[nodes]==1):raise ValueError('dual-ring comparison requires unsmoothed ring states')
            indices=[k for k,(src,dst) in enumerate(zip(shape.src,shape.dst)) if src in nodes and dst in nodes]
            if len(indices)!=len(nodes):raise ValueError('dual-ring comparison requires one closed ring edge per node')
            trainable[indices]=0
            for node in nodes[1:]:trainable[len(shape.src)+node]=0
    best=max((r for r in history if 'dev_loss' in r),key=key,default=None)
    if (recipe=='phase_portfolio' or extended_recipe) and not history:
        if precision_recipe:
            dl,precision_score=evaluate_recipe(shape,p)
        elif extended_recipe:dl,logits=evaluate_stream(shape,p,dev,cw)
        else:dl,_,logits,_,_=run(shape,p,dev['x'],dev['labels'],cw)
        first=dict(epoch=0,step=step,exposure_ticks=0,split='warm_start_evaluation',lr=lr,window=window,
            train_loss=None,gradient_norm=None,elapsed_call=0.,dev_loss=dl)
        first.update(precision_score if precision_recipe else metrics(dev,logits.argmax(1)));best=first.copy();history.append(first)
        np.savez_compressed(folder/'epoch_0000.npz',p=p,m=m,v=v,ending_state=np.zeros(shape.n),aux_weights=aux_weights,aux_m=aux_m,aux_v=aux_v,
            leaks=shape.leaks,alpha_m=alpha_m,alpha_v=alpha_v,alpha_step=alpha_step,
            metadata=json.dumps(dict(epoch=0,step=step,exposure=0,lr=lr,window=window,recipe=recipe,
                frozen_parameter_indices=np.flatnonzero(trainable==0).tolist())))
        with journal.open('a') as f:f.write(json.dumps(first)+'\n')
    started=time.monotonic()
    for epoch in range(epoch+1,target+1):
        split='clean' if epoch<=5 else 'patterns' if epoch<=10 else f'mixed_{(epoch-11)%12:02d}'
        if curriculum:
            split='constant' if epoch<=60 else 'four_patterns' if epoch<=120 else 'single_bytes' if epoch<=180 else f'mixed_{(epoch-181)%12:02d}'
        if recipe in ('phase_leaks','phase_fine','phase_route','phase_portfolio','phase_extended'):split=f'mixed_{(epoch-1)%12:02d}'
        if recipe=='phase_rich':split=f'mixed_{(epoch-1)%24:02d}'
        if precision_recipe:
            split=f'precision_epoch_{epoch:04d}'
            data_epoch=epoch+data_epoch_offset
            if native_recipe or coverage_recipe:
                if native_recipe and epoch<=10:pieces=[train['clean' if epoch<=5 else 'patterns']]
                else:
                    data_epoch=epoch-10 if native_recipe else epoch+data_epoch_offset
                    long_path=native_v6_long_path(root,profile,data_epoch) if enlarged_recipe else root/precision_corpus/profile/'train'/f'long_{data_epoch:04d}'
                    pieces=[load(long_path)]
                    if enlarged_recipe:split=str(long_path.relative_to(root))
                    pieces.extend(load(root/precision_corpus/profile/'train'/f'cold_{i:03d}') for i in ((np.arange(4)+(data_epoch-1)*4)%256))
                    pieces.extend(load(root/'data_startup_modes'/profile/f'idle_{i:03d}') for i in ((np.arange(4)+(data_epoch-1)*4)%256))
                    pieces.extend(load(root/'data_startup_modes'/profile/f'errors_{i:03d}') for i in ((np.arange(2)+(data_epoch-1)*2)%64))
            else:
                pieces=[load(root/precision_corpus/profile/'train'/f'long_{data_epoch:04d}')] if recipe.endswith('_v2') else [load(root/'data_fresh'/profile/f'epoch_{epoch:04d}')]
                pieces.extend(load(root/precision_corpus/profile/'train'/f'cold_{i:03d}') for i in ((np.arange(8)+(data_epoch-1)*8)%256))
            lengths=[len(s['x']) for s in pieces]
            data={k:np.concatenate([s[k] for s in pieces]) for k in ('x','labels')}
            if train_aux:data['aux']=np.concatenate([timing_targets(s['lines'],profile) for s in pieces],axis=1)
        elif recovery_recipe:
            split=f'epoch_{epoch:04d}'
            data=load(root/('data_recovery' if epoch%2 else 'data_fresh')/profile/split)
        elif fresh_recipe:
            split=f'epoch_{epoch+data_epoch_offset:04d}';data=load(root/'data_fresh'/profile/split)
            if train_aux:data['aux']=timing_targets(data['lines'],profile)
        else:data=train[split]
        x=data['x'];y=data['labels'];h=np.zeros(shape.n)
        losses=[];norms=[];aux_losses=[]
        edges=np.r_[0,np.cumsum(lengths)] if precision_recipe else [0,len(x)]
        chunks=[(t,min(t+window,end),t==start) for start,end in zip(edges[:-1],edges[1:]) for t in range(start,end,window)]
        for t,end,cold_start in chunks:
            if cold_start:h=np.zeros(shape.n)
            before=h.copy()
            loss,h,_,g,dh=run(shape,p,x[t:end],y[t:end],cw,h,backward=True,learn_leaks=learn_leaks,focal=recipe=='phase_focal',**({'readout_only':True} if precision_readout else {}))
            alpha_grad=dh[shape.n:].copy() if learn_leaks else np.zeros(shape.n)
            if train_aux:
                aux_grad=np.zeros_like(aux_weights)
                for ai in range(3):
                    ap=p.copy();ap[offset:]=aux_weights[ai]
                    aux_cw=np.array([1.,8.,1.,1.,1.,1.]) if inlet_recipe and ai==0 else None
                    al,ah,_,ag,ad=run(shape,ap,x[t:end],data['aux'][ai,t:end],aux_cw,h=before,backward=True,learn_leaks=learn_leaks)
                    if not np.array_equal(ah,h):raise AssertionError('auxiliary head changed recurrent state')
                    g[:offset]+=.25*ag[:offset];aux_grad[ai]=ag[offset:];aux_losses.append(al)
                    if learn_leaks:alpha_grad+=.25*ad[shape.n:]
                if inlet_recipe:aux_grad[0]=0
            norm=float(np.linalg.norm(g));norms.append(norm);losses.append(loss)
            if not np.isfinite(norm+loss):raise FloatingPointError((shape.name,profile,seed,epoch))
            g*=trainable;g/=max(1.,norm);step+=1;m=.9*m+.1*g;v=.999*v+.001*g*g
            p-=lr*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8);np.clip(p,-7.99,7.99,out=p)
            if learn_leaks:
                alpha_grad*=alpha_mask;alpha_grad/=max(1.,float(np.linalg.norm(alpha_grad)))
                alpha_step+=1;alpha_m=.9*alpha_m+.1*alpha_grad;alpha_v=.999*alpha_v+.001*alpha_grad*alpha_grad
                shape.leaks-=1e-5*(alpha_m/(1-.9**alpha_step))/(np.sqrt(alpha_v/(1-.999**alpha_step))+1e-8)
                np.clip(shape.leaks,1/64,1.,out=shape.leaks)
            if train_aux:
                aux_grad/=max(1.,float(np.linalg.norm(aux_grad)))
                aux_m=.9*aux_m+.1*aux_grad;aux_v=.999*aux_v+.001*aux_grad*aux_grad
                aux_weights-=lr*(aux_m/(1-.9**step))/(np.sqrt(aux_v/(1-.999**step))+1e-8)
        exposure+=len(x)
        row=dict(epoch=epoch,step=step,exposure_ticks=exposure,split=split,lr=lr,window=window,
                 train_loss=float(np.mean(losses)),gradient_norm=float(np.mean(norms)),elapsed_call=time.monotonic()-started)
        row['training_objective']='focal_gamma2' if recipe=='phase_focal' else 'weighted_cross_entropy'
        if train_aux:row['offchip_auxiliary_loss']=float(np.mean(aux_losses))
        if epoch%5==0 or epoch==target:
            if precision_recipe:
                dl,precision_score=evaluate_recipe(shape,p)
            elif extended_recipe:dl,logits=evaluate_stream(shape,p,dev,cw)
            else:dl,_,logits,_,_=run(shape,p,dev['x'],dev['labels'],cw)
            row.update(precision_score if precision_recipe else metrics(dev,logits.argmax(1)));row['dev_loss']=dl
            if curriculum:
                row['curriculum_probes']={}
                for probe in ('simple_dev','nominal_dev'):
                    d=train[probe];z=run(shape,p,d['x'])[2]
                    row['curriculum_probes'][probe]=metrics(d,z.argmax(1))
            if best is None or key(row)>key(best):best=dict(row)
        path=folder/f'epoch_{epoch:04d}.npz'
        tmp=path.with_suffix('.pending.npz')
        np.savez_compressed(tmp,p=p,m=m,v=v,ending_state=h,aux_weights=aux_weights,aux_m=aux_m,aux_v=aux_v,
            leaks=shape.leaks,alpha_m=alpha_m,alpha_v=alpha_v,alpha_step=alpha_step,
            metadata=json.dumps(dict(epoch=epoch,step=step,exposure=exposure,lr=lr,window=window,
                next_epoch=epoch+1,state_policy='cold only at explicit independent-stream boundaries; continuous through every stream and its messages',
                next_mixed_index=max(0,epoch-10)%12,recipe=recipe,
                initialization='recipe-specific initialization recorded in batch source snapshot and FOLLOWUPS.md',
                offchip_auxiliary_heads=3 if train_aux else 0,frozen_parameter_indices=np.flatnonzero(trainable==0).tolist())))
        tmp.replace(path)
        with journal.open('a') as f:f.write(json.dumps(row)+'\n')
        history.append(row)
    selected=folder/f"epoch_{best['epoch']:04d}.npz"
    chosen=np.load(selected,allow_pickle=False)
    np.savez_compressed(folder/'selected.npz',p=chosen['p'],leaks=chosen['leaks'] if 'leaks' in chosen else shape.leaks)
    blocks=[r for r in history if r['epoch']%30==0 and 'dev_loss' in r]
    improving=len(blocks)<2 or (blocks[-1]['message_accuracy']>blocks[-2]['message_accuracy'] or
        blocks[-1]['boundary_f1']>=blocks[-2]['boundary_f1']+.01 or blocks[-1]['dev_loss']<blocks[-2]['dev_loss']*.98)
    result=dict(shape=shape.name,construction=kwargs,profile=profile,seed=seed,recipe=recipe,epochs=target,
        selected_epoch=best['epoch'],selected=best,checkpoint=str(selected),class_weights=cw.tolist(),
        status='training_limited' if improving else 'block_complete_not_capacity_proof',exposure_ticks=exposure)
    result['development_distribution']='precision_v2' if recipe.endswith(('_v2','_v3','_v4')) else 'precision' if precision_recipe else 'extended' if extended_recipe else 'original'
    if enlarged_recipe:result['development_distribution']='precision_v2_plus_corners_v4_plus_startup_v5'
    if (folder/'warm_start.json').exists():result['warm_start']=json.loads((folder/'warm_start.json').read_text())
    write_json(folder/f'block_{target:04d}.json',result)
    return result
