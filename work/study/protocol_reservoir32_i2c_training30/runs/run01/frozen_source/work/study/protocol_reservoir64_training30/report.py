"""Read-only analysis and figures after frozen confirmation; never adjusts fitting."""
import csv
import json
from pathlib import Path
import numpy as np
from work.model.stream_reservoir import NAMES, StreamReceiver, initial_weights, load_weights
from work.study.protocol_reservoir64.data import load_split
from .data import PROFILES
from .training import SEEDS, write_json
from .audit import credit_trace


def adequacy(history):
    a = [r for r in history if r['epoch'] in (18,21,24)]
    b = [r for r in history if r['epoch'] in (24,27,30)]
    changes = {k:float(np.mean([r['live'][k] for r in b])-np.mean([r['live'][k] for r in a]))
               for k in ('strict_exchanges','byte_exact_exchanges','aligned_byte_fraction','boundary_f1','macro_f1')}
    before = np.mean([r['dev_loss'] for r in a]); after = np.mean([r['dev_loss'] for r in b])
    changes['relative_dev_loss_reduction'] = float((before-after)/max(before,1e-15))
    improving = (changes['strict_exchanges']>=1 or changes['byte_exact_exchanges']>=1 or
                 any(changes[k]>=.01 for k in ('aligned_byte_fraction','boundary_f1','macro_f1')) or
                 changes['relative_dev_loss_reduction']>=.02)
    return dict(status='training-limited / not converged' if improving else 'plateau under this recipe; capacity not established',
                early_epochs=[18,21,24],late_epochs=[24,27,30],changes=changes)


def diagnostics(output):
    rows = []
    for profile in PROFILES:
        stream = load_split(output,profile,'dev')[0]
        for seed in SEEDS:
            directory = output/'models'/profile/f'seed_{seed}'
            for epoch in (12,30):
                w,_ = load_weights(directory/f'epoch_{epoch:02d}.npz')
                rx, states, logits, correct = StreamReceiver(w),[],[],[]
                for tick,line in enumerate(stream['lines']):
                    rx.step(line,tick); states.append(rx.state.copy()); logits.append(rx.logits.copy())
                states, logits = np.array(states),np.array(logits)
                by_kind = {}
                for kind in (1,2,3,4,5,6):
                    ticks = np.flatnonzero(stream['labels']==kind)
                    if not len(ticks): continue
                    ranked = np.argmax(logits[ticks],axis=1)
                    around = [bool(np.any(np.argmax(logits[max(0,t-2):t+3],axis=1)==kind)) for t in ticks]
                    by_kind[NAMES[kind]] = dict(expected=len(ticks),
                        top_class_at_teacher_tick=float(np.mean(ranked==kind)),
                        top_class_within_two_ticks=float(np.mean(around)),
                        mean_true_logit_margin=float(np.mean(logits[ticks,kind]-np.max(np.delete(logits[ticks],kind,axis=1),axis=1))))
                singular = np.linalg.svd(states-states.mean(axis=0),compute_uv=False)
                rows.append(dict(profile=profile,seed=seed,epoch=epoch,
                    near_saturated_state_fraction=float(np.mean(abs(states)>.98)),
                    state_std_mean=float(np.mean(states.std(axis=0))),
                    variance_dimensions_99=int(np.searchsorted(np.cumsum(singular**2)/np.sum(singular**2),.99)+1),
                    max_abs_weight=max(float(abs(v).max()) for v in w.values()),
                    stop_credit_trace=credit_trace(w,stream['lines']),event_logit_diagnostics=by_kind,
                    interpretation='Sensitivity and separability diagnostics, not a proof of state collisions or insufficient capacity.'))
    return rows


def replay_traces(output):
    records = []
    for trace in sorted((output/'final/traces').glob('*/*_phrase')):
        parts = trace.name.split('_')
        mode_index = parts.index('float') if 'float' in parts else parts.index('quantized')
        profile = '_'.join(parts[:mode_index]); mode=parts[mode_index]; seed=int(parts[mode_index+1])
        variant = trace.parent.name
        w,_ = load_weights(output/'models'/profile/variant/'selected.npz')
        with np.load(trace/'waveform.npz') as data:
            rx,actual = StreamReceiver(w,mode),[]
            for t,pair in enumerate(data['lines']):
                e=rx.step(pair,t)
                if e is not None: actual.append((e.kind,e.observation_tick,e.decision_tick))
            np.testing.assert_array_equal(np.array(actual,dtype=np.int64).reshape(-1,3),data['events'])
        records.append(dict(trace=str(trace.relative_to(output)),exact=True,events=len(actual)))
    return records


