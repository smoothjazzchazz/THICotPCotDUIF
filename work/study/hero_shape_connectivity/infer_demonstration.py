"""Receive raw sampled lanes with a frozen demonstration; labels are never read."""
import argparse,hashlib,importlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
from .run import digest
from .train import write_json


def infer(manifest,profile,input_path,arithmetic='float'):
    config=json.loads(manifest.read_text());entry=next(e for e in config['entries'] if e['profile']==profile)
    source=Path(config['frozen_source']);frozen=json.loads((source.parent/'freeze.json').read_text())
    for name,expected in frozen['source_hashes'].items():assert digest(source/name)==expected,('source changed',name)
    weights=manifest.parent/entry['weight_file'];assert digest(weights)==entry['weight_sha256']
    package='hero_frozen_'+hashlib.sha256(str(source.resolve()).encode()).hexdigest()[:16]
    if package not in sys.modules:
        spec=importlib.util.spec_from_file_location(package,source/'__init__.py',submodule_search_locations=[str(source)])
        module=importlib.util.module_from_spec(spec);sys.modules[package]=module;spec.loader.exec_module(module)
    shapes=importlib.import_module(package+'.shapes');runtime=importlib.import_module(package+'.runtime');confirmation=importlib.import_module(package+'.confirm');assembly=importlib.import_module(package+'.vendor.data')
    with np.load(input_path,allow_pickle=False) as data:lines=data['lines'].copy()
    if lines.ndim!=2 or lines.shape[1]!=3 or not len(lines) or not np.isin(lines,[0,1]).all():raise ValueError('input requires a nonempty Nx3 array named lines containing only0/1 sampled lanes')
    sh=shapes.make_shape(**entry['construction']);a=np.load(weights,allow_pickle=False);sh.leaks=a['leaks'];p=a['p']
    if arithmetic=='float':
        receiver=runtime.Receiver(sh,p);events=[]
        for start in range(0,len(lines),8192):events.extend(receiver.samples(lines[start:start+8192]))
    else:
        x=shapes.features(lines)[0];kinds=confirmation.infer(sh,p,x,True);events=runtime.events(runtime.pulses(kinds))
    accepted,rejected=assembly.assemble(events,profile)
    return dict(shape=config['shape'],profile=profile,seed=entry['seed'],arithmetic=arithmetic,input_samples=len(lines),weight_sha256=entry['weight_sha256'],events=events,accepted_messages=accepted,rejected_event_groups=rejected,
        interface='raw lanes enter the frozen receiver; only learned events enter assembly; no input labels, truth, boundaries or decoder state are consumed')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--profile',required=True);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--arithmetic',choices=['float','quantized'],default='float');a=ap.parse_args()
    if a.output.exists():raise ValueError('choose a new output file; existing output is preserved')
    result=infer(a.manifest,a.profile,a.input,a.arithmetic);write_json(a.output,result)
    print(json.dumps(dict(samples=result['input_samples'],events=len(result['events']),accepted_messages=len(result['accepted_messages']),output=str(a.output))))
