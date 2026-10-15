"""Resume a recorded batch using its immutable source snapshot and original jobs."""
import argparse,importlib,json,sys
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from .run import ROOT,digest
from .train import write_json

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('label');ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--entry',choices=['train','error_mining','margin_calibrate','window_rescue','hard_margin_v4','stop_margin','startup_margin_v5','startup_core_v5','closure_v6','linear_closure_v7','linear_closure_v8','bit_hold_closure_v9','grid_margin_v10','gated_margin_v11','gated_linear_v12','gated_linear_v13','pruned_readout_v14','pruned_readout_v15','head_learning_v16','pruned_clocked_v17','head_learning_clocked_v18','grid_margin_v19','clocked_pause_v20'],default='train')
    ap.add_argument('--job-index',type=int);a=ap.parse_args()
    root=ROOT/'runs'/'connectivity01';snapshot=root/'batch_sources'/a.label;hashes=json.loads((root/f'{a.label}_source_hashes.json').read_text())
    bad=[name for name,value in hashes.items() if digest(snapshot/name)!=value]
    if bad:raise AssertionError(('frozen batch source changed',bad))
    jobs=json.loads((root/f'{a.label}_jobs.json').read_text());indices=list(range(len(jobs))) if a.job_index is None else [a.job_index]
    if a.entry=='hard_margin_v4':sys.path.insert(0,str(root/'dependencies'))
    sys.path.insert(0,str(snapshot.parent));module=importlib.import_module(a.label+'.'+a.entry);fit=module.fit
    if a.entry in ('head_learning_v16','head_learning_clocked_v18'):
        prepared=set()
        for index in indices:
            job=jobs[index];identity=(job[0],job[2],job[3])
            if identity not in prepared:
                module.bank(Path(job[0]),job[2],job[3],job[6]);prepared.add(identity)
    path=root/f'{a.label}_resumed_ledger.json';result=json.loads(path.read_text()) if path.exists() else dict(label=a.label,entry=a.entry,completed={},failures={})
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        tasks={pool.submit(fit,jobs[i]):i for i in indices}
        for f in as_completed(tasks):
            index=tasks[f]
            try:
                row=f.result();result['completed'][str(index)]=row;result['failures'].pop(str(index),None)
                models=row if isinstance(row,list) else row.get('models',[row])
                for model in models:
                    print(json.dumps(dict(job=index,shape=model['shape'],profile=model['profile'],seed=model['seed'],epochs=model['epochs'],exact=model['selected']['message_accuracy'],boundary=model['selected']['boundary_errors'])),flush=True)
            except Exception as error:
                result['failures'][str(index)]=repr(error);write_json(path,result);raise
            write_json(path,result)