def report(output):
    from .run import ORIGINAL, HERE, verify
    verify(output)
    final=output/'final'; analysis=output/'analysis'; analysis.mkdir(exist_ok=True)
    manifest=json.loads((final/'manifest.json').read_text())
    from .run import sha
    for p,d in manifest.items(): assert sha(final/p)==d
    summary=json.loads((final/'summary.json').read_text())
    exposure=json.loads((output/'exposure.json').read_text())
    fits={}
    for p in PROFILES:
        for variant in [*(f'seed_{s}' for s in SEEDS),'original_loss_11']:
            fits[p,variant]=json.loads((output/'models'/p/variant/'fit.json').read_text())
    convergence=[dict(profile=p,variant=v,**adequacy(f['history'])) for (p,v),f in fits.items()]
    write_json(analysis/'convergence.json',convergence)
    write_json(analysis/'diagnostics.json',diagnostics(output))
    write_json(analysis/'phrase_replays.json',replay_traces(output))
    fields=['profile','variant','mode','condition','valid','passes','byte_exact','expected_bytes','output_bytes',
            'event_errors','false_known','false_invalid','START_precision','START_recall','STOP_precision','STOP_recall',
            'deadline_misses','buffer_overflows','recovery_success']
    with (analysis/'per_condition.csv').open('w',newline='') as h:
        writer=csv.DictWriter(h,fieldnames=fields);writer.writeheader()
        for model in summary['models']:
            p,v,m=model['profile'],model['variant'],model['mode']
            record=json.loads((final/f'{p}_{v}_{m}.json').read_text())
            for r in record['conditions']:
                event=r['symbols'];row=dict(profile=p,variant=v,mode=m,condition=r['condition'],valid=r['valid'],
                    passes=r['passes'],byte_exact=r['bytes']['exact'],expected_bytes=r['bytes']['expected'],
                    output_bytes=r['bytes']['recovered'],event_errors=event['totals']['errors'],
                    false_known=event['totals']['false_known'],false_invalid=event['totals']['false_invalid'],
                    deadline_misses=r['deadline_misses'],buffer_overflows=r['buffer_overflows'],recovery_success=r['recovery_success'])
                for k in ('START','STOP'):
                    for metric in ('precision','recall'): row[k+'_'+metric]=event['by_kind'][k][metric]
                writer.writerow(row)
    plot(output,fits,summary)
    lines=['# Stronger training with the same 64 nodes','',
        'All twelve candidates completed 30 epochs, including three original-loss controls. '
        'The receiver architecture and original experiment are unchanged. This is a simulation of the original assumed profiles.', '',
        '## Exposure', '',
        '| Profile | Original ticks / updates | New transaction / nonpadding ticks | New updates | Transaction exposure / update ratio |',
        '| --- | ---: | ---: | ---: | ---: |']
    for p,e in exposure.items():
        lines.append(f"| {p} | {e['original_unique_nonpadding_ticks']:,} / {e['original_updates']:,} | "
            f"{e['unique_transaction_ticks']:,} / {e['unique_nonpadding_ticks']:,} | {e['optimizer_updates']:,} | "
            f"{e['transaction_to_original_nonpadding_ratio']:.2f}x / {e['update_ratio']:.2f}x |")
    lines += ['', 'Every candidate uses batch 12 and a 512-tick gradient window; state carries across chunks. '
        'The ratio compares new transaction ticks against **all** old nonpadding ticks, so idle cannot satisfy it. '
        'These are generated sample positions, not a claim every waveform substring differs. '
        'Repeated presentations equal the corresponding unique ticks multiplied by 30; padding is reported separately in exposure.json.', '',
        '## Fresh final results', '',
        '| Profile / seed or control | Selected epoch | Float exact / strict cases | Quantized exact / strict cases | Phrase float / quantized |',
        '| --- | ---: | ---: | ---: | --- |']
    for (p,v),fit in fits.items():
        columns=[];phrases=[]
        for mode in ('float','quantized'):
            r=json.loads((final/f'{p}_{v}_{mode}.json').read_text());s=r['summary']
            columns.append(f"{s['byte_exact_exchanges']}/{s['valid_exchanges']} / {s['strict_exchanges']}/{s['valid_exchanges']}")
            phrases.append(str(next(c for c in r['conditions'] if c['condition']=='phrase')['bytes']['exact']))
        lines.append(f"| {p} / {v} | {fit['best_epoch']} | {columns[0]} | {columns[1]} | {' / '.join(phrases)} |")
    lines += ['', 'Qualification: '+json.dumps(summary['qualification'])+'. Exact payload delivery alone does not satisfy the zero-event-error gate.', '',
        'The original UART candidates returned zero bytes and had zero correctly timed STOP events. Original I2C seeds 11/47 had 10/12 '
        'byte-exact cases, seed 29 had 2/12, and all failed the strict gate. Original final data were already observed; '
        'new binary payloads, transaction phases and peer-jitter seeds are fresh, so this is a condition-matched comparison rather than identical trials.', '',
        '## Training adequacy', '']
    for row in convergence:
        changes=row['changes']
        lines.append(f"- {row['profile']} / {row['variant']}: **{row['status']}**; late dev-loss change "
                     f"{changes['relative_dev_loss_reduction']*100:+.1f}% improvement, boundary F1 {changes['boundary_f1']:+.3f}, "
                     f"aligned-byte fraction {changes['aligned_byte_fraction']:+.3f}.")
    lines += ['', 'These labels follow the preregistered late-window rule. Thirty epochs do not establish capacity limits. '
        'Selection uses protocol behavior; an earlier selected epoch can coexist with an improving loss at epoch 30. '
        'Epoch 12 and epoch 30, all intermediate weights, and complete Adam checkpoints are retained.', '',
        '## Interpretation and limits', '',
        'The intervention combines more transactions, longer credit assignment, more updates, and improved live-bus training coverage. '
        'The original-loss controls isolate loss weighting within this expanded budget; this design does not separately identify the effects '
        'of extra data versus longer windows versus matched bus timing. No failing result proves that 64 nodes cannot support the task.', '',
        'Read per-class precision/recall and false events alongside byte delivery: aggregate I2C loss can hide START/STOP faults; '
        'UART cell-center predictions can remain too weak or mistimed to deliver a complete frame. Diagnostics compare teacher-tick '
        'versus nearby event logits, state saturation, and long-range STOP sensitivity at epochs 12/30. These diagnose a recipe, '
        'not a universal representational impossibility. Float/quantized final rows isolate arithmetic degradation.', '',
        'A layered 64-node comparison becomes justified after retaining these baselines and either (a) continued training reaches a stable '
        'protocol-performance plateau across seeds/objectives or (b) targeted state/gradient probes expose a reproducible timing or '
        'representation weakness that layering addresses. Use the same event/timing/rejection budgets, separate new selection data, '
        'and account for every added temporal state. If this run is still improving, resume it before claiming architecture failure.', '',
        'The loaded receiver has the original 1,224 learned coefficients, 64 recurrent nodes and 256 taps. No temporal memory was added '
        'at inference. Cost, finite queues, deadline failures, rejection/recovery, and disabled/no-recurrence controls remain explicit. '
        'USB receives zero fitting steps unless UART/I2C qualify and protocol sources are supplied; no hardware gate is passed.', '',
        '## Evidence', '',
        '- [Recipe and commands](README.md); [exposure](runs/run01/exposure.json); [preflight audit](runs/run01/audit/preflight.json).',
        '- [Learning curves](runs/run01/analysis/learning_curves.png); [per-condition CSV](runs/run01/analysis/per_condition.csv); '
        '[convergence](runs/run01/analysis/convergence.json); [diagnostics](runs/run01/analysis/diagnostics.json).',
        '- [Frozen hashes](runs/run01/freeze.json); [all weights and optimizer states](runs/run01/models/); '
        '[waveform traces](runs/run01/final/traces/); [phrase replay checks](runs/run01/analysis/phrase_replays.json).',
        '- [Resource accounting](runs/run01/final/cost.json); [final manifest](runs/run01/final/manifest.json); '
        '[USB status](runs/run01/final/usb_status.json).', '']
    (HERE/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(dict(report=str(HERE/'REPORT.md'),qualification=summary['qualification'],convergence=convergence)),flush=True)


