"""Spend extra fitting only on configurations that still miss strict gates."""
import argparse
import json
from .run import ROOT,batch_jobs
from .shapes import make_shape,SEEDS


def passes(r):
    return r['message_accuracy']==1 and r['boundary_errors']==0 and r['invalid_accepted']==0 and r['background_accepted']==0


def jobs(root,action):
    output=[]
    for kwargs in json.loads((ROOT/'phase_route_candidates.json').read_text()):
        sh=make_shape(**kwargs)
        for profile in ('uart_n','uart_e'):
            for seed in SEEDS:
                folder=root/'models'/'phase_profile_fresh'/sh.name/profile/str(seed)
                current=json.loads((folder/'block_0060.json').read_text())
                if passes(current['selected']):continue
                if action=='refine':output.append((str(root),kwargs,profile,seed,120,'phase_profile_fresh'))
                else:
                    source=root/'models'/'phase_ring_fixed'/sh.name/profile/str(seed)/'block_0600.json'
                    if not passes(json.loads(source.read_text())['selected']):output.append((str(root),kwargs,profile,seed,1200,'phase_ring_fixed'))
    return output

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['refine','pretrain']);ap.add_argument('--workers',type=int,default=6);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';selected=jobs(root,a.action)
    print('Unresolved jobs selected by the common rule:',len(selected),flush=True)
    batch_jobs(root,selected,a.workers,'adaptive_fresh120' if a.action=='refine' else 'adaptive_fixed1200')
