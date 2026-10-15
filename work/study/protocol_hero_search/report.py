"""Generate the measured report, exact manifests, diagrams, and learning curves."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import numpy as np
from .run import ROOT,digest
from .shapes import make_shape,PROFILES,SEEDS
from .training import write_json


def costs(candidate):
    sh=make_shape(candidate['variant'],candidate['nodes']);e=len(sh.src);n=sh.n
    return dict(shape=sh.name,nodes=n,groups=list(map(len,sh.groups)),
        input_connections=int(np.sum(sh.src<0)),same_tick_connections=int(np.sum((sh.src>=0)&(sh.delay==0))),
        registered_connections=int(np.sum((sh.src>=0)&(sh.delay==1))),weights_and_biases=sh.parameters,
        programmable_leaks=n,model_storage_float64_bytes=8*(sh.parameters+n),
        model_storage_q12_bytes=2*(sh.parameters+n),q12_tanh_table_bytes=4097*2,
        recurrent_state_float64_bytes=n*8,recurrent_state_q12_bytes=n*2,
        scratch_state_float64_bytes=n*8,scratch_state_q12_bytes=n*2,
        multiply_accumulates_per_tick=e+6*n,leak_multiplies_per_tick=2*n,tanh_per_tick=n,
        sequential_activation_depth=len(sh.groups) if candidate['variant'].endswith('current') else 1,
        preprocessing_state_bits=3+3*9,pulse_former_bits=3,divider_setting_bits=32,divider_counter_bits=32,
        lane_map_bits=6,integer_accumulator_bits=64,observation_tick_counter_bits=64,decision_tick_buffer=0,
        assembly='Python event-only assembler; up to 9225 bits per phase and 1026 stored I2C bytes plus ACK bits/segment metadata. No synthesized buffer/control-area estimate.',
        scheduling='all nodes each sampled tick; current propagation needs ordered layer evaluations, registered propagation reads prior tick',
        hardware_clock_hz=0,hardware_area='unmeasured',electrical_compliance='not evaluated')


def plots(root,chosen):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
    out=root/'figures';out.mkdir(exist_ok=True)
    for c in chosen:
        sh=make_shape(c['variant'],c['nodes']);fig,ax=plt.subplots(figsize=(9,3.4));ax.axis('off')
        ax.set_xlim(-.2,10);ax.set_ylim(-.2,3)
        blocks=[('9 shared\ninput features',.0,.95,1.5,1.)]
        positions=np.linspace(2.2,6.3,len(sh.groups))
        for i,(xx,g) in enumerate(zip(positions,sh.groups)):
            blocks.append((f'Layer {i+1}\n{len(g)} nodes\nleak {sh.leaks[g[0]]:g}',xx,.85,1.45,1.2))
        blocks.append(('6-logit readout\n+ pulse former',8,.95,1.65,1.))
        for label,x,y,w,h in blocks:
            ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.07',facecolor='#eaf0fa',edgecolor='#254b79'))
            ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10)
        ax.add_patch(FancyArrowPatch((1.6,1.45),(positions[0]-.08,1.45),arrowstyle='->',mutation_scale=14))
        for i in range(len(positions)-1):
            ax.add_patch(FancyArrowPatch((positions[i]+1.5,1.45),(positions[i+1]-.08,1.45),arrowstyle='->',mutation_scale=14))
            ax.text((positions[i]+positions[i+1]+1.4)/2,2.23,'1 tick' if 'registered' in c['variant'] else 'same tick',ha='center',fontsize=9)
        for i,xx in enumerate(positions):
            y=.48-i*.13
            ax.plot([xx+.7,xx+.7,8.8],[.8,y,y],color='#6a7c98',lw=1)
        ax.annotate('',xy=(8.8,.88),xytext=(8.8,.12),arrowprops=dict(arrowstyle='->',color='#6a7c98'))
        ax.set_title(f"{c['shape']} — readout observes every layer",fontsize=13)
        fig.tight_layout();fig.savefig(out/f"{c['shape']}_connections.png",dpi=170);plt.close(fig)
    fig,axes=plt.subplots(len(chosen),2,figsize=(11,3.5*len(chosen)),squeeze=False)
    for row,c in enumerate(chosen):
        for col,profile in enumerate(('uart_n','uart_e')):
            regime=c['profiles'][profile]['regime'];ax=axes[row,col]
            for seed in SEEDS:
                h=json.loads((root/'models'/c['shape']/profile/f'{regime}_{seed}'/'history.json').read_text())
                h=[r for r in h if 'dev_loss' in r]
                ax.plot([r['epoch'] for r in h],[r['dev_loss'] for r in h],label=str(seed),lw=1)
            ax.set_title(f"{c['shape']} / {profile}");ax.set_xlabel('Epoch');ax.set_ylabel('Development weighted loss');ax.grid(alpha=.2)
    axes[0,0].legend(title='Training seed',fontsize=8,ncol=3)
    fig.tight_layout();fig.savefig(out/'uart_learning_curves.png',dpi=170);plt.close(fig)


def build(root):
    selection=json.loads((root/'final_selection.json').read_text());chosen=selection['top_two']
    results=json.loads((root/'confirmation_ledger.json').read_text())
    screen=json.loads((root/'screen_ledger.json').read_text())
    finals=json.loads((root/'finalists_ledger.json').read_text())
    verification=json.loads((root/'verification.json').read_text())
    diagnostics=json.loads((root/'diagnostics.json').read_text())
    summaries=[];rows=[]
    for c in chosen:
        per_profile={}
        for profile in PROFILES:
            counts={}
            for arithmetic in ('float','quantized','no_recurrence'):
                found=[r for r in results if r['shape']==c['shape'] and r['profile']==profile and r['arithmetic']==arithmetic]
                counts[arithmetic]=sum(r['pass_all'] for r in found)
                for r in found:
                    rows.extend(dict(shape=c['shape'],**condition) for condition in r['conditions'])
            per_profile[profile]=counts
        summaries.append(dict(shape=c['shape'],qualified=all(p['float']>=5 for p in per_profile.values()),profiles=per_profile))
    write_json(root/'qualification.json',summaries)
    screen_rows=[dict(shape=r['shape'],profile=r['profile'],regime=r['regime'],seed=r['seed'],
                      epochs=r['epochs'],status=r['status'],selected_epoch=r['selected_epoch'],
                      **{k:r['selected'][k] for k in ('exact_messages','valid_messages','boundary_errors','boundary_f1','false_events','dev_loss')})
                 for r in screen['completed']]
    with (root/'screen_summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(screen_rows[0]));writer.writeheader();writer.writerows(screen_rows)
    fields=sorted({k for row in rows for k in row})
    with (root/'per_condition.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    cost=[costs(c) for c in chosen];write_json(root/'costs.json',cost)
    plots(root,chosen)
    demos=root/'demonstration_configs';demos.mkdir(exist_ok=True)
    for c in chosen:
        dest=demos/c['shape'];dest.mkdir(exist_ok=True)
        write_json(dest/'shape.json',make_shape(c['variant'],c['nodes']).config())
        for profile in PROFILES:
            regime=c['profiles'][profile]['regime']
            src=root/'models'/c['shape']/profile/f'{regime}_11'/'selected.npz'
            shutil.copy2(src,dest/f'{profile}_seed11.npz')
        (dest/'README.md').write_text('These are measured demonstration configurations, not production weights. Seed 11 is a reproducible example, not a claim of qualification. Load with the shared shape mask and profile-specific event-only assembly.\n')
    screen_limited=sum(r['status']=='training_limited' for r in screen['completed'])
    epochs=[r['epochs'] for r in finals['completed']]
    text=['# Measured reservoir shape search','',
          f"**{sum(r['qualified'] for r in summaries)} of the two final candidates qualify.** The fixed-hardware search, floating-point qualification, and integer replay are separate results.",'',
          '## Two strongest measured candidates','',
          '| Shape | Allocation | Why it advanced | Qualification |','| --- | --- | --- | --- |']
    for c,q in zip(chosen,summaries):
        text.append(f"| {c['shape']} | {' → '.join(map(str,map(len,make_shape(c['variant'],c['nodes']).groups)))} | Development-only weakest-profile ranking after six-seed continuation | {'qualified' if q['qualified'] else 'not qualified'} |")
    text+=['','These are fully trained sparse recurrent networks inspired by reservoir computing. The broad search also includes fixed-reservoir, readout-only ESN controls. Each physical mask, input route, activation, readout and schedule remains identical across protocol configurations. Learned weights are demonstration configurations.','',
           '## Fresh confirmation','',
           'Pass counts below require the entire profile suite, including all timing conditions, malformed/background rejection and startup/recovery. The gate is at least five of six seeds for **every** profile. Message exactness includes frame/transaction boundaries; boundaries are compared at exact causal reference ticks, with no tolerance added after seeing results.','',
           '| Shape | Profile | Float passing seeds / 6 | Fixed-point passing seeds / 6 | No-recurrence control / 1 |',
           '| --- | --- | ---: | ---: | ---: |']
    for q in summaries:
        for profile,p in q['profiles'].items():text.append(f"| {q['shape']} | {profile} | {p['float']} | {p['quantized']} | {p['no_recurrence']} |")
    text+=['','Unmet five-of-six requirements:','']
    for q in summaries:
        failed=[f"{p} ({v['float']}/6)" for p,v in q['profiles'].items() if v['float']<5]
        text.append(f"- **{q['shape']}**: {', '.join(failed) if failed else 'none'}.")
    text+=['','| Shape | Profile | Exact-message accuracy range across valid conditions and seeds |',
           '| --- | --- | ---: |']
    for c in chosen:
        for profile in PROFILES:
            values=[r['message_accuracy'] for r in rows if r['shape']==c['shape'] and r['profile']==profile and r['arithmetic']=='float' and r['kind']=='valid']
            text.append(f"| {c['shape']} | {profile} | {100*min(values):.2f}%–{100*max(values):.2f}% |")
    text+=['','Detailed per-condition counts, failed seeds, exact-message rates, boundary errors and accepted-invalid counts are in [per_condition.csv](runs/run01/per_condition.csv). Every condition retains its complete prediction trace and accepted/expected message records under `runs/run01/confirmation/`.','',
           'Each valid timing condition contains at least 1,000 complete messages. Every condition includes all byte values, 0x00/0xff/0x55/0xaa, random payloads and a 1,024-byte message. UART covers nominal, ±3%, bounded one-tick edge jitter, combined corners and gaps. I2C covers duty, pauses/stretching and repeated START, with read/write direction, ninth-clock ACK/NACK and additional address/write NACK examples. SPI covers modes 0–3, duty, pauses and one-tick setup. Invalid/partial transfers and break/parity/framing recovery are separate.','',
           'The ambiguous prefix after midstream startup is measured but is not required to be rejected: it can be indistinguishable from valid traffic. Qualification resumes after an observable synchronization opportunity. Long idle and cold startup are retained; no between-message state reset is supplied.','',
           '## Training adequacy and limits','',
           f"The screen completed {len(screen['completed'])} fits across 27 physical shapes (six families, with current/registered scheduling variants), 32/48/64 nodes, three seeds, seven profiles and two training regimes. Every fit received 60 epochs: the requested initial 30 plus a matched extra block before ranking. {screen_limited} screening fits remained improving and are explicitly **training-limited**, not architectural failures.",'',
           f"Four shapes advanced to six seeds (11,29,47,71,101,131), totaling {len(finals['completed'])} finalist fits. Finalist runs reached {min(epochs)}–{max(epochs)} epochs. Continuation used the requested message/boundary/loss improvement rule, then two stale blocks, lower-learning-rate continuation and a 1,024-tick window rescue. A recorded plateau is a plateau of this recipe and corpus, **not proof that the architecture lacks capacity**.",'',
           'Training uses three fixed, independently seeded continuous curricula of at least 8,192 ticks per profile. The first five epochs use clean short traffic, the next five repeated patterns, and all remaining epochs the mixed distribution. This is a modest training corpus; repeated epochs do not equal fresh examples. Exposure counts and optimizer steps are retained in each checkpoint. Training never uses confirmation payloads or boundaries. Larger/diversified training data remain a possible remedy; no architectural impossibility claim is made.','',
           'Checkpoint selection uses complete development messages, then boundary errors, false accepted messages, false events, and loss. Development selection sees about 8,192 ticks per profile; this small development sample is a limitation. Every epoch, including worse checkpoints, is retained with Adam moments and ending recurrent state. States and feature ages continue through messages and truncations; each independent epoch stream begins cold.','',
           '## Timing, resources and configurations','',
           '| Shape | Nodes | Weights + biases | Input / registered / same-tick edges | MACs per tick | Q12 model bytes | Tanh evaluations / tick |',
           '| --- | ---: | ---: | --- | ---: | ---: | ---: |']
    for c in cost:text.append(f"| {c['shape']} | {c['nodes']} | {c['weights_and_biases']} | {c['input_connections']} / {c['registered_connections']} / {c['same_tick_connections']} | {c['multiply_accumulates_per_tick']} | {c['model_storage_q12_bytes']} | {c['tanh_per_tick']} |")
    text+=['','These counts exclude no reservoir branch. The full [cost ledger](runs/run01/costs.json) separately lists leaks, state banks, preprocessing, pulse register, lane mapping, shared divider, accumulator width, activation scheduling and assembly storage. The Q12 activation table adds 8,194 bytes if stored literally. The Python assembler is not synthesized; its buffer/control area is unmeasured, so model parameter counts are not total chip area.','',
           'Fixed-point replay uses signed Q3.12 weights/states, integer Q24 accumulation in 64-bit accumulators, specified nearest rounding and a 4,097-entry Q12 tanh table. It is independently checked against scalar integer calculations. This is simulation evidence, not RTL, post-route timing or electrical qualification. `clock_hz` remains 0.','',
           'Observation and decision ticks are explicit in the event interface. There is no look-ahead or decision buffer. UART labels sample at offsets 7,23,… from a visible start edge. I2C commits bits on the falling edge ending the high phase; that includes a high-phase delay from the preceding rising-edge observation. Current-layer computation requires sequential within-tick activation stages; registered layers use the preceding tick. Physical decision time depends on an unimplemented schedule/clock and is not measured in seconds.','',
           'Exact masks, node leaks, allocations and demonstration weights are in [demonstration_configs](runs/run01/demonstration_configs/). Seed 11 is provided consistently rather than chosen to conceal seed failures. All six seeds remain under `models/`.','']
    for c in chosen:text+=[f"![{c['shape']} connection diagram](runs/run01/figures/{c['shape']}_connections.png)",'']
    text+=['![UART learning curves](runs/run01/figures/uart_learning_curves.png)','',
           '## Audits and deferred work','',
           f"Artifact verification: {'PASS' if verification['passed'] else 'FAIL'}; {verification['checkpoints_checked']} checkpoints checked; {verification['preservation_checked']} pre-existing files checked for preservation. Analytic gradients were checked numerically for every schedule. Causal prefix, online/batch state, repeated-bit occurrence, every-byte corner cases, malformed recovery, integer replay, and exact epoch-59→60 continuation checks passed. Fresh per-configuration replay audits accompany confirmation results.",'',
           'The [diagnostics](runs/run01/diagnostics.json) report memory gradients through 16/64/176/512/1024 ticks and close states with conflicting labels. These diagnose fitted configurations; small gradients or near-collisions alone do not prove an architectural information bound. No-recurrence controls remove within-layer recurrent weights while retaining inter-layer routes, generic edge-age preprocessing and leak state; they are not memoryless classifiers.','',
           'Pre-training generator/reference failures are preserved in [HARNESS_FAILURES.md](HARNESS_FAILURES.md). The earlier UART/I2C studies and unrelated working-tree changes remain intact. No reference-design gate or specification was changed.','',
           'USB low-speed and 10BASE-T are **not attempted** because mandatory qualification was not achieved; both are untested scope, not failed architectures. The 20–24-node successful-family reduction is deferred because no family met the mandatory multi-protocol gate. No 72-node comparison was authorized by the required specific 64-node memory diagnosis, so none was substituted for adequate training.','',
           '## Reproduce','',
           'From the repository root, use a fresh output directory (never overwrite this run):','',
           '```sh',
           'export OPENBLAS_NUM_THREADS=1',
           'PY=/home/daniel/stuff/THICotPCotDUIF/work/study/.venv/bin/python',
           'OUT=work/study/protocol_hero_search/runs/reproduction01',
           '$PY -B -m work.study.protocol_hero_search.run generate --output "$OUT"',
           '$PY -B -m unittest work.study.protocol_hero_search.test_experiment -v',
           '$PY -B -m work.study.protocol_hero_search.run screen --output "$OUT" --workers 8',
           '$PY -B -m work.study.protocol_hero_search.run select --output "$OUT"',
           '$PY -B -m work.study.protocol_hero_search.run finalists --output "$OUT" --workers 8',
           '$PY -B -m work.study.protocol_hero_search.validation continuation --output "$OUT"',
           '$PY -B -m work.study.protocol_hero_search.evaluation freeze --output "$OUT"',
           '$PY -B -m work.study.protocol_hero_search.evaluation generate --output "$OUT"',
           '$PY -B -m work.study.protocol_hero_search.evaluation evaluate --output "$OUT" --workers 8',
           '$PY -B -m work.study.protocol_hero_search.evaluation diagnostics --output "$OUT"',
           '$PY -B -m work.study.protocol_hero_search.validation verify --output "$OUT"',
           '$PY -B -m work.study.protocol_hero_search.report --output "$OUT"',
           '```','',
           'Python/NumPy, a C++17 compiler and Matplotlib are required. Compilation uses double arithmetic without fast-math. Dataset, topology, weight and selection hashes are retained. CPU/compiler differences may prevent bitwise identity; the tests and full confirmation remain required. See [the supplied plan](PLAN.md), [research rationale](RESEARCH.md), and [protocol source/profile details](PROFILES.md).']
    report='\n'.join(text)+'\n'
    local_report=report.replace('runs/run01/','')
    for name in ('PLAN.md','RESEARCH.md','PROFILES.md','HARNESS_FAILURES.md'):
        local_report=local_report.replace(f']({name})',f'](../../{name})')
    (root/'REPORT.md').write_text(local_report)
    # Root report is the reviewable result for the default preserved run.
    if root.name=='run01':(ROOT/'REPORT.md').write_text(report)
    write_json(root/'delivery_manifest.json',{str(p.relative_to(root)):digest(p) for p in list(demos.rglob('*'))+list((root/'figures').glob('*')) if p.is_file()})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'runs'/'run01');a=p.parse_args();build(a.output)