def plot(output,fits,summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,4,figsize=(16,10),layout='constrained')
    for i,p in enumerate(PROFILES):
        for v in [*(f'seed_{s}' for s in SEEDS),'original_loss_11']:
            h=fits[p,v]['history'];live=[r for r in h if 'live' in r]
            style='--' if v=='original_loss_11' else '-'
            axes[i,0].plot([r['epoch'] for r in h],[r['dev_loss'] for r in h],style,label=v)
            axes[i,1].plot([r['epoch'] for r in live],[r['live']['boundary_f1'] for r in live],style)
            axes[i,2].plot([r['epoch'] for r in live],[r['live']['aligned_byte_fraction'] for r in live],style)
            axes[i,3].plot([r['epoch'] for r in live],[r['live']['strict_exchanges'] for r in live],style)
        axes[i,0].set_ylabel(p);axes[i,0].set_yscale('log')
        for ax in axes[i]: ax.axvline(12,color='gray',lw=.8,alpha=.6);ax.set_xlabel('Epoch');ax.grid(alpha=.2)
    for ax,title in zip(axes[0],('Weighted dev loss (recipes differ)','Minimum START/STOP F1','Aligned delivered byte fraction','Strict passing dev exchanges')): ax.set_title(title)
    axes[0,0].legend(fontsize=8)
    fig.savefig(output/'analysis/learning_curves.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(13,7),layout='constrained')
    for ax,p in zip(axes,PROFILES):
        path=output/'final/traces/seed_11'/f'{p}_quantized_11_phrase/waveform.npz'
        with np.load(path) as trace:
            n=min(1500,len(trace['lines']));t=np.arange(n)
            ax.step(t,trace['lines'][:n,0],where='post',label='observed line 0')
            if p=='i2c': ax.step(t,trace['lines'][:n,1]+1.5,where='post',label='observed SDA + 1.5')
            else: ax.step(t,trace['output'][:n]+1.5,where='post',label='TX + 1.5')
            events=trace['events'];events=events[events[:,1]<n]
            ax.scatter(events[:,1],events[:,0]/8+3,s=8,label='event kind / 8 + 3')
        ax.set_title(p+' seed 11, quantized phrase prefix');ax.set_xlabel('Tick');ax.legend(loc='upper right',fontsize=7)
    fig.savefig(output/'analysis/phrase_waveforms.png',dpi=160);plt.close(fig)
