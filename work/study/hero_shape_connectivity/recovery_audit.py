"""Verify that successful readout corrections did not modify recurrence."""
import json
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape
from .train import write_json

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';rows=[]
    for folder in sorted((root/'models'/'phase_recovery_readout').glob('*/*/*')):
        blocks=sorted(folder.glob('block_*.json'))
        if not blocks:continue
        b=json.loads(blocks[-1].read_text());warm=json.loads((folder/'warm_start.json').read_text())
        before=np.load(warm['checkpoint']);after=np.load(b['checkpoint']);sh=make_shape(**b['construction']);offset=len(sh.src)+sh.n
        same_state=bool(np.array_equal(before['p'][:offset],after['p'][:offset]) and np.array_equal(before['leaks'],after['leaks']))
        if not same_state:raise AssertionError('readout correction changed state transition')
        source=warm['selected_source']['extended_development'];dest=b['selected']
        rows.append(dict(shape=sh.name,profile=b['profile'],seed=b['seed'],state_transition_bitwise_unchanged=same_state,
            source_checkpoint=warm['checkpoint'],source_sha256=digest(warm['checkpoint']),selected_checkpoint=b['checkpoint'],selected_sha256=digest(b['checkpoint']),
            selected_epoch=b['selected_epoch'],epochs_spent=b['epochs'],training_ticks=b['exposure_ticks'],
            source_exact=source['exact_messages'],selected_exact=dest['exact_messages'],valid_messages=dest['valid_messages'],
            source_boundary_errors=source['boundary_errors'],selected_boundary_errors=dest['boundary_errors'],
            readout_weight_delta_l2=float(np.linalg.norm(after['p'][offset:]-before['p'][offset:]))))
    write_json(root/'recovery_readout_audit.json',dict(checks=rows,pass_all=all(r['state_transition_bitwise_unchanged'] for r in rows),
        conclusion='same deployed state trajectories; changes arise solely from existing readout weights; this is development evidence, not a general capacity proof'))
    print('Verified unchanged recurrent transitions:',len(rows))
