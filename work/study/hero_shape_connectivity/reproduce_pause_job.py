"""Actually rerun one frozen pause-fitting job in a fresh isolated output directory."""
import argparse,importlib,json,sys
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .train import write_json


def reproduce(index,output):
    root=ROOT/'runs/connectivity01';label='clocked_pause_v20_all12';snapshot=root/'batch_sources'/label
    hashes=json.loads((root/f'{label}_source_hashes.json').read_text())
    for name,expected in hashes.items():assert digest(snapshot/name)==expected
    jobs=json.loads((root/f'{label}_jobs.json').read_text());job=jobs[index]
    output=output.resolve();output.mkdir(parents=True,exist_ok=False)
    # The fitting entry point only reads these shared inputs. Model outputs and
    # newly computed state caches live under the new directory, never the source.
    for name in ('dependencies','data_clocked_pause_v20'):(output/name).symlink_to(root/name,target_is_directory=True)
    write_json(output/'reproduction_inputs.json',dict(label=label,job_index=index,original_job=job,source_hashes=hashes,shared_input_directories=['dependencies','data_clocked_pause_v20']))
    sys.path.insert(0,str(snapshot.parent));module=importlib.import_module(label+'.clocked_pause_v20')
    reproduced=module.fit([str(output),*job[1:]])
    original=root/'models/phase_clocked_pause_v20'/reproduced['shape']/reproduced['profile']/str(reproduced['seed'])/'block_0012.json';record=json.loads(original.read_text())
    a=np.load(reproduced['checkpoint']);b=np.load(record['checkpoint']);weights_equal=bool(np.array_equal(a['p'],b['p']));leaks_equal=bool(np.array_equal(a['leaks'],b['leaks']))
    fields=('exact_messages','valid_messages','boundary_errors','invalid_accepted','background_accepted')
    score_equal=all(reproduced['selected'][k]==record['selected'][k] for k in fields)
    result=dict(weights_bitwise_equal=weights_equal,leaks_bitwise_equal=leaks_equal,development_scores_equal=score_equal,
                maximum_weight_difference=float(np.max(np.abs(a['p']-b['p']))),same_selected_epoch=reproduced['selected_epoch']==record['selected_epoch'],
                original_block=str(original),reproduced_checkpoint=reproduced['checkpoint'],scope='actual repeat of independent pause-pool scan, output fitting and scalar development from frozen same-seed source; not new confirmation')
    write_json(output/'reproduction_verification.json',result)
    assert weights_equal and leaks_equal and score_equal and result['same_selected_epoch'],result
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--job-index',type=int,default=14);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();reproduce(a.job_index,a.output)
