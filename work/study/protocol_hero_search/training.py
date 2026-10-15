"""Resumable off-chip sparse BPTT/Adam, with complete-message checkpoint selection."""
import json
import time
import traceback
from pathlib import Path
import numpy as np
from .shapes import make_shape,initialize,PROFILES
from .network import run
from .data import score


def write_json(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def load_data(root,profile,split):
    base=Path(root)/'data'/f'{profile}_{split}'
    a=dict(np.load(base.with_suffix('.npz'),allow_pickle=False))
    a.update(json.loads(base.with_suffix('.json').read_text()))
    return a


def key(row):
    return (row['message_accuracy'],-row['boundary_errors'],
            -row['invalid_accepted']-row['background_accepted'],-row['false_events'],-row['dev_loss'])


def improved(old,new):
    return (new['message_accuracy']>old['message_accuracy'] or
            new['boundary_f1']>=old['boundary_f1']+.01 or
            (new['dev_loss']<old['dev_loss'] and new['dev_loss']<=old['dev_loss']*.98))


def checkpoint(path,p,m,v,h,epoch,step,exposure,lr,window):
    temporary=path.with_suffix('.pending.npz')
    np.savez_compressed(temporary,p=p,m=m,v=v,ending_state=h,
                        metadata=json.dumps(dict(epoch=epoch,step=step,exposure=exposure,lr=lr,window=window,
                            next_epoch=epoch+1,next_chunk=0,state_policy='new independent stream at epoch start; continuous within stream')))
    temporary.replace(path)


def fit(job):
    root,variant,n,profile,seed,regime,stage=job
    root=Path(root);shape=make_shape(variant,n)
    directory=root/'models'/shape.name/profile/f'{regime}_{seed}'
    directory.mkdir(parents=True,exist_ok=True)
    if (root/'freeze.json').exists():raise ValueError('training after freeze prohibited')
    done=directory/f'{stage}_done.json'
    if done.exists():return json.loads(done.read_text())
    try:
        train={s:load_data(root,profile,s) for s in ('clean','patterns','mixed')}
        dev=load_data(root,profile,'dev')
        counts=np.bincount(train['mixed']['labels'],minlength=6)
        cw=np.minimum(16,np.sqrt(max(counts)/np.maximum(1,counts)))
        cw[[3,4,5]]*=1.5
        p=initialize(shape,seed);m=np.zeros_like(p);v=np.zeros_like(p)
        epoch=step=exposure=0;history=[];lr=.003;window=512;stale=0;rescue='none'
        if (directory/'history.json').exists() or (directory/'history.jsonl').exists():
            if (directory/'history.json').exists():history=json.loads((directory/'history.json').read_text())
            journal=directory/'history.jsonl'
            if journal.exists():
                history=[json.loads(line) for line in journal.read_text().splitlines() if line.strip()]
            epoch=history[-1]['epoch']
            with np.load(directory/f'epoch_{epoch:04d}.npz',allow_pickle=False) as a:
                p=a['p'].copy();m=a['m'].copy();v=a['v'].copy();meta=json.loads(str(a['metadata']))
            step=meta['step'];exposure=meta['exposure']
            lr=meta['lr'];window=meta['window'];rescue=history[-1].get('rescue','none')
            controller=directory/'continuation_state.json'
            if controller.exists():
                control=json.loads(controller.read_text())
                if control['epoch']<=epoch:
                    stale=control['stale_blocks'];rescue=control['rescue']
                    lr=control['lr'];window=control['window']
        else:
            checkpoint(directory/'initial.npz',p,m,v,np.zeros(n),0,0,0,lr,window)
        journal=directory/'history.jsonl'
        if not journal.exists():journal.write_text(''.join(json.dumps(row)+'\n' for row in history))
        evaluations=[r for r in history if 'dev_loss' in r]
        best=max(evaluations,key=key) if evaluations else None
        blocks=[r for r in evaluations if r['epoch']%30==0]
        previous_block=blocks[-1] if blocks else None
        started=time.monotonic()
        # Broad-screen fits receive an initial and matched extra 30-epoch block.
        # Finalists continue adaptively until two stale blocks and both rescues.
        target=60 if stage=='screen' else None
        while target is None or epoch<target:
            epoch+=1
            split='clean' if epoch<=5 else 'patterns' if epoch<=10 else 'mixed'
            data=train[split];x=data['x'];y=data['labels'];h=np.zeros(n)
            losses=[];gradnorm=[];groupnorm=[]
            for begin in range(0,len(x),window):
                loss,h,_,g,_=run(shape,p,x[begin:begin+window],y[begin:begin+window],cw,h,
                                backward=True,readout_only=regime=='esn')
                norm=float(np.linalg.norm(g))
                if not np.isfinite(norm+loss):raise FloatingPointError('nonfinite loss or gradient')
                groupnorm.append([float(np.linalg.norm(g[:len(shape.src)])),float(np.linalg.norm(g[len(shape.src):len(shape.src)+n])),float(np.linalg.norm(g[len(shape.src)+n:]))])
                g/=max(1.,norm);step+=1
                m=.9*m+.1*g;v=.999*v+.001*g*g
                p-=lr*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8)
                np.clip(p,-7.99,7.99,out=p)
                losses.append(loss);gradnorm.append(norm)
            exposure+=len(x)
            row=dict(epoch=epoch,steps=step,exposure_ticks=exposure,split=split,lr=lr,window=window,
                     train_loss=float(np.mean(losses)),gradient_norm_mean=float(np.mean(gradnorm)),
                     gradient_groups_mean=np.mean(groupnorm,axis=0).tolist(),rescue=rescue,
                     elapsed_this_call=time.monotonic()-started)
            if epoch%5==0:
                dl,_,logits,_,_=run(shape,p,dev['x'],dev['labels'],cw)
                row.update(score(dev,logits.argmax(1)));row['dev_loss']=dl
                if best is None or key(row)>key(best):best=dict(row)
            history.append(row)
            checkpoint(directory/f'epoch_{epoch:04d}.npz',p,m,v,h,epoch,step,exposure,lr,window)
            with journal.open('a') as f:f.write(json.dumps(row)+'\n')
            if epoch%30==0:write_json(directory/'history.json',history)
            if epoch%30==0:
                progress=previous_block is None or improved(previous_block,row)
                stale=0 if progress else stale+1;previous_block=dict(row)
                write_json(directory/'progress.json',dict(epoch=epoch,stale_blocks=stale,rescue=rescue,best_epoch=best['epoch'],latest=row))
                if target is None and stale>=2:
                    if rescue=='none':rescue='lower_learning_rate';lr=.0003;stale=0
                    elif rescue=='lower_learning_rate':rescue='longer_window';window=1024;stale=0
                    else:break
                write_json(directory/'continuation_state.json',dict(epoch=epoch,stale_blocks=stale,
                           rescue=rescue,lr=lr,window=window))
                # Once both rescues have run, two stale blocks establish recipe plateau.
        best_path=directory/f"epoch_{best['epoch']:04d}.npz"
        with np.load(best_path,allow_pickle=False) as a: np.savez_compressed(directory/'selected.npz',p=a['p'])
        recent=[r for r in history if r['epoch']%30==0]
        improving=len(recent)<2 or improved(recent[-2],recent[-1])
        result=dict(shape=shape.name,variant=variant,nodes=n,profile=profile,seed=seed,regime=regime,
                    stage=stage,epochs=epoch,selected_epoch=best['epoch'],selected=best,
                    status='training_limited' if stage=='screen' and improving else
                           'screen_budget_complete_not_capacity' if stage=='screen' else 'recipe_plateau_after_rescues',
                    class_weights=cw.tolist(),exposure_ticks=exposure,shape_sha256=shape.config()['shape_sha256'],
                    checkpoint=str(best_path),demonstration_weights=True)
        write_json(done,result);return result
    except Exception:
        write_json(directory/f'{stage}_failure.json',dict(job=list(job),traceback=traceback.format_exc()))
        raise
