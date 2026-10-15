"""Audit each retained model against its original initialization and frozen core."""
import hashlib
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import ARCHITECTURE_HASH, MASK, initial_weights, load_weights

root=Path(__file__).resolve().parents[1]
rows=[]
for path in sorted((root/'models').glob('*/*/fit.json')):
    fit=json.loads(path.read_text());directory=path.parent
    seed=fit['seed'];initial,meta=load_weights(directory/'initial.npz')
    for k,v in initial_weights(seed).items(): np.testing.assert_array_equal(initial[k],v)
    epochs=[]
    for epoch in range(1,31):
        w,meta=load_weights(directory/f'epoch_{epoch:02d}.npz')
        assert np.count_nonzero(w['wh']*(1-MASK))==0
        assert all(np.all(np.isfinite(v)) and np.max(abs(v))<=7.99 for v in w.values())
        assert meta['epoch']==epoch
        epochs.append(epoch)
    selected,meta=load_weights(directory/'selected.npz')
    expected,_=load_weights(directory/f"epoch_{fit['best_epoch']:02d}.npz")
    for k in expected: np.testing.assert_array_equal(selected[k],expected[k])
    rows.append(dict(profile=path.parent.parent.name,variant=directory.name,seed=seed,
        epochs_checked=epochs,architecture_hash=ARCHITECTURE_HASH,
        exact_fresh_initialization=True,unchanged_topology=True,selected_checkpoint_exact=True,
        selected_epoch=fit['best_epoch'],parameter_changes=fit['parameter_l2_changes']))
assert len(rows)==12
(root/'audit/architecture_check.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Verified all 360 epochs, 12 exact initializations, and 12 selected checkpoints.')
