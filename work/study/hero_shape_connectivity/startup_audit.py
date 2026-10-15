"""Check declared payloads after cold cutting, independently of model scores."""
import json
from .run import ROOT,digest
from .data import load
from .train import write_json


def mismatches(s):
    failures=[]
    for i,g in enumerate(s['groups']):
        if not g['valid']:continue
        accepted=[a for a in s['truth'] if g['start']<=a['start']<g['end']]
        got=[v for a in accepted for seg in a['segments'] for v in seg['bytes'][1:]] if s['profile']=='i2c' else [v for a in accepted for v in a['bytes']]
        if got!=g['payload']:failures.append(dict(group=i,declared_payload=g['payload'],reference_payload=got))
    return failures


if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';rows=[]
    paths=list((root/'confirmations').glob('*/data/*midstream.json'))
    paths+=list((root/'data_precision').glob('*/dev/cold*.json'))
    paths+=list((root/'data_extended').glob('*/dev.json'))
    for path in paths:
        s=load(path.with_suffix(''));bad=mismatches(s)
        rows.append(dict(path=str(path),sha256=digest(path),profile=s['profile'],groups=len(s['groups']),mismatches=bad))
    write_json(root/'startup_payload_audit.json',dict(cases=rows,affected_cases=sum(bool(r['mismatches']) for r in rows),
        issue='cold-cut UART reference can remain out of phase beyond the short gap; declared valid payloads then disagree with oracle truth',
        consequence='startup results and cold-cut training require a corrected observable synchronization interval; no historical result is overwritten',
        correction='new independent version-2 corpus inserts 256 mark-high ticks before scored recovery and asserts every post-cut valid payload'))
    print('Affected cases',sum(bool(r['mismatches']) for r in rows),'of',len(rows))
