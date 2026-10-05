"""Memory-window plots and an audit index for the separate leak experiment."""

import base64
from html import escape

import numpy as np

from work.study.shared.comparison import METHODS
from work.study.shared.report import plt, save_figure


def write_mixed_report(output, audit, result):
    """Show all controls and mixtures, including rejected candidates."""
    records = audit["candidates"]
    figure, axes = plt.subplots(4, 2, figsize=(12, 13), layout="constrained")
    colors = plt.get_cmap("tab10").colors
    for index, record in enumerate(records):
        for pair_index, pair in enumerate(record["memory"]["comparisons"]):
            for row, (encoding, window) in enumerate((
                    ("full", "reset_distance"), ("bits", "reset_distance"),
                    ("full", "continuous_min_distance"), ("bits", "continuous_min_distance"))):
                ax = axes[row, pair_index]
                ax.plot(range(4), pair[encoding][window], marker="o", color=colors[index],
                        linestyle="--" if record["name"].startswith("uniform") else "-",
                        label=record["name"])
                ax.set_xticks(range(4))
                ax.grid(alpha=.2)
                if row == 0:
                    ax.set_title(f"{tuple(pair['known'])} vs {tuple(pair['unknown'])}")
    # Set the lower bound after every curve is present; doing it earlier freezes
    # autoscaling at the all-zero control and clips the later candidate curves.
    for ax in axes.flat:
        ax.set_ylim(bottom=-.3)
    labels = ("Reset: full-state L1", "Reset: differing sign bits",
              "Continuous: minimum L1", "Continuous: minimum differing bits")
    for row, label in enumerate(labels):
        axes[row, 0].set_ylabel(label)
    for ax in axes[-1]:
        ax.set_xlabel("Decision offset (0 = final falling edge)")
    axes[0, 0].legend(fontsize=8, ncols=2)
    figure.suptitle("First-pulse information through all four decision ticks\n"
                     "Continuous curves take the minimum across 50 matched prefixes")
    save_figure(figure, output, "memory")

    figure, axes = plt.subplots(1, 2, figsize=(12, 5.5), layout="constrained")
    for index, pair in enumerate(records[0]["memory"]["comparisons"]):
        values = []
        for record in records:
            full = record["memory"]["comparisons"][index]["full"]
            values.append(np.asarray(full["cross_context_min_distance"])
                          - np.asarray(full["within_target_max_distance"]))
        values = np.asarray(values)
        limit = max(1, int(np.abs(values).max()))
        plot = axes[index].imshow(values, cmap="RdBu", vmin=-limit, vmax=limit, aspect="auto")
        for row in range(len(records)):
            for tick in range(4):
                axes[index].text(tick, row, str(values[row, tick]), ha="center", va="center",
                                 color="white" if abs(values[row, tick]) > .6 * limit else "black")
        axes[index].set_yticks(range(len(records)), [r["name"] for r in records])
        axes[index].set_xticks(range(4))
        axes[index].set_xlabel("Decision offset")
        axes[index].set_title(f"{tuple(pair['known'])} vs {tuple(pair['unknown'])}")
        figure.colorbar(plot, ax=axes[index], label="Cross-target distance − prefix diameter")
    figure.suptitle("Does unrelated history exceed the task distinction?\n"
                     "Negative: prefix variation is larger; zero may also mean no memory")
    save_figure(figure, output, "context")

    def embedded(name):
        data = base64.b64encode((output / f"{name}.png").read_bytes()).decode()
        return f'<img alt="{name} diagnostics" src="data:image/png;base64,{data}">'

    audit_rows = []
    metric_rows = []
    for record in records:
        name = record["name"]
        reasons = "; ".join(record["rejection_reasons"]) or "Eligible"
        probe = record["probe_readouts"]["linear_full"]
        audit_rows.append(
            f"<tr><th><a href='{name}/report.html'>{name}</a></th>"
            f"<td>{record['training']['saturated_state_fraction']:.1%}</td>"
            f"<td>{record['initial_state']['maximum_tail_gap']}</td>"
            f"<td>{probe['minimum_continuous_recall']:.1%}</td><td>{escape(reasons)}</td></tr>")
        for method in METHODS:
            if method == "run_length" and name != records[0]["name"]:
                continue
            for condition in ("clean", "aggregate"):
                candidate = result["candidates"][name]
                metrics = (candidate["aggregate"] if condition == "aggregate"
                           else candidate["conditions"][condition])[method]
                label = "reference" if method == "run_length" else name
                metric_rows.append(
                    f"<tr><th>{label}</th><td>{METHODS[method]}</td><td>{condition}</td>"
                    f"<td>{metrics['matched_events']}/{metrics['expected_events']}</td>"
                    f"<td>{metrics['predicted_events'] - metrics['matched_events']}</td>"
                    f"<td>{metrics['event_precision']:.1%}</td><td>{metrics['event_f1']:.1%}</td>"
                    f"<td>{metrics['unknown_recall']:.1%}</td>"
                    f"<td>{metrics['false_events_per_1000_ticks']:.2f}</td>"
                    f"<td>{metrics['median_latency_ticks']} / {metrics['p95_latency_ticks']}</td></tr>")
    outcome = audit["selected_candidate"] or "None: every candidate failed eligibility"
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mixed per-node leak experiment</title><style>
body{{font:16px/1.5 system-ui;background:#f5f7f7;color:#24333b;margin:auto;max-width:1250px;padding:24px}}
section{{background:white;padding:20px;margin:20px 0}}img{{max-width:100%}}table{{border-collapse:collapse;font-size:13px}}
th,td{{padding:8px;text-align:left;border-bottom:1px solid #ddd}}.scroll{{overflow-x:auto}}a{{color:#176b77}}
</style><h1>Does mixed retention preserve the first pulse?</h1>
<p>Selected: <strong>{escape(outcome)}</strong>. Failed candidates below are diagnostic controls,
not accepted receivers. One 16-node six-bit reservoir runs at a time; only leak shifts differ.</p>
<section><h2>Frozen policy and evidence</h2><p>{escape(result['selection_policy'])}</p>
<p>Training/validation seed 23; fresh test seed 104. Every candidate saw identical held-out
streams after all settings and eligibility were saved. No held-out results changed settings.
Earlier inspected test runs are development evidence, not controlled comparisons here.</p>
<p><a href="plan.json">Plan and source hashes</a> · <a href="selection.json">Full audit</a> ·
<a href="config.json">Frozen configurations</a> · <a href="metrics.json">Metrics</a> ·
<a href="memory_traces.json.gz">Probe inputs, states, scores and decisions</a></p></section>
<section><h2>Memory and sign quantization</h2>{embedded('memory')}
<p>Each reset probe begins with 20 low ticks. Pulse gaps are three ticks. Continuous probes
prepend every ordered pair of the five nominal patterns, with 12 or 20 low ticks after each.
The model resets only at stream start. Each point compares updated states at the same relative
decision offset, not at the same absolute tick. Zero means identical snapshots.</p>
{embedded('context')}<p>Prefix diameter is the maximum within-target L1 distance across histories.
Cross-target distance is the minimum over independently varying histories. This conservative
distance comparison is descriptive; readout decisions establish whether retained information
is usable. Finite prefixes and initialization tests cannot establish fading memory on all inputs.</p></section>
<section><h2>Eligibility audit</h2><div class="scroll"><table><tr><th>Candidate/report</th>
<th>Saturation</th><th>Initialization gap</th><th>Worst full-state probe recall</th><th>Reasons</th></tr>
{''.join(audit_rows)}</table></div></section>
<section><h2>Fresh held-out recognition</h2><p>Aggregate pools clean, jitter, glitches and mixed
conditions. Known detections match once within the original six-tick event window. False counts
include early, late, duplicate and wrong events; unknown recall uses four decision ticks.
Latency median/p95 covers matched events only. Per-candidate reports include all condition metrics,
confusion plots and the first mixed stream, with full traces and streaming reload verification.</p>
<div class="scroll"><table><tr><th>Candidate</th><th>Readout</th><th>Condition</th><th>Known matched/expected</th>
<th>False events</th><th>Precision</th><th>F1</th><th>Unknown recall</th><th>False/1k ticks</th>
<th>Latency median/p95</th></tr>{''.join(metric_rows)}</table></div>
<p>Float linear coefficients remain a diagnostic. This experiment changes no model arithmetic,
feature encoding, reset behavior, RTL, released specifications, firmware, or project gates.</p></section></html>"""
    (output / "report.html").write_text(html)
