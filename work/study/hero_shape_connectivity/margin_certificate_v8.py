"""Numerical margin bound for one fixed learned representation, not a proof gate."""
import json,sys,shutil
import numpy as np
from .run import ROOT,digest
sys.path.insert(0,str(ROOT/'runs/connectivity01/dependencies'))
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree
from .hard_readout import margin
from .train import write_json


if __name__=='__main__':
    root=ROOT/'runs/connectivity01';source=next((root/'models/phase_linear_closure_v8').glob('*/uart_n/131/epoch_0003.npz'))
    out=root/'diagnostics/margin_certificate_v8_n131';out.mkdir(exist_ok=True)
    source_copy=out/'margin_certificate_v8_at_run.py'
    if source_copy.exists():assert digest(source_copy)==digest(__file__)
    else:shutil.copy2(__file__,source_copy)
    a=np.load(source);x=a['support_x'];y=a['support_y'];ids=a['support_ids'];n,d=x.shape;size=6*d
    owners=np.repeat(np.arange(n),5);target=np.repeat(y,5)
    competitors=np.broadcast_to(np.arange(6),(n,6))[np.arange(6)[None,:]!=y[:,None]]
    indices=np.c_[target[:,None]*d+np.arange(d),competitors[:,None]*d+np.arange(d),np.full(5*n,size)].ravel()
    values=np.c_[-x[owners],x[owners],np.ones(5*n)].ravel();indptr=np.arange(0,len(values)+1,2*d+1)
    matrix=csr_matrix((values,indices,indptr),shape=(5*n,size+1))
    solved=linprog(np.r_[np.zeros(size),-1.],A_ub=matrix,b_ub=np.zeros(5*n),bounds=[(-7.99,7.99)]*size+[(None,None)],method='highs',
        options=dict(time_limit=300,primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
    report=dict(source=str(source),source_sha256=digest(source),source_code_sha256=digest(source_copy),states=n,success=bool(solved.success),status=int(solved.status),message=solved.message,
        scope='finite retained canonical training states, fixed learned state equations, existing affine outputs, weights bounded7.99; numerical diagnostic, not physical-shape impossibility or formal verification')
    if solved.x is not None:
        w=solved.x[:size].reshape(6,d);m=margin(x,y,w)
        report.update(claimed_margin=float(solved.x[-1]),verified_minimum_margin=float(m.min()),support_errors=int((m<=0).sum()),max_constraint_residual=float(np.max(matrix@solved.x)))
        lam=np.maximum(0.,-solved.ineqlin.marginals);total=float(lam.sum())
        if total>0:
            lam/=total;residual=np.asarray(matrix[:,:size].T@lam).ravel()
            report.update(nonnegative_dual_sum=float(lam.sum()),dual_residual_l1=float(np.abs(residual).sum()),numerical_margin_upper_bound=float(7.99*np.abs(residual).sum()),
                bound_derivation='nonnegative weighted constraint sum gives margin <=7.99*L1(weight coefficient residual); reported floating arithmetic is not a formal certificate')
            np.savez_compressed(out/'solution_and_dual.npz',weights=w,row_multipliers=lam,weight_residual=residual)
    closest=None
    for label in np.unique(y):
        left=np.flatnonzero(y==label);right=np.flatnonzero(y!=label)
        distance,at=cKDTree(x[right,:-1]).query(x[left,:-1],k=1);local=int(np.argmin(distance));i=int(left[local]);j=int(right[at[local]])
        if closest is None or distance[local]<closest['l2']:
            delta=np.abs(x[i,:-1]-x[j,:-1]);closest=dict(i=i,j=j,labels=[int(y[i]),int(y[j])],ids=[int(ids[i]),int(ids[j])],l2=float(distance[local]),linf=float(delta.max()),l1=float(delta.sum()),pairwise_margin_bound=float(7.99*delta.sum()),bitwise_identical=bool(np.array_equal(x[i],x[j])))
    report['nearest_opposite_label_pair']=closest;write_json(out/'result.json',report);print(json.dumps(report),flush=True)
