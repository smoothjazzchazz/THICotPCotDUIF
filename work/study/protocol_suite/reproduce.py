"""Cold refit/reconfirmation in a new suite-local package, retaining original evidence."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from .run import ROOT,save


def main():
    p=argparse.ArgumentParser()
    p.add_argument('name',help='New directory name below protocol_suite/reproductions/')
    p.add_argument('--all-development',action='store_true')
    args=p.parse_args()
    if not args.name or Path(args.name).name!=args.name or args.name in ('.','..'):
        p.error('Use a single new directory name')
    base=ROOT/'reproductions'/args.name
    package=base/'replica'
    package.mkdir(parents=True,exist_ok=False)
    for src in [*ROOT.glob('*.py'),ROOT/'PLAN.md',ROOT/'run.sh']:
        shutil.copyfile(src,package/src.name)
    shutil.copytree(ROOT/'configs',package/'configs')
    for d in ('artifacts','tmp','cache/matplotlib'):
        (package/d).mkdir(parents=True,exist_ok=True)
    env={**os.environ,'PYTHONPATH':str(base),'PYTHONDONTWRITEBYTECODE':'1',
         'TMPDIR':str(package/'tmp'),'MPLCONFIGDIR':str(package/'cache/matplotlib'),
         'XDG_CACHE_HOME':str(package/'cache'),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
    commands=[]
    if args.all_development:
        commands=[['run','screen'],['run','refine','--config',str(package/'configs/refine.json'),'--seeds','11,29,47'],
                  ['run','refine','--name','representation_v2','--config',str(package/'configs/representation.json'),'--seeds','11,29,47'],
                  ['run','refine','--name','final_development','--config',str(package/'configs/final_development.json')]]
    commands += [['confirmation','freeze'],['confirmation','evaluate'],['analyze'],['verify','replay']]
    for index,command in enumerate(commands):
        cmd=[sys.executable,'-B','-m','replica.'+command[0],*command[1:]]
        with (base/f'{index:02d}_{command[0]}.log').open('w') as log:
            subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        print('reproduced',' '.join(command),flush=True)
    # Exact metrics/traces are the reproducibility claim; timestamps/source lists
    # differ because this is an independently launched, suite-local execution.
    old=ROOT/'artifacts/confirmation'
    new=package/'artifacts/confirmation'
    mismatches=[]
    for src in old.glob('*_predictions.json.gz'):
        from .run import read
        if read(src)!=read(new/src.name):
            mismatches.append(src.name)
    for src in old.glob('*_metrics.json'):
        from .run import read
        if read(src)!=read(new/src.name):
            mismatches.append(src.name)
    save(base/'comparison.json',{'mismatches':mismatches,'passed':not mismatches,
                               'replayed_models':120,'note':'Fresh refit with the same frozen seeds; reproduction, not additional independent confirmation.'})
    if mismatches:
        raise RuntimeError(mismatches)


if __name__=='__main__':
    main()
