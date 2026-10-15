"""Can a frozen-state readout separate retained training states at any margin?"""
import json,sys
import numpy as np
from .run import ROOT,digest
sys.path.insert(0,str(ROOT/'runs/connectivity01/dependencies'))
from scipy.optimize import linprog
from scipy.sparse import coo_matrix,csr_matrix,hstack,vstack,eye
from .hard_readout import margin
from .train import write_json


def solve(x,y,prior,radius):
    n,d=x.shape;rows=[];cols=[];values=[]
    for i in range(n):
        for other in range(6):
            if other==y[i]:continue
            row=len(rows)//(2*d+1)
            rows.extend([row]*(2*d+1));cols.extend((int(y[i])*d+np.arange(d)).tolist()+(other*d+np.arange(d)).tolist()+[6*d])
            values.extend((-x[i]).tolist()+x[i].tolist()+[1.])
    a=coo_matrix((values,(rows,cols)),shape=(5*n,6*d+1)).tocsr()
    lo=np.maximum(-7.99,prior.ravel()-radius) if radius is not None else np.full(6*d,-7.99)
    hi=np.minimum(7.99,prior.ravel()+radius) if radius is not None else np.full(6*d,7.99)
    c=np.r_[np.zeros(6*d),-1.]
    result=linprog(c,A_ub=a,b_ub=np.zeros(5*n),bounds=list(zip(lo,hi))+[(None,None)],method='highs',
        options=dict(time_limit=300,primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
    record=dict(success=bool(result.success),status=int(result.status),message=result.message,radius=radius,states=n)
    weights=None
    if result.x is not None:
        weights=result.x[:-1].reshape(6,d);m=margin(x,y,weights)
        record.update(claimed_margin=float(result.x[-1]),verified_minimum_margin=float(m.min()),support_errors=int((m<=0).sum()),
            max_constraint_residual=float(np.max(a@result.x)),iterations=int(result.nit),max_weight=float(np.max(np.abs(weights))))
    return record,weights


def minimum_change(x,y,prior,required_margin=.01):
    """Find the smallest L1 output-weight change meeting every retained label."""
    n,d=x.shape;size=6*d;owners=np.repeat(np.arange(n),5);target=np.repeat(y,5)
    competitors=np.broadcast_to(np.arange(6),(n,6))[np.arange(6)[None,:]!=y[:,None]]
    indices=np.c_[target[:,None]*d+np.arange(d),competitors[:,None]*d+np.arange(d)].ravel()
    values=np.c_[-x[owners],x[owners]].ravel();indptr=np.arange(0,len(values)+1,2*d)
    a=csr_matrix((values,indices,indptr),shape=(5*n,size));identity=eye(size,format='csr')
    matrix=vstack([hstack([a,csr_matrix((5*n,size))]),hstack([identity,-identity]),hstack([-identity,-identity])],format='csr')
    rhs=np.r_[np.full(5*n,-required_margin),prior.ravel(),-prior.ravel()]
    result=linprog(np.r_[np.zeros(size),np.ones(size)],A_ub=matrix,b_ub=rhs,
        bounds=[(-7.99,7.99)]*size+[(0,None)]*size,method='highs',
        options=dict(time_limit=300,primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
    if result.success:
        weights=result.x[:size].reshape(prior.shape)
        # Tolerances never substitute for checking the concrete classifier.
        assert margin(x,y,weights).min()>=required_margin-1e-7
        assert np.max(np.abs(weights))<=7.9900001
    return result


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';out=root/'diagnostics/linear_margin_v6';out.mkdir(exist_ok=True);rows=[]
    for profile,seed in [('uart_n',131),('uart_e',47),('uart_e',71)]:
        folder=next((root/'models/phase_closure_v6').glob(f'*/{profile}/{seed}'))
        source=folder/'epoch_0008.npz'
        if not source.exists():raise ValueError(('wait for declared complete closure source',source))
        final=np.load(source);original=np.load(folder/'epoch_0000.npz');prior=original['w'];x=final['support_x'];y=final['support_y']
        for label,radius in [('trust',.25),('full',None)]:
            record,w=solve(x,y,prior,radius);record.update(profile=profile,seed=seed,label=label,source=str(source),source_sha256=digest(source));rows.append(record)
            if w is not None:np.savez_compressed(out/f'{profile}_{seed}_{label}.npz',weights=w)
            write_json(out/f'{profile}_{seed}_{label}.json',record);print(json.dumps(record),flush=True)
    write_json(out/'summary.json',dict(source_sha256=digest(__file__),scope='finite retained training states and frozen learned state equations only; not architecture impossibility or qualification',rows=rows))
