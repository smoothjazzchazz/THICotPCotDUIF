"""Reproduce selected pilot trials and retain both epochs and optimizer states.

This is deterministic verification of the pre-main pilots, not additional fitting
of a main candidate or a new recipe selection. The original pilot outputs stay.
"""
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import load_weights,save_weights
from work.study.protocol_reservoir64.training import batch,class_weights,loss_gradient
from .investigation import initialize
from .data import load_split
from .training import MULTIPLIERS,adam_step,save_optimizer,write_json


def replay(output):
    output=Path(output);rows=[]
    for profile in ('uart_n','uart_e'):
        x,y,valid=batch(load_split(output,profile,'train'));x,y,valid=x[:8192],y[:8192],valid[:8192]
        weights=class_weights(y,valid)*MULTIPLIERS
        for recipe in ('previous','memory095','memory105'):
            w=initialize(11,recipe);m,v=({k:np.zeros_like(a) for k,a in w.items()} for _ in range(2));step=0
            dest=output/'investigation/all_epochs'/profile/recipe;dest.mkdir(parents=True,exist_ok=True)
            save_weights(dest/'initial.npz',w,seed=11,recipe=recipe)
            for epoch in (1,2):
                state=np.zeros((12,64))
                for a in range(0,len(x),512):
                    _,state,g=loss_gradient(w,x[a:a+512],y[a:a+512],valid[a:a+512],state,weights)
                    step+=1;adam_step(w,g,m,v,step)
                save_weights(dest/f'epoch_{epoch:02d}.npz',w,epoch=epoch,seed=11,recipe=recipe)
                save_optimizer(dest/f'optimizer_{epoch:02d}.npz',w,m,v,state,epoch,step)
            original,_=load_weights(output/'investigation'/f'{profile}_{recipe}.npz')
            for k in w:np.testing.assert_array_equal(w[k],original[k])
            rows.append(dict(profile=profile,recipe=recipe,exact=True,verification_updates=step))
    write_json(output/'investigation/pilot_replay.json',rows)

if __name__=='__main__':
    import sys
    replay(Path(sys.argv[1]))
