"""Frozen-result tables, paired uncertainty, plots, failure cases and cost notes."""
from pathlib import Path
import numpy as np
from .run import ROOT,read,save
from .scoring import summarize,in_window

TASKS=("pulse","biphase","clockdata","context","transfer")
FIELDS=("tp","fp","known","unknown","unknown_tp","transaction_ok","transactions")


def main():
    rows=read(ROOT/"artifacts/confirmation/summary.json")
    out=ROOT/"artifacts/analysis"
    out.mkdir(exist_ok=True)
    ids=list(dict.fromkeys(r["id"] for r in rows))
    rng=np.random.default_rng(61058291)
    rw=np.array([np.bincount(rng.integers(0,3,3),minlength=3) for _ in range(10000)])
    bw=np.array([np.bincount(rng.integers(0,8,8),minlength=8) for _ in range(10000)])
    tables={}; boot={}; stats={}; recovery={}
    for name in ids:
        tables[name]={}; stats[name]={}
        arr=np.zeros((5,3,8,len(FIELDS)))
        for ti,task in enumerate(TASKS):
            rs=[r for r in rows if r["id"]==name and r["task"]==task]
            metrics=summarize([x for r in rs for x in r["metrics"]["rows"]])
            conditions={c:summarize([x for r in rs for x,bc in zip(r["metrics"]["rows"],r["block_conditions"]) if bc[1]==c])
                        for c in rs[0]["metrics"]["conditions"]}
            splices=summarize([x for r in rs for x in r["splice_metrics"]["rows"]])
            tables[name][task]={"metrics":metrics,"conditions":conditions,"splice":splices,
                "resources_max":{k:max(r["resources"][k] for r in rs) for k in
                    ("parameter_bits","dynamic_state_bits","feature_count","contributions_per_gate","accumulator_bits")},
                "replicate_f1":[r["metrics"]["aggregate"]["f1"] for r in rs]}
            if "float_metrics" in rs[0]:
                fm=summarize([x for r in rs for x in r["float_metrics"]["rows"]])
                tables[name][task]["float_f1"]=fm["f1"]
                tables[name][task]["quantized_f1_delta"]=metrics["f1"]-fm["f1"]
            for r in rs:
                for x,(block,_) in zip(r["metrics"]["rows"],r["block_conditions"]):
                    arr[ti,r["replicate"],block]+=np.asarray([x[k] for k in FIELDS])
        draws=np.einsum('dr,db,trbk->dtk',rw,bw,arr,optimize=True)
        f1=2*draws[:,:,0]/np.maximum(1,draws[:,:,2]+draws[:,:,0]+draws[:,:,1])
        unk=draws[:,:,4]/np.maximum(1,draws[:,:,3])
        boot[name]={"f1":f1,"unknown":unk,"macro":f1[:,:4].mean(axis=1)}
        for ti,task in enumerate(TASKS):
            stats[name][task]={"f1_95":np.percentile(f1[:,ti],[2.5,97.5]).tolist(),
                               "unknown_95":np.percentile(unk[:,ti],[2.5,97.5]).tolist()}
        stats[name]["macro_core_f1_95"]=np.percentile(f1[:,:4].mean(axis=1),[2.5,97.5]).tolist()
    comparisons={}
    for a,b in (("binary_duration","raw_duration"),("binary_strict","sample20_latched"),
                ("binary_duration","recurrent32"),("binary_duration","linear_binary"),
                ("binary_strict","binary_duration")):
        differences=boot[a]["f1"]-boot[b]["f1"]
        comparisons[f"{a}_minus_{b}"]={t:np.percentile(differences[:,i],[2.5,97.5]).tolist() for i,t in enumerate(TASKS)}
        comparisons[f"{a}_minus_{b}"]["macro_core"]=np.percentile(differences[:,:4].mean(axis=1),[2.5,97.5]).tolist()
    save(out/"tables.json",tables)
    save(out/"uncertainty.json",{"draws":10000,"seed":61058291,
        "method":"paired crossed resampling of 3 fitted-model replicates and 8 independent stream blocks; all conditions/tasks remain in each block; empirical 95% percentile intervals; no multiple-comparison coverage claim",
        "models":stats,"paired_differences":comparisons})

    # Startup/error recovery and representative traces are read-only analyses.
    min_gate_gap=100000
    failures=[]
    for name in ("binary_duration","binary_strict","raw_duration"):
        recovery[name]={}
        for task in TASKS:
            ss=read(ROOT/"artifacts/confirmation"/f"{task}_streams.json.gz")
            vals={"first_complete_correct":0,"after_dropout_correct":0,"streams":0,"startup_false_known":0}
            for rep in range(3):
                pp=read(ROOT/"artifacts/confirmation"/f"{name}_{task}_{rep}_predictions.json.gz")["normal"]
                for s,p in zip(ss,pp):
                    if len(p)>1:
                        min_gate_gap=min(min_gate_gap,min(b["tick"]-a["tick"] for a,b in zip(p,p[1:])))
                    if s["condition"]=="recovery":
                        vals["streams"]+=1
                        first=s["events"][0]
                        following=s["events"][len(s["events"])//2+1]
                        for k,e in (("first_complete_correct",first),("after_dropout_correct",following)):
                            vals[k]+=int(any(q["class"]==e["class"] and in_window(q["tick"],e) for q in p))
                        vals["startup_false_known"]+=sum(q["class"]!=7 and q["tick"]<first["start"] for q in p)
                    if rep==0 and s["block"]==0 and s["condition"]=="novel":
                        bad=next(((e,q) for e in s["events"] if e["class"]==7 for q in p if q["class"]!=7 and in_window(q["tick"],e)),None)
                        if bad:
                            e,q=bad;lo=max(0,e["start"]-10);hi=e["end"]+18
                            failures.append({"model":name,"task":task,"seed":s["seed"],"truth":e,"prediction":q,
                                             "sample_start":lo,"samples":s["samples"][lo:hi]})
            recovery[name][task]=vals
    save(out/"recovery.json",recovery)
    save(out/"failure_examples.json",failures)

    ss=read(ROOT/"artifacts/confirmation/context_streams.json.gz")
    ix=next(i for i,s in enumerate(ss) if s["block"]==0 and s["condition"]=="mixed")
    s=ss[ix]
    trace={"selection":"predetermined first mixed context stream, block 0, fitted replicate 0", "stream":s,
           "predictions":{name:read(ROOT/"artifacts/confirmation"/f"{name}_context_0_predictions.json.gz")["normal"][ix]
                           for name in ("binary_duration","binary_strict","raw_duration","sample20_latched")}}
    save(out/"representative_trace.json",trace)

    selected=read(ROOT/"artifacts/frozen/binary_strict_context_0.json")
    acc=max(tables["binary_strict"][t]["resources_max"]["accumulator_bits"] for t in TASKS)
    hardware={"status":"analytical counts only; no RTL, synthesis, STA or pad evidence",
        "recommended_family":"16-entry run memory, 5 binary features/run, selected pair products, q8 readout",
        "run_payload_bits":80,"validity_counter_bits_conservative":5,"support_state_bits":18,
        "front_end_output_sync_bits":55,"parallel_dynamic_bits":158,
        "feature_count":600,"pair_sign_operations_per_gate":520,"coefficient_contributions_per_gate":1800,
        "loaded_parameter_bits_range":[min(tables['binary_strict'][t]['resources_max']['parameter_bits'] for t in TASKS),
                                       max(tables['binary_strict'][t]['resources_max']['parameter_bits'] for t in TASKS)],
        "max_accumulator_bits":acc,"margin_subtraction_bits":acc+1,
        "fixed_implementation_point":{"coefficient_bits":8,"bias_bits":8,"score_bits":18,"margin_difference_bits":19,
          "parameter_bits":(600+1)*3*8+2*18+2+50,
          "explanation":"All frozen binary configurations fit signed 8-bit biases. Provision fixed 18-bit scores from the worst case 601*128=76928, independent of fitted sparsity; 19-bit subtraction. Floor/margin storage is 18 bits. Reject future loaded configurations outside these bounds rather than silently widening hardware. Per-config minimal counts above are estimates, not distinct fabricated word widths."},
        "extra_computation":{"per_sample":"2 lane-majority votes (6 AND + 4 OR if literal), edge/idle compares, 8-bit age increment/saturation, 16-bit tick increment",
          "per_transition":"3 five-bit duration comparisons, 8-bit count increment, two five-bit min/max comparisons, up to 80 packed history-bit moves; reset validity on observed long-idle-to-activity",
          "per_gate":"16 shared slot-validity signals, 600 feature-valid enables, 520 pair XNOR/sign operations, 1800 coefficient sign/zero selections and additions, 3 bias loads, 3-way argmax, floor/margin checks, 4 support comparisons, timestamp subtraction and output register"},
        "accounting_note":"Frozen resources.py conservatively lists 112 raw-token bit moves per transition for binary memory; physical binary payload moves are 80. This clarification changes no configuration, decision, parameter count or confirmation result.",
        "serial_schedule":{"measured_min_gate_spacing_ticks":min_gate_gap,
          "mac_only_min_clocks_per_sample_at_that_spacing":int(np.ceil(1800/min_gate_gap)),
          "coefficient_contribution_cycles_per_gate":1800,"one_feature_issue_cycle_extra_if_serial":600,
          "additional_state_estimate":85+3*18+10+2+1+16,
          "detail":"Latch 80 run bits plus validity, use 3 accumulators, feature/class counters, busy bit and pending timestamp. Allows live receive state to keep updating. Throughput needs clock/tick ratio and scheduling validation; added emission delay is not in sampled-stream metrics."},
        "excluded_system_blocks":"RX/TX FIFOs, core/firmware, loader, TX table and physical pads; these are outside the recognizer and still consume chip resources"}
    save(out/"hardware_accounting.json",hardware)

    lines=["# Confirmation tables","", "Each cell pools three frozen fits × eight stream blocks. Transfer was excluded from architecture selection.","",
           "| Architecture | Pulse F1 | Biphase F1 | Clock/data F1 | Context F1 | Transfer F1 | Max config bits |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for name in ids:
        lines.append('| '+name+' | '+' | '.join(f"{100*tables[name][t]['metrics']['f1']:.1f}%" for t in TASKS)+f" | {max(tables[name][t]['resources_max']['parameter_bits'] for t in TASKS):,} |")
    for name in ids:
        lines += ["",f"## {name}","","| Task / condition | Precision | Recall | F1 | Unknown recall | False known / 1k ticks | Transactions | p95 latency |","|---|---:|---:|---:|---:|---:|---:|---:|"]
        for task in TASKS:
            for c,m in {"aggregate":tables[name][task]["metrics"],**tables[name][task]["conditions"]}.items():
                lines.append(f"| {task} / {c} | "+' | '.join(f"{100*m[k]:.1f}%" for k in ('precision','recall','f1','unknown_recall'))+f" | {m['false_per_1000']:.3f} | {100*m['transaction_success']:.1f}% | {m['latency_p95']} |")
    (out/"TABLES.md").write_text('\n'.join(lines)+'\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(10,5.2),layout='constrained')
    values=np.array([[tables[n][t]['metrics']['f1'] for t in TASKS] for n in ids])
    im=ax.imshow(values,vmin=.4,vmax=1,cmap='YlGnBu',aspect='auto')
    ax.set_xticks(range(5),['Pulse','Biphase','Clock/data','Long context','Held-out transfer'])
    ax.set_yticks(range(len(ids)),ids)
    ax.axvline(3.5,color='white',linewidth=3)
    for i in range(len(ids)):
        for j in range(5):
            ax.text(j,i,f'{100*values[i,j]:.1f}',ha='center',va='center',color='white' if values[i,j]>.8 else 'black')
    fig.colorbar(im,ax=ax,label='Known-event F1')
    ax.set_title('Fresh confirmation: four core tasks and a held-out signal family')
    fig.savefig(out/'comparison.png',dpi=180)
    plt.close(fig)

    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    for name in ids:
        cost=max(tables[name][t]['resources_max']['parameter_bits'] for t in TASKS)
        worst=min(tables[name][t]['metrics']['f1'] for t in TASKS[:4])
        ax.scatter(cost,worst,s=65)
        offset={'binary_strict':(5,-16),'raw_duration':(5,12)}.get(name,(5,5))
        ax.annotate(name,(cost,worst),xytext=offset,textcoords='offset points',fontsize=9)
    ax.axvline(32768,color='#a12c2c',linestyle='--',label='Study parameter budget')
    ax.set_xscale('log');ax.set_ylim(.35,1.02)
    ax.set_xlabel('Maximum loaded parameter bits (analytical)');ax.set_ylabel('Worst core-task F1')
    ax.set_title('Recognition / storage tradeoff — rejection failures remain separate')
    ax.legend(loc='lower right')
    fig.savefig(out/'tradeoff.png',dpi=180);plt.close(fig)

    fig,axes=plt.subplots(5,1,figsize=(12,6),sharex=True,layout='constrained')
    limit=min(700,len(s['samples']))
    axes[0].step(np.arange(limit),np.asarray(s['samples'][:limit])&1,where='post',color='#233d63')
    axes[0].set_ylabel('Input lane 0');axes[0].set_title('First mixed context stream, block 0 (preselected trace)')
    for ax,(name,pred) in zip(axes[1:],trace['predictions'].items()):
        for e in s['events']:
            if e['end']<limit:
                ax.axvline(e['end'],color='#999999',alpha=.3)
                ax.scatter(e['end']+10,e['class'],s=55,facecolors='none',edgecolors='black')
        p=[p for p in pred if p['tick']<limit]
        ax.scatter([p['tick'] for p in p],[p['class'] for p in p],s=15,color='#c44e52')
        ax.set_yticks([0,1,7]);ax.set_ylim(-.5,7.6);ax.set_ylabel(name,fontsize=8)
    axes[-1].set_xlabel('Sample tick; hollow circles = intended event, red = emitted class')
    fig.savefig(out/'trace.png',dpi=180);plt.close(fig)
    print('Wrote tables, uncertainty, hardware accounting, failures and three figures.')


if __name__=='__main__':
    main()
