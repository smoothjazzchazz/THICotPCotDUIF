"""Separate frozen replay outcomes, reference validity, and qualification."""
import json
from .run import ROOT
from .train import write_json
from .qualification import summarize

if __name__=='__main__':
    root=ROOT/'runs'/'connectivity01';summarize(root)
    outcomes=json.loads((root/'qualification_summary.json').read_text())
    lines=['# Frozen confirmation evidence','',
        'The original qualification thresholds remain unchanged. An invalid stimulus/reference contract cannot qualify a shape, even when model events match that reference. Float and integer replay are independent columns. V3 counts require the same seeds to pass fresh and prior-regression suites. [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md) is the current physical-shape summary and demonstration index.','']
    for label in sorted({r['comparison'] for r in outcomes}):
        lines+=['## '+label,'','| Shape | Profile | Float suite passes | Integer suite passes | Valid declared payloads |','| --- | --- | ---: | ---: | --- |']
        for shape in sorted({r['shape'] for r in outcomes if r['comparison']==label}):
            pair={r['arithmetic']:r for r in outcomes if r['comparison']==label and r['shape']==shape}
            for profile in pair['float']['mandatory_profiles']:
                f=pair['float']['per_profile'][profile];q=pair['quantized']['per_profile'][profile]
                if not f['evaluated'] and not q['evaluated']:continue
                lines.append(f"| {shape} | {profile} | {f['passed']}/{f['evaluated']} | {q['passed']}/{q['evaluated']} | {'yes' if f['reference_payload_contract_valid'] else 'NO: startup reference mismatch'} |")
    lines+=['','The startup mismatch audit is in `runs/connectivity01/startup_payload_audit.json`. A short gap after cutting into an unknown UART phase did not guarantee synchronization, so some oracle outputs disagreed with the declared valid payloads. Version-2 data inserts a 256-tick high synchronization interval before scored recovery and asserts every valid post-cut payload. No model reset or sync signal is supplied. All old results and data remain preserved.','',
        'Complete per-condition fresh results and joint seed failures are in `runs/connectivity01/qualification_summary.json` and `runs/connectivity01/all_confirmation_conditions.csv`. Missing profiles never count as passed. The scoped clocked cost confirmation remains valid; later full-profile qualifications are listed in QUALIFIED_SHAPES.md.','']
    (ROOT/'CONFIRMATIONS.md').write_text('\n'.join(lines))
