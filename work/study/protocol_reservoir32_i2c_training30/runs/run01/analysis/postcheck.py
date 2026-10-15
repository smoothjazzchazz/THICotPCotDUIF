"""Post-freeze diagnostics only; does not change models, cases or acceptance."""
import json
from pathlib import Path

import numpy as np

from work.model.stream_reservoir import NAMES, StreamEvent
from work.study.protocol_reservoir64.checkers import bus_events
from work.study.protocol_reservoir64.scoring import score_events
from work.study.protocol_reservoir32_i2c_training30.run import HERE, sha, verify
from work.study.protocol_reservoir32_i2c_training30.receiver import StreamReceiver, load_weights
from work.study.protocol_reservoir32_i2c_training30.training import write_json


def main():
    output = Path(__file__).resolve().parent.parent
    analysis = output / 'analysis'
    final = output / 'final'
    verify(output)
    for name, digest in json.loads((final / 'manifest.json').read_text()).items():
        assert sha(final / name) == digest, name
    records = [json.loads(p.read_text()) for p in sorted(final.glob('n*_*.json'))]
    assert len(records) == 20
    assert sum(len(r['conditions']) for r in records) == 236
    assert len(list((output / 'models/i2c').glob('*/epoch_*.npz'))) == 120
    replays = json.loads((analysis / 'phrase_replays.json').read_text())
    assert len(replays) == 16 and all(r['exact'] for r in replays)

    traces = []
    for path in sorted((final / 'traces').glob('*/*/waveform.npz')):
        with np.load(path) as data:
            expected = bus_events(data['lines'])
            events = [StreamEvent(*map(int, row)) for row in data['events']]
        score, _ = score_events(expected, events)
        stored = json.loads((path.parent / 'path.json').read_text())['result']
        assert score['totals'] == stored['symbols']['totals']
        first_edge = expected[0][0]
        startup = [event for event in events if event.decision_tick < first_edge]
        after_startup, _ = score_events(
            expected, [event for event in events if event.decision_tick >= first_edge])
        traces.append(dict(trace=str(path.parent.relative_to(final)),
            first_reference_edge=first_edge, errors=score['totals']['errors'],
            startup_events=[dict(kind=NAMES[e.kind], tick=e.decision_tick) for e in startup],
            errors_after_excluding_startup=after_startup['totals']['errors']))
    assert len(traces) == 64
    write_json(analysis / 'startup_diagnostics.json', dict(traces=traces,
        note='Removing startup events is an offline diagnostic only. All original strict failures remain.'))

    idle_probes = []
    for record in records:
        if record['nodes'] != 32 or record['control'] != 'trained':
            continue
        weights, _ = load_weights(output / 'models/i2c' / record['variant'] / 'selected.npz')
        receiver = StreamReceiver(weights, record['mode'])
        emitted = []
        for tick in range(64):
            event = receiver.step((1, 1), tick)
            if event is not None:
                emitted.append(dict(kind=NAMES[event.kind], tick=event.decision_tick))
        idle_probes.append(dict(variant=record['variant'], mode=record['mode'], events=emitted))
    write_json(analysis / 'cold_idle_probes.json', dict(ticks=64, fixed_lines=[1, 1],
        probes=idle_probes, note='Diagnostic after freeze; no weights or acceptance criteria changed.'))

    cases = json.loads((final / 'cases.json').read_text())
    coverage = [dict(condition=c['name'], low=c.get('low', 10), high=c.get('high', 10),
        jitter_applied=c['name'] == 'jitter',
        unused_ratio=c.get('ratio'), unused_jitter_field=c.get('jitter')) for c in cases]
    write_json(analysis / 'effective_timing_cases.json', dict(cases=coverage,
        note='The unchanged inherited I2C scorer enables jitter only for the case named jitter. '
             'It ignores ratio and the generic jitter field. The combined-case names therefore '
             'denote fixed asymmetric 8/12 and 12/8 timing, not combined jitter or ratio sweeps.'))

    trained = [r for r in records if r['control'] == 'trained']
    valid = [c for r in trained for c in r['conditions'] if c['valid']]
    latencies = [c['response_latency'] for c in valid if c['response_latency']['n']]
    results = dict(condition_rows=236, phrase_replays=16, checked_traces=64,
        previous_files_unchanged=True,
        valid_deadline_misses=sum(c['deadline_misses'] for c in valid),
        valid_overflows=sum(c['buffer_overflows'] for c in valid),
        valid_latency_min=min(c['minimum'] for c in latencies),
        valid_latency_max=max(c['maximum'] for c in latencies))
    write_json(analysis / 'verification.json', results)

    marker = '\n## Post-freeze diagnostic detail\n'
    report = (HERE / 'REPORT.md').read_text().split(marker)[0]
    lines = [marker, '',
        'The strict failure counts above are unchanged. Saved traces were rescored against the '
        'independent bus-edge checker to locate startup errors; excluding an event below is '
        'a diagnostic, not a revised acceptance rule.', '',
        '| Candidate / arithmetic | Phrase startup events | Remaining phrase event errors |',
        '| --- | --- | ---: |']
    for row in traces:
        if not row['trace'].endswith('_phrase'):
            continue
        group, name = Path(row['trace']).parts[-2:]
        mode = name.split('_')[1]
        startup = ', '.join(f"{e['kind']} at tick {e['tick']}" for e in row['startup_events']) or 'none'
        lines.append(f"| {group} / {mode} | {startup} | {row['errors_after_excluding_startup']} |")
    lines += ['',
        'A separate 64-tick cold-idle probe holds both lines high from reset. '
        '[Its emitted events](runs/run01/analysis/cold_idle_probes.json) isolate startup '
        'behavior without a payload or any physical line transition.', '',
        '**Timing coverage limitation inherited from the comparison harness:** only the '
        '`jitter` case actually enables random jitter. The cases named `fast_with_jitter` and '
        '`slow_with_jitter` execute fixed low/high pairs 8/12 and 12/8; their generic jitter '
        'and ratio fields are ignored by the existing I2C scorer. The same behavior applies '
        'to both node counts. These results cover fixed timing corners and a separate '
        'nominal jitter test, not combined corner-plus-jitter or independent ratio sweeps.', '',
        f"Across both sizes and all trained candidates, valid-case response latencies range "
        f"from {results['valid_latency_min']} to {results['valid_latency_max']} ticks, with "
        f"{results['valid_deadline_misses']} deadline misses and {results['valid_overflows']} overflows.", '',
        'Malformed/recovery and idle/disturbance recovery means exact final output. It does '
        'not by itself establish zero false events or comprehensive unknown rejection.', '',
        '[Startup diagnostics](runs/run01/analysis/startup_diagnostics.json), '
        '[effective timing cases](runs/run01/analysis/effective_timing_cases.json), and '
        '[verification](runs/run01/analysis/verification.json) retain the details. '
        'After the normal report command, reproduce this section with '
        '`OPENBLAS_NUM_THREADS=1 /home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python -B -m '
        'work.study.protocol_reservoir32_i2c_training30.runs.run01.analysis.postcheck`.', '',
        '**Reporting command correction:** the frozen report script requires an absolute '
        '`--output /home/daniel/stuff/THICotPCotDUIF_exp/work/study/'
        'protocol_reservoir32_i2c_training30/runs/run01` path when building its analysis '
        'manifest. Use this instead of the relative output in the preregistered README '
        'for the report action. The initial path error is retained in '
        '`runs/run01/report.relative_path_failure.log`; rerunning with the absolute '
        'path succeeds. No training, evaluation or frozen source was changed.', '']
    (HERE / 'REPORT.md').write_text(report + '\n'.join(lines))
    write_json(analysis / 'manifest.json', {
        str(p.relative_to(HERE)): sha(p)
        for p in sorted([*analysis.glob('*'), HERE / 'REPORT.md'])
        if p.is_file() and p.name != 'manifest.json'})
    print(json.dumps(results), flush=True)


if __name__ == '__main__':
    main()
