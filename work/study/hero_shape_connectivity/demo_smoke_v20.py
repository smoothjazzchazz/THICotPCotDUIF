"""Exercise all frozen demonstration profiles from raw lanes only."""
import json,shutil
from pathlib import Path
import numpy as np
from .run import ROOT,digest
from .data import build
from .shapes import PROFILES
from .train import write_json
from .infer_demonstration import infer


def verify():
    root=ROOT/'runs/connectivity01';frozen=root/'confirmations/readout_cost_full_v3b';freeze=json.loads((frozen/'freeze.json').read_text());topologies=json.loads((frozen/'topologies.json').read_text())
    output=root/'raw_demonstration_verification_v20';output.mkdir(exist_ok=True);rows=[]
    for name,top in topologies.items():
        folder=output/top['physical_sha256'][:12];folder.mkdir(exist_ok=True);entries=[]
        for profile in PROFILES:
            e=next(e for e in freeze['entries'] if (e['shape'],e['profile'],e['seed'])==(name,profile,11));source=frozen/e['weight_path'];target=folder/(profile+'.npz');assert digest(source)==e['weight_sha256']
            if target.exists():assert digest(target)==e['weight_sha256']
            else:shutil.copy2(source,target)
            entries.append(dict(profile=profile,seed=11,weight_file=target.name,weight_sha256=e['weight_sha256'],construction=e['construction'],configured_leaks=e['configured_leaks']))
        manifest=folder/'manifest.json';write_json(manifest,dict(shape=name,physical_sha256=top['physical_sha256'],frozen_source=str(frozen/'source'),entries=entries,purpose='seed11 raw-interface verification; qualification is separate'))
        for pi,profile in enumerate(PROFILES):
            stream=build(profile,421000000+pi*10000,messages=16);raw=folder/(profile+'_raw_lines.npz')
            if not raw.exists():np.savez_compressed(raw,lines=stream['lines'])
            else:assert np.array_equal(np.load(raw)['lines'],stream['lines'])
            # Oracle truth remains outside the receiver input file. Inference
            # consumes only the Nx3 raw lines and the frozen demonstration.
            for arithmetic in ('float','quantized'):
                result=infer(manifest,profile,raw,arithmetic);matched=result['accepted_messages']==stream['truth']
                write_json(folder/f'{profile}_{arithmetic}.json',result)
                rows.append(dict(shape=name,profile=profile,arithmetic=arithmetic,seed=11,samples=len(stream['lines']),accepted=len(result['accepted_messages']),raw_only_payload_match=matched,weight_sha256=result['weight_sha256']))
                assert matched,rows[-1]
    write_json(output/'verification.json',dict(configurations=rows,pass_all=True,scope='28 raw-line interface smoke tests on independent family421000000; not a substitute for qualification or an additional fresh finalist selection'))
    print('Verified raw-line demonstration interface for',len(rows),'shape/profile/arithmetic combinations',flush=True)


if __name__=='__main__':verify()
