"""Frozen fresh confirmation plus expanded startup and separate v2 regression."""
import argparse,json,shutil
from pathlib import Path
from .run import ROOT,digest
from .confirm import freeze,evaluate
from .confirm_v2 import generate_v2
from .precision_data_v2 import prefix,finish
from .vendor.data import Builder
from .data import save,load,conditions
from .shapes import PROFILES,SEEDS,features,make_shape,specification
from .topology_registry import physical_definition,identity
from .startup_audit import mismatches
from .train import write_json


def startup_case(profile,seed,mode,index):
    if mode=='midframe':b,cut=prefix(profile,seed)
    elif mode=='idle':b=Builder(profile,seed);cut=None
    else:raise ValueError(mode)
    for j in range(8):
        size=64 if j==0 and index%11==0 else int(b.rng.integers(1,9))
        payload=b.rng.integers(0,256,size).tolist()
        if index%5==0:payload=[(0,255,85,170)[index//5%4]]*size
        b.message(payload,conditions(profile)[(index+j)%7])
    if cut is None:
        s=b.finish();s['x']=features(s['lines'])[0];s['seed']=seed
    else:s=finish(b,cut,seed)
    assert len([g for g in s['groups'] if g['valid']])==8
    assert not mismatches(s),'startup payload contract'
    return s


def freeze_v3(root,label,candidates,family,recipe,regression_labels=()):
    # Reserve a new range after all training/development families used here.
    if family<500000000:raise ValueError('v3 confirmation family must start at or above500million')
    for p in (root/'confirmations').glob('*/freeze.json'):
        old=json.loads(p.read_text()).get('seed_family')
        if old is not None and abs(family-old)<10000000:raise ValueError(('confirmation seed range overlaps',p))
    regression_sources=[]
    for prior_label in dict.fromkeys(('full_shape_v2a',*regression_labels)):
        if Path(prior_label).name!=prior_label:raise ValueError('regression label must be a directory name')
        prior=root/'confirmations'/prior_label
        hashes=json.loads((prior/'data_hashes.json').read_text())
        for name,expected in hashes.items():assert digest(prior/'data'/name)==expected,('prior regression changed',name)
        regression_sources.append(dict(label=prior_label,path=str(prior),data_hashes=hashes))
    primary=regression_sources[0]
    out=freeze(root,label,candidates,family,recipe,PROFILES)
    write_json(out/'topologies.json',{make_shape(**kw).name:dict(configuration=specification(make_shape(**kw),kw),physical_definition=physical_definition(make_shape(**kw)),physical_sha256=identity(make_shape(**kw))) for kw in candidates})
    write_json(out/'startup_semantics.json',dict(version=3,observable_sync_high_ticks=256,
        topology_file_sha256=digest(out/'topologies.json'),
        added_cases_per_uart_profile=dict(known_idle=64,midframe=64),valid_groups_per_added_case=8,
        cold_known_idle='ordinary generated17–48 high ticks; zero neural state, no artificial settling prefix',
        midframe='independent unknown cut;256 observable high ticks before scored recovery; no runtime reset',
        qualification='same seeds must pass all fresh and prior-regression conditions; >=5/6 each profile; float and quantized separate',
        regression_source=primary['path'],regression_data_hashes=primary['data_hashes'],regression_sources=regression_sources,
        unchanged='all v2 timing, complete-message, boundary, rejection, recovery, long payload and causality gates'))
    return out


def generate_v3(out):
    config=json.loads((out/'freeze.json').read_text());policy=json.loads((out/'startup_semantics.json').read_text())
    assert policy['version']==3
    generate_v2(out)
    manifest=json.loads((out/'data/manifest.json').read_text());family=config['seed_family']
    for pi,profile in enumerate(config['profiles']):
        if not profile.startswith('uart'):continue
        for mi,mode in enumerate(('idle','midframe')):
            for i in range(64):
                name=f'{profile}_startup_{mode}_{i:03d}';path=out/'data'/name
                if not path.with_suffix('.json').exists():
                    save(path,startup_case(profile,family+6000000+pi*100000+mi*10000+i*100,mode,i))
                manifest.append(dict(name=name,profile=profile,condition=f'startup_{mode}_{i:03d}',kind='independent_startup',required_messages=8))
    write_json(out/'data/manifest.json',manifest)
    write_json(out/'data_hashes.json',{str(p.relative_to(out/'data')):digest(p) for p in (out/'data').iterdir() if p.is_file()})
    audits=[]
    for entry in manifest:
        s=load(out/'data'/entry['name']);bad=mismatches(s);valid=sum(g['valid'] for g in s['groups'])
        assert not bad and valid>=entry['required_messages'],('fresh payload/count contract',entry['name'],bad,valid)
        audits.append(dict(name=entry['name'],valid_messages=valid,payload_mismatches=0))
    write_json(out/'data_contract.json',dict(cases=audits,pass_all=True,scope='independent waveform-parser payload equality and declared per-condition counts'))
    prepare_regression(out,config,policy)


def prepare_regression(out,config,policy):
    """Copy previous suites byte-for-byte, with distinct names in a joint ledger."""
    sources=policy.get('regression_sources',[dict(label=Path(policy['regression_source']).name,
        path=policy['regression_source'],data_hashes=policy['regression_data_hashes'])])
    reg=out/'regression';(reg/'data').mkdir(parents=True,exist_ok=True)
    combined=[];hashes={};multiple=len(sources)>1
    for entry in sources:
        prior=Path(entry['path']);prefix=entry['label']+'__' if multiple else ''
        for name,expected in entry['data_hashes'].items():
            source=prior/'data'/name;assert digest(source)==expected
            if name=='manifest.json' and multiple:continue
            target=reg/'data'/(prefix+name)
            if target.exists():assert digest(target)==expected
            else:shutil.copy2(source,target)
            hashes[prefix+name]=expected
        manifest=json.loads((prior/'data/manifest.json').read_text())
        combined.extend({**item,'name':prefix+item['name'],'condition':prefix+item['condition'],
                         'regression_source':entry['label']} for item in manifest)
    if multiple:
        assert len({e['name'] for e in combined})==len(combined),'regression name collision'
        write_json(reg/'data/manifest.json',combined);hashes['manifest.json']=digest(reg/'data/manifest.json')
    write_json(reg/'data_hashes.json',hashes)
    write_json(reg/'freeze.json',{**config,'entries':[{**e,'weight_path':'../'+e['weight_path']} for e in config['entries']],
        'data_generated_after_freeze':False,'purpose':'previously observed regression suites; never fresh confirmation',
        'original_confirmations':[e['path'] for e in sources]})


def joint_summary(fresh,regression):
    lookup={(r['shape'],r['profile'],r['seed'],r['arithmetic']):r for r in regression}
    if len(lookup)!=len(regression):raise ValueError('duplicate regression result')
    rows=[]
    for r in fresh:
        k=(r['shape'],r['profile'],r['seed'],r['arithmetic']);old=lookup.pop(k)
        rows.append(dict(shape=k[0],profile=k[1],seed=k[2],arithmetic=k[3],fresh_pass=r['pass_all'],
            regression_pass=old['pass_all'],joint_pass=r['pass_all'] and old['pass_all']))
    if lookup:raise ValueError('unmatched regression entries')
    groups={}
    for shape in sorted({r['shape'] for r in rows}):
        for arithmetic in sorted({r['arithmetic'] for r in rows}):
            counts={}
            for profile in PROFILES:
                subset=[r for r in rows if (r['shape'],r['arithmetic'],r['profile'])==(shape,arithmetic,profile)]
                if sorted(r['seed'] for r in subset)!=sorted(SEEDS):raise ValueError('all six seeds of every profile required')
                counts[profile]=sum(r['joint_pass'] for r in subset)
            groups[f'{shape}/{arithmetic}']=dict(passes=counts,qualified=all(n>=5 for n in counts.values()))
    return dict(per_seed=rows,per_shape=groups,criterion='>=5/6 same seeds per profile pass both fresh and prior regression; arithmetic kept separate')


def evaluate_v3(out,workers,arithmetic):
    policy=json.loads((out/'startup_semantics.json').read_text());assert digest(out/'topologies.json')==policy['topology_file_sha256']
    for folder in (out,out/'regression'):
        hashes=json.loads((folder/'data_hashes.json').read_text())
        for name,expected in hashes.items():assert digest(folder/'data'/name)==expected,('data changed',folder,name)
        evaluate(folder,workers,arithmetic)
    fresh=json.loads((out/'ledger.json').read_text());prior=json.loads((out/'regression/ledger.json').read_text())
    assert len(fresh['completed'])==fresh['total'] and len(prior['completed'])==prior['total']
    scored=lambda rows:[r for r in rows if r['arithmetic'] in ('float','quantized')]
    write_json(out/'joint_qualification.json',joint_summary(scored(fresh['completed']),scored(prior['completed'])))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','generate','evaluate']);ap.add_argument('--label',required=True)
    ap.add_argument('--candidates',type=Path);ap.add_argument('--seed-family',type=int);ap.add_argument('--recipe')
    ap.add_argument('--regression-label',action='append',default=[],help='previous failed confirmation to retain alongside the original v2 suite')
    ap.add_argument('--workers',type=int,default=8);ap.add_argument('--arithmetic',default='float,quantized,no_recurrence,no_feedback');a=ap.parse_args()
    root=ROOT/'runs/connectivity01';out=root/'confirmations'/a.label
    if a.action=='freeze':
        if a.seed_family is None:ap.error('choose an unused seed family only after finalist selection')
        freeze_v3(root,a.label,json.loads(a.candidates.read_text()),a.seed_family,a.recipe,a.regression_label)
    elif a.action=='generate':generate_v3(out)
    else:evaluate_v3(out,a.workers,a.arithmetic)
