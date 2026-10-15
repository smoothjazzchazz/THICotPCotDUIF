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



def plot(output,fits,summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,4,figsize=(16,10),layout='constrained')
    for i,p in enumerate(PROFILES):
        for v in [*(f'seed_{s}' for s in SEEDS),'previous_recipe_11']:
            h=fits[p,v]['history'];live=[r for r in h if 'live' in r]
            style='--' if v=='previous_recipe_11' else '-'
            axes[i,0].plot([r['epoch'] for r in h],[r['dev_loss'] for r in h],style,label=v)
            axes[i,1].plot([r['epoch'] for r in live],[r['live']['boundary_f1'] for r in live],style)
            axes[i,2].plot([r['epoch'] for r in live],[r['live']['aligned_byte_fraction'] for r in live],style)
            axes[i,3].plot([r['epoch'] for r in live],[r['live']['strict_exchanges'] for r in live],style)
        axes[i,0].set_ylabel(p);axes[i,0].set_yscale('log')
        for ax in axes[i]: ax.axvline(12,color='gray',lw=.8,alpha=.6);ax.set_xlabel('Epoch');ax.grid(alpha=.2)
    for ax,title in zip(axes[0],('Weighted dev loss (recipes differ)','Minimum START/STOP F1','Aligned delivered byte fraction','Strict passing dev exchanges')): ax.set_title(title)
    axes[0,0].legend(fontsize=8)
    fig.savefig(output/'analysis/learning_curves.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(13,7),layout='constrained')
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


def report(output):
    from .run import verify, HERE, sha
    from .validation import checkpoints
    verify(output)
    output=Path(output);final=output/'final';analysis=output/'analysis';analysis.mkdir(exist_ok=True)
    for p,d in json.loads((final/'manifest.json').read_text()).items():assert sha(final/p)==d
    summary=json.loads((final/'summary.json').read_text()); recipe=json.loads((output/'recipe.json').read_text())
    fits={(p,v):json.loads((output/'models'/p/v/'fit.json').read_text()) for p in PROFILES for v in [*(f'seed_{s}' for s in SEEDS),'previous_recipe_11']}
    convergence=[dict(profile=p,variant=v,**adequacy(f['history'])) for (p,v),f in fits.items()]
    write_json(analysis/'convergence.json',convergence)
    write_json(analysis/'diagnostics.json',diagnostics(output))
    write_json(analysis/'phrase_replays.json',replay_traces(output))
    checkpoints(output)
    plot(output,fits,summary)
    records=[json.loads((final/f"{m['profile']}_{m['variant']}_{m['mode']}.json").read_text()) for m in summary['models']]
    fields=['profile','variant','mode','condition','valid','passes','exact','expected','recovered','event_errors','false_known','false_invalid','deadline_misses','buffer_overflows','recovery','cold_start_events','START_precision','START_recall','STOP_precision','STOP_recall','START_timing_mean','STOP_timing_mean']
    with (analysis/'per_condition.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for model in records:
            for r in model['conditions']:
                row={k:model[k] for k in ('profile','variant','mode')}
                row.update(condition=r['condition'],valid=r['valid'],passes=r['passes'],exact=r['bytes']['exact'],expected=r['bytes']['expected'],recovered=r['bytes']['recovered'],event_errors=r['symbols']['totals']['errors'],false_known=r['symbols']['totals']['false_known'],false_invalid=r['symbols']['totals']['false_invalid'],deadline_misses=r['deadline_misses'],buffer_overflows=r['buffer_overflows'],recovery=r['recovery_success'],cold_start_events=len(r['cold_start_events']))
                for k in ('START','STOP'):
                    for metric in ('precision','recall'):row[k+'_'+metric]=r['symbols']['by_kind'][k][metric]
                    row[k+'_timing_mean']=r['boundary_timing'][k]['mean']
                writer.writerow(row)
    exposure=json.loads((output/'exposure.json').read_text());cold=json.loads((final/'cold_idle.json').read_text())
    counts=dict(candidates=len(fits),epochs=sum(f['epochs'] for f in fits.values()),optimizer_updates=sum(f['steps'] for f in fits.values()),nonpadding_presentations=sum(f['repeated_nonpadding_presentations'] for f in fits.values()))
    write_json(analysis/'budget_totals.json',counts)
    lines=['# Six-seed UART with the shared 64-node receiver','',
           f"All {counts['candidates']} candidates completed 30 epochs: {counts['epochs']} saved weight/optimizer checkpoints, {counts['optimizer_updates']:,} main/control optimizer updates and {counts['nonpadding_presentations']:,} nonpadding tick presentations.", '',
           'The original StreamReceiver implementation is imported unchanged for both UART and frozen I2C weights. It has 64 nodes, the same 256-edge mask for every seed/protocol, six generic features, unchanged leaks, arithmetic, margin, event interface and update timing. No protocol timing state was added.', '',
           '## Pre-main investigation and controlled intervention','',
           f"The training/development pilot selected `{recipe['selected']}`: original input weights ×.2, nonself recurrent weights ×.1, existing self weights initialized to .95 and NONE bias .5. All these are trainable parameters. The two-pass, twelve-stream 8,192-tick pilot compared previous, .95 and 1.05 initialization; its {recipe['pilot_updates']} updates and {recipe['pilot_presentations']:,} presentations are separate from the main budget. It offered a development-based choice, not evidence of full-frame success.", '',
           'Labels were reconstructed against actual cell boundaries, payloads and parity. Repeated identical bits retain separate pulses with intervening NONE ticks. The 512-tick analytical gradients pass finite differences; training/batched forward decisions agree with the online receiver and state carries across chunks/transactions. Actual first-STOP sensitivity probes of prior epoch-30 weights and alternative initializations are retained. A longer gradient window alone does not guarantee useful complete-frame credit.', '',
           'The exact previous30 corpora and weighted loss are reused; only initialization changes for the main candidates. Matched seed11 previous-recipe controls receive the same corpus, optimizer, 30 epochs and update count. The old original-loss control is a different experiment. No previous final data select these weights.', '',
           '## Budget per candidate','',
           '| Profile | Transaction ticks | Nonpadding ticks | Padding ticks/pass | Updates | Repeated nonpadding ticks |','| --- | ---: | ---: | ---: | ---: | ---: |']
    for p,e in exposure.items():lines.append(f"| {p} | {e['unique_transaction_ticks']:,} | {e['unique_nonpadding_ticks']:,} | {e['padding_ticks']:,} | {e['optimizer_updates']:,} | {e['repeated_nonpadding_presentations']:,} |")
    lines+=['','Twelve streams, 512-tick TBPTT and 30 full passes apply to every candidate. Transaction exposure and updates exactly equal the preceding 30-epoch budget. Padding is loss-masked. Independent streams start cold each epoch; inference is continuous across transactions and gradient chunks. Every epoch retains weights, Adam moments, step count, ending state and deterministic continuation position.','',
            '## Fresh final results','',
            '| Profile / candidate | Epoch | Float exact / strict | Quantized exact / strict | Float / quantized delivered bytes |','| --- | ---: | ---: | ---: | ---: |']
    for (p,v),fit in fits.items():
        rr=[next(r for r in records if r['profile']==p and r['variant']==v and r['mode']==m) for m in ('float','quantized')]
        vals=[f"{r['summary']['byte_exact_exchanges']}/{r['summary']['valid_exchanges']} / {r['summary']['strict_exchanges']}/{r['summary']['valid_exchanges']}" for r in rr]
        n=[sum(c['bytes']['recovered'] for c in r['conditions'] if c['valid']) for r in rr]
        lines.append(f"| {p} / {v} | {fit['best_epoch']} | {vals[0]} | {vals[1]} | {n[0]} / {n[1]} |")
    lines+=['',f"Strict all-main-seed qualification, including cold-idle false events: **{summary['qualification']}**.",'',
            'These are complete input-waveform → learned receiver → controller → transmitter → independent output-decoder results. Final-only phrase, every byte, 2,048 random bytes, 1,024-byte message, long constant runs, patterns, gaps, back-to-back frames, .97/1.03 timing and jitter corners are included. Malformed stops/parity, disturbances and recovery have separate rows. Fresh final transaction seeds start at 50,000,000; live development uses 40,000,000. Fixed challenge payloads intentionally recur across experiments.', '',
            '## Failures, arithmetic and training adequacy','']
    for r in records:
        if r['mode']!='float':continue
        p,v=r['profile'],r['variant'];q=next(a for a in records if a['profile']==p and a['variant']==v and a['mode']=='quantized')
        sr=r['summary'];sq=q['summary'];ci=[a for a in cold if a['profile']==p and a['variant']==v]
        lines.append(f"- {p}/{v}: float START recall {sr['events']['START']['recall']:.1%}, STOP recall {sr['events']['STOP']['recall']:.1%}; {sr['false_events']:,}/{sq['false_events']:,} float/quantized false events; cold-idle events {sum(a['false_events'] for a in ci)} across both modes; recovery {sum(bool(c['recovery_success']) for c in r['conditions'] if not c['valid'])}/{sum(not c['valid'] for c in r['conditions'])} float cases.")
    lines+=['','The preceding 64-node/30-epoch UART run delivered zero bytes in both profiles and both arithmetic modes. Compare byte delivery above, not loss alone. Full per-class precision/recall, boundary timing, malformed false bytes, deadlines, buffer overflows and per-condition results are retained. Cold-start events remain errors, including tick zero; no warm-up interval is removed.','']
    for c in convergence:lines.append(f"- {c['profile']}/{c['variant']}: **{c['status']}**; late loss improvement {c['changes']['relative_dev_loss_reduction']:.1%}, boundary-F1 change {c['changes']['boundary_f1']:+.3f}, aligned-byte fraction change {c['changes']['aligned_byte_fraction']:+.3f}.")
    lines+=['','Thirty epochs and a failed initialization recipe do not prove insufficient reservoir capacity. If still improving, the next controlled experiment should resume retained checkpoints with a declared additional budget before architectural conclusions. Otherwise test a training-only curriculum for reliable repeated-bit/STOP timing, keeping this architecture and matching exposure; any later generic architectural revision must also be demonstrated trainable on I2C.','',
            '## Fresh I2C compatibility','',
            '| Frozen 64-node candidate | Mode | Exact / strict valid cases |','| --- | --- | ---: |']
    i2c=json.loads((final/'i2c_compatibility/summary.json').read_text())
    for v in ('seed_11','seed_29','seed_47','original_loss_11'):
        for m in ('float','quantized'):
            rr=[r for r in i2c['rows'] if r['variant']==v and r['mode']==m and r['valid']]
            lines.append(f"| {v} | {m} | {sum(r['bytes']['exact'] for r in rr)}/{len(rr)} / {sum(r['passes'] for r in rr)}/{len(rr)} |")
    lines+=['',f"Shared architecture hash: `{i2c['architecture_hash']}`. I2C weights were never retrained. All runs use the same receiver code. Known startup failures are counted. The new harness actually applies jitter to combined low/high corners; prior I2C reports disclosed that those combined cases ignored jitter. Actual high/low durations are retained; low durations may include target stretching.",'',
            '## Resources and verification','',
            '1,224 learned coefficients (2,448 bytes packed int16), 64 recurrent states (256 bytes for two int16 buffers), 1,152 sparse weighted MACs/tick versus 4,992 in the dense NumPy implementation. The 8,194-byte packed tanh ROM, feature/event/controller state, finite buffers and shared scheduler remain additional costs. These are logical estimates and software measurements, not synthesis, physical frequency, area, power or electrical compliance.', '',
            'All 420 epoch weight/optimizer pairs are checked against the topology and metadata; selected weights and initializations are verified. Four actual epoch29→30 continuations reproduce weights, moments and ending state exactly. Saved phrase events replay exactly. Prior experiment preservation and frozen source/data/config/weight hashes are verified. Disabled/no-recurrence controls retain matched phrase/every-byte/pattern failures or successes without implying universal recurrence necessity.', '',
            '## Evidence and reproduction','',
            '- [Recipe and commands](README.md), [selected recipe](runs/run01/recipe.json), [pilot trials](runs/run01/investigation/pilots.json), [preflight](runs/run01/audit/preflight.json), [real-frame gradients](runs/run01/audit/complete_frame_credit.json).',
            '- [Learning curves](runs/run01/analysis/learning_curves.png), [per-condition CSV](runs/run01/analysis/per_condition.csv), [diagnostics](runs/run01/analysis/diagnostics.json), [convergence](runs/run01/analysis/convergence.json).',
            '- [All checkpoints](runs/run01/models/), [traces](runs/run01/final/traces/), [cold idle](runs/run01/final/cold_idle.json), [I2C cases](runs/run01/final/i2c_compatibility/summary.json), [effective timing](runs/run01/final/i2c_compatibility/effective_timing.json).',
            '- [Checkpoint verification](runs/run01/analysis/checkpoint_verification.json), [phrase replays](runs/run01/analysis/phrase_replays.json), [tests](runs/run01/tests.log), [preservation](runs/run01/original_preservation.json), [freeze](runs/run01/freeze.json), [cost](runs/run01/final/cost.json).','']
    (HERE/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(dict(report=str(HERE/'REPORT.md'),qualification=summary['qualification'],budget=counts)),flush=True)
