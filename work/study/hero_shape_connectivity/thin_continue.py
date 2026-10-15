"""Apply the existing unresolved-seed continuation rule to edge reallocation."""
import json
from .run import ROOT,batch_jobs
from .shapes import make_shape,SEEDS

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';kwargs=json.loads((ROOT/'edge_reallocation_candidates.json').read_text())[0];sh=make_shape(**kwargs);jobs=[]
    for profile in ('uart_n','uart_e'):
        for seed in SEEDS:
            block=root/'models'/'phase_ring_fixed'/sh.name/profile/str(seed)/'block_0600.json';r=json.loads(block.read_text())['selected']
            if r['message_accuracy']==1 and r['boundary_errors']==0 and r['invalid_accepted']==0 and r['background_accepted']==0:continue
            jobs.append((str(root),kwargs,profile,seed,1200,'phase_ring_fixed'))
    batch_jobs(root,jobs,6,'thin_unresolved1200')
