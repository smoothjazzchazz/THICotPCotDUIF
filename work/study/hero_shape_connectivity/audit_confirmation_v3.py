"""Check frozen provenance, physical identities, raw-data order and causal replay artifacts."""
import argparse,importlib,json,sys
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .train import write_json


def audit(label):
    folder=(ROOT/'runs/connectivity01/confirmations'/label).resolve();config=json.loads((folder/'freeze.json').read_text());policy=json.loads((folder/'startup_semantics.json').read_text());topologies=json.loads((folder/'topologies.json').read_text())
    for name,expected in config['source_hashes'].items():assert digest(folder/'source'/name)==expected,('source changed',name)
    sys.path.insert(0,str(folder));shapes=importlib.import_module('source.shapes');registry=importlib.import_module('source.topology_registry')
    contracts=[]
    for entry in config['entries']:
        path=folder/entry['weight_path'];assert digest(path)==entry['weight_sha256'];a=np.load(path);shape=shapes.make_shape(**entry['construction'])
        assert a['p'].shape==(shape.parameters,) and np.isfinite(a['p']).all();assert np.array_equal(a['leaks'],entry['configured_leaks'])
        assert registry.identity(shape)==topologies[shape.name]['physical_sha256']
        if getattr(shape,'nonlinear_readout',False):
            assert shape.n==64 and np.all(a['leaks'][48:]==1),'current readout must not introduce hidden memory'
            assert not np.any(shape.src>=48) and np.all(shape.delay[shape.dst>=48]==0)
        row=dict(profile=entry['profile'],seed=entry['seed'],shape=shape.name,weights_sha256=digest(path),physical_sha256=registry.identity(shape))
        for arithmetic in ('float','quantized'):
            evidence=folder/'results'/shape.name/entry['profile']/f'{arithmetic}_{entry["seed"]}'/'replay_audit.json'
            values=json.loads(evidence.read_text());assert all(values.values()),('causal/chunk audit',evidence);row[arithmetic]=values
        contracts.append(row)
    freeze_time=max((folder/name).stat().st_mtime_ns for name in ('freeze.json','topologies.json','startup_semantics.json'))
    files=[p for p in (folder/'data').iterdir() if p.suffix in ('.json','.npz') and p.name!='manifest.json']
    assert all(p.stat().st_mtime_ns>=freeze_time for p in files),'fresh files predate completed freeze'
    for scope in ('','regression'):
        base=folder/scope
        for name,expected in json.loads((base/'data_hashes.json').read_text()).items():assert digest(base/'data'/name)==expected,('data changed',scope,name)
    assert json.loads((folder/'data_contract.json').read_text())['pass_all']
    write_json(folder/'complete_contract_audit.json',dict(source_files_checked=len(config['source_hashes']),weight_configurations=len(contracts),fresh_waveform_and_metadata_files=len(files),all_fresh_files_postdate_completed_freeze=True,physical_and_causal_contracts=contracts,regression_sources=policy.get('regression_sources',[dict(path=policy['regression_source'])]),scope='model-level provenance, exact masks, finite weights, independent payload/count oracle, causal/chunk runtime; not a hardware gate'))
    print('Verified',label,len(contracts),'configurations and',len(files),'fresh waveform/metadata files',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);args=ap.parse_args();audit(args.label)
