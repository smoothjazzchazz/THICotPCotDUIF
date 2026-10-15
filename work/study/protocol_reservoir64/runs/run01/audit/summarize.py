"""Audited presentation of frozen metrics. Does not replace original results."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / 'final'
rows, summaries = [], []
for path in sorted(FINAL.glob('*_seed_*.json')) + sorted(FINAL.glob('*_readout_only_*.json')):
    record = json.loads(path.read_text())
    valid = [c for c in record['conditions'] if c['valid']]
    summary = {k: record[k] for k in ('profile', 'variant', 'mode', 'seed', 'qualified')}
    summary.update(valid_cases=len(valid), byte_exact_cases=sum(c['bytes']['exact'] for c in valid),
        strict_pass_cases=sum(c['passes'] for c in valid),
        expected_bytes=sum(c['bytes']['expected'] for c in valid),
        output_bytes=sum(c['bytes']['recovered'] for c in valid),
        expected_symbols=sum(c['symbols']['totals']['expected'] for c in valid),
        correct_symbols=sum(c['symbols']['totals']['correct'] for c in valid),
        symbol_errors=sum(c['symbols']['totals']['errors'] for c in valid),
        false_known=sum(c['symbols']['totals']['false_known'] for c in valid),
        false_invalid=sum(c['symbols']['totals']['false_invalid'] for c in valid))
    summaries.append(summary)
    for c in record['conditions']:
        row = {k: record[k] for k in ('profile', 'variant', 'mode', 'seed')}
        row.update(condition=c['condition'], valid=c['valid'], byte_exact=c['bytes']['exact'],
            strict_pass=c['passes'], expected_bytes=c['bytes']['expected'],
            output_bytes=c['bytes']['recovered'], byte_substitutions=c['bytes']['substitutions'],
            byte_deletions=c['bytes']['deletions'], byte_insertions=c['bytes']['insertions'],
            controller_recovered_bytes=c['controller_bytes']['recovered'],
            controller_exact=c['controller_bytes']['exact'],
            presented_data_bytes=(max(0, len(c['peer_acks']) - 2) if record['profile'] == 'i2c'
                                  else c['input_presented_bytes']),
            symbols_expected=c['symbols']['totals']['expected'],
            symbols_correct=c['symbols']['totals']['correct'],
            symbols_missing=c['symbols']['totals']['missing'],
            symbols_wrong_class=c['symbols']['totals']['wrong_class'],
            false_known=c['symbols']['totals']['false_known'],
            false_invalid=c['symbols']['totals']['false_invalid'],
            duplicates=c['symbols']['totals']['duplicates'],
            recovery_success=c['recovery_success'],
            response_latency_n=c['response_latency']['n'],
            response_latency_min=c['response_latency']['minimum'],
            response_latency_mean=c['response_latency']['mean'],
            response_latency_max=c['response_latency']['maximum'],
            failed_or_unverifiable_deadlines=c['deadline_misses'],
            controller_errors=c['controller_errors'], buffer_overflows=c['buffer_overflows'])
        rows.append(row)
with (FINAL/'per_condition.csv').open('w', newline='') as handle:
    writer=csv.DictWriter(handle,fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
(FINAL/'summary_tables.json').write_text(json.dumps(summaries,indent=2)+'\n')
notes = dict(
    original_metrics_preserved=True,
    corrections=[
        'In original I2C JSON, input_presented_bytes actually counts controller-recovered write bytes. The audited CSV labels that separately and uses len(peer_acks)-2 to count data-byte attempts made by the live master, excluding its two address cycles.',
        'UART deadline_misses for a non-exact output is conservatively the expected byte count: these deadlines are failed or unverifiable, not evidence that every byte was delivered late. Latency samples are withheld unless output is wholly exact.',
        'I2C fast_with_jitter/slow_with_jitter names are shared with UART; they mean fixed asymmetric low/high timings (8/12 or 12/8). The separate jitter case randomizes each low and high period over 8..12.',
        'The cost file lists logical UART FIFO capacity and its actual encoded command/deadline representation. Do not sum an extra 32-byte data array into implemented Python state: no separate byte queue is allocated.',
        'Each case is a complete write/read exchange or multi-frame UART stream, reset once at case start. Byte-exact cases and strict qualified cases are distinct.'
    ], audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(FINAL/'measurement_notes.json').write_text(json.dumps(notes,indent=2)+'\n')
print('Saved',len(rows),'condition rows and',len(summaries),'model summaries')
