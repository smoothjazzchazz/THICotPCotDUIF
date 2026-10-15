"""Keep all previous development and add separately generated startup cases."""
from .corner_evaluate import evaluate as corner_evaluate


def evaluate(sh,p,root,profile,cw,cache=None):
    paths=[('startup_'+f.stem,f) for f in sorted((root/'data_startup_dev_v5'/profile).glob('*.json'))]
    if len(paths)!=320:raise ValueError('all320 independent startup cases required')
    return corner_evaluate(sh,p,root,profile,cw,cache,paths)
