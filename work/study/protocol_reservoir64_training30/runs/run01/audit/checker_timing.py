"""Explain retained conventional-checker misses without altering labels or samples."""
import json
from pathlib import Path
import numpy as np
from work.study.protocol_reservoir64.data import load_split
from work.study.protocol_reservoir64.checkers import uart_decode

root=Path(__file__).resolve().parents[1]
rows=[]
for profile in ('uart_n','uart_e'):
    for split in ('train','dev'):
        for stream in load_split(root,profile,split):
            for tx in stream['metadata']['transactions']:
                check=tx['independent_check']
                if not check['clean'] or check['exact']: continue
                a=tx['offset'];line=stream['lines'][a:a+tx['ticks'],0]
                labels=stream['labels'][a:a+tx['ticks']]
                checker=uart_decode(line,profile=='uart_e',16*tx['ratio'])
                drift=[]
                for frame in tx['frames']:
                    centers=np.flatnonzero(labels[frame['start']:frame['end']+1])+frame['start']
                    estimated=np.array([frame['start']+int((c+.5)*16*tx['ratio']) for c in range(len(centers))])
                    drift.extend((estimated-centers).tolist())
                rows.append(dict(profile=profile,split=split,seed=tx['seed'],jitter=tx['jitter'],ratio=tx['ratio'],
                    intended=tx['expected'],checker=checker,
                    sampling_center_offset_min=min(drift),sampling_center_offset_max=max(drift),
                    independent_exact_cell_label_audit='passed in preflight.json',
                    interpretation='Checker assumes one fixed cell period; cumulative per-cell jitter changes true centers. Retained as a checker limitation, not a reason to omit these examples or relax final scoring.'))
(root/'audit/checker_timing.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
