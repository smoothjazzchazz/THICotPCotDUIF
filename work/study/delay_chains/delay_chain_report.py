"""Plots and a compact evidence index for the frozen delay-chain experiment."""

import base64
from html import escape

import numpy as np
from matplotlib.patches import Rectangle

from work.study.shared.comparison import METHODS
from work.study.shared.report import plt, save_figure


def plot_chain_position(output, timing):
    nominal = next(row for row in timing["records"] if row["range"] == 1
                   and row["nominal_known"] == [3, 8] and row["first_delta"] == 0
                   and row["gap"] == 3 and row["second"] == 8)
    figure, axes = plt.subplots(2, 2, figsize=(14, 6.5), layout="constrained")
    for row, name in enumerate(("age_chain", "level_chain")):
        for col, pair in enumerate(((3, 8), (8, 8))):
            ax = axes[row, col]
            states = np.asarray(nominal["candidates"][name]["decision_states"][col])
            ax.imshow(states, cmap="RdBu_r", vmin=-5, vmax=5, aspect="auto")
            for offset in range(4):
                for node in range(16):
                    ax.text(node, offset, str(states[offset, node]), ha="center", va="center", fontsize=8)
                ax.add_patch(Rectangle((11.5 + offset, offset - .5), 1, 1,
                                       fill=False, edgecolor="#d97b00", linewidth=3))
            ax.set_xticks(range(16))
            ax.set_yticks(range(4))
            ax.set_xlabel("Node = input delay in ticks")
            ax.set_ylabel("Decision offset")
            ax.set_title(f"{name}: {pair}")
    figure.suptitle("Nominal first-pulse last high sample: nodes 12 → 13 → 14 → 15 (orange)\n"
                     "Updated integer states; age magnitudes can differ while signs agree")
    save_figure(figure, output, "chain_position")


def plot_separation(output, records):
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
    colors = plt.get_cmap("tab10").colors
    for index, record in enumerate(records):
        for row, pair in enumerate(record["memory"]["comparisons"]):
            for col, encoding in enumerate(("full", "bits")):
                ax = axes[row, col]
                ax.plot(range(4), pair[encoding]["reset_distance"], color=colors[index],
                        linestyle=":", linewidth=3, alpha=.7)
                ax.plot(range(4), pair[encoding]["cross_context_min_distance"],
                        color=colors[index], marker="o", label=record["name"])
                ax.set_title(f"{tuple(pair['known'])} vs {tuple(pair['unknown'])}")
                ax.set_ylabel("Full-state L1 distance" if encoding == "full" else "Differing sign bits")
                ax.set_xticks(range(4))
                ax.set_xlabel("Decision offset")
                ax.grid(alpha=.2)
    for ax in axes.flat:
        ax.set_ylim(bottom=-.3)
    axes[0, 0].legend(fontsize=8)
    figure.suptitle("Nominal separation at each updated decision tick\n"
                     "Dotted: reset; solid: minimum across independently varying prefixes")
    save_figure(figure, output, "separation")

    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for index, ax in enumerate(axes):
        for color, record in zip(colors, records):
            full = record["memory"]["comparisons"][index]["full"]
            ax.plot(range(4), full["within_target_max_distance"], marker="o", color=color,
                    label=record["name"])
        pair = records[0]["memory"]["comparisons"][index]
        ax.set_title(f"{tuple(pair['known'])} / {tuple(pair['unknown'])}")
        ax.set_xticks(range(4))
        ax.set_xlabel("Decision offset")
        ax.set_ylabel("Maximum same-target prefix L1 difference")
        ax.set_ylim(bottom=-.1)
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    figure.suptitle("Unrelated prefix variation, measured separately from target separation")
    save_figure(figure, output, "prefix_variation")


def plot_boundary(output, timing):
    rows = [r for r in timing["records"] if r["range"] == 2 and r["nominal_known"] == [3, 8]
            and r["first_delta"] == 0]
    figure, axes = plt.subplots(2, 4, figsize=(15, 8), layout="constrained")
    for row, name in enumerate(("age_chain", "level_chain")):
        maximum = max(max(r["candidates"][name]["full_distance"]) for r in rows)
        for offset, ax in enumerate(axes[row]):
            values = np.zeros((5, 5), dtype=int)
            outside = np.zeros((5, 5), dtype=bool)
            for record in rows:
                i, j = record["gap"] - 1, record["second"] - 6
                values[i, j] = record["candidates"][name]["full_distance"][offset]
                outside[i, j] = not record["last_first_high_inside"][offset]
            ax.imshow(values, vmin=0, vmax=max(1, maximum), cmap="Blues", origin="lower")
            for i, j in np.ndindex(values.shape):
                ax.text(j, i, f"{values[i, j]}{' ×' if outside[i, j] else ''}",
                        ha="center", va="center", fontsize=9,
                        color="white" if values[i, j] > maximum * .55 else "black")
            ax.add_patch(Rectangle((.5, .5), 3, 3, fill=False, edgecolor="#bd6a00", linewidth=2))
            ax.add_patch(Rectangle((1.5, 1.5), 1, 1, fill=False, edgecolor="#147d67", linewidth=3))
            ax.set_xticks(range(5), range(6, 11))
            ax.set_yticks(range(5), range(1, 6))
            ax.set_xlabel("Second-pulse width")
            ax.set_ylabel("Internal gap")
            ax.set_title(f"{name} · offset {offset}")
    figure.suptitle("Timing boundary: full-state distance, (3, second) vs (8, second)\n"
                     "Green: nominal; orange: ±1 range; full grid: ±2; ×: last first high is older than 15 ticks")
    save_figure(figure, output, "timing_boundary")


def plot_recognition(output, records):
    figure, axes = plt.subplots(len(records), 3, figsize=(13, 12), layout="constrained")
    for row, record in enumerate(records):
        for col, method in enumerate(("hamming", "linear_bits", "linear_full")):
            groups = record["decision_counts"][method]
            values = np.asarray([
                record["probe_readouts"][method]["pairs"][pair]["continuous_recall_by_tick"]
                for pair in groups]) * 100
            ax = axes[row, col]
            ax.imshow(values, vmin=0, vmax=100, cmap="Blues", aspect="auto")
            for index, group in enumerate(groups.values()):
                for offset, counts in enumerate(group["continuous"]):
                    predicted = max(counts, key=counts.get)
                    ax.text(offset, index, f"{values[index, offset]:.0f}% → {predicted}",
                            ha="center", va="center", fontsize=8,
                            color="white" if values[index, offset] > 55 else "black")
            ax.set_yticks(range(5), [f"{pair}: {group['target']}" for pair, group in groups.items()])
            ax.set_xticks(range(4))
            ax.set_xlabel("Decision offset")
            ax.set_title(f"{record['name']} · {METHODS[method]}", fontsize=10)
    figure.suptitle("Actual trained decisions across 50 continuous prefixes\n"
                     "Cells: correct fraction → most frequent prediction; target class is in each row label")
    save_figure(figure, output, "recognition")


def write_delay_report(output, audit, result, timing):
    records = audit["candidates"]
    plot_chain_position(output, timing)
    plot_separation(output, records)
    plot_boundary(output, timing)
    plot_recognition(output, records)

    def embedded(name):
        data = base64.b64encode((output / f"{name}.png").read_bytes()).decode()
        return f'<img alt="{name.replace("_", " ")}" src="data:image/png;base64,{data}">'

    audit_rows, metric_rows = [], []
    for record in records:
        name = record["name"]
        reasons = "; ".join(record["rejection_reasons"]) or "Passed screens"
        audit_rows.append(
            f"<tr><th><a href='{name}/report.html'>{name}</a> ({record['role']})</th>"
            f"<td>{record['training']['distinct_binary_fingerprints']}</td>"
            f"<td>{record['training']['saturated_state_fraction']:.1%}</td>"
            f"<td>{record['initial_state']['maximum_tail_gap']}</td>"
            f"<td>{escape(reasons)}</td></tr>")
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
                    f"<td>{metrics['matched_events']}</td><td>{metrics['missed_events']}</td>"
                    f"<td>{metrics['false_events']}</td><td>{metrics['event_precision']:.1%}</td>"
                    f"<td>{metrics['event_f1']:.1%}</td><td>{metrics['unknown_recall']:.1%}</td>"
                    f"<td>{metrics['median_latency_ticks']} / {metrics['p95_latency_ticks']}</td></tr>")
    outcome = audit["selected_candidate"] or "None: neither chain passed eligibility"
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finite delay-chain experiment</title><style>
body{{font:16px/1.5 system-ui;background:#f5f7f7;color:#24333b;margin:auto;max-width:1350px;padding:24px}}
section{{background:white;padding:20px;margin:20px 0}}img{{max-width:100%}}table{{border-collapse:collapse;font-size:13px}}
th,td{{padding:8px;text-align:left;border-bottom:1px solid #ddd}}.scroll{{overflow-x:auto}}a{{color:#176b77}}
</style><h1>Does explicit finite memory make pulse pairs recognizable?</h1>
<p>Selected: <strong>{escape(outcome)}</strong>. One 16-node, six-bit integer reservoir runs at a time.
The two chains differ only in the age input. Legacy controls also differ in topology and input placement.</p>
<section><h2>Frozen experiment</h2><p>{escape(result['selection_policy'])}</p>
<p>Training/validation seed 23 and original stream counts/distributions. Local records were checked
before reserving test seed 105. Configurations, readouts, validation choices and eligibility were saved
and reloaded before generating any held-out streams. All configurations share the same 24 test streams.
Seeds 23, 24 and 104 are prior development evidence; scores on them are not controlled improvement evidence.</p>
<p><a href="plan.json">Plan</a> · <a href="freeze.json">Freeze hashes</a> ·
<a href="config.json">Complete settings</a> · <a href="selection.json">Selection audit</a> ·
<a href="metrics.json">All metrics and dataset hashes</a> · <a href="timing.json">Timing diagnostic</a> ·
<a href="memory_traces.json.gz">Probe inputs, states, scores and decisions</a></p></section>
<section><h2>Finite memory and timing</h2><p>At tick t, after the update, state[i] = q(t−i).
Node 0 uses signed_level − log_age, or signed_level for the ablation. A chain stores the current
input and 15 previous ticks. The last first-pulse high has delay gap + second width + 1 + offset.
Nominal delays are 12–15; ±1 variation can reach 17 and ±2 can reach 19 at offset 3.</p>
{embedded('chain_position')}<p>Both chains erase arbitrary initial reservoir values by update 16 under
identical features: each update replaces one more downstream initial value. The saved extreme-state
probe verifies that bound. This is a reservoir-state property, not a claim that arbitrary FeatureExtractor
state converges in 16 ticks or that pulse recognition succeeds.</p>
{embedded('timing_boundary')}<p>This deterministic development grid is separate from fresh test results.
It changes gap and second width across both duration ranges, plus matched first-width changes in the
saved diagnostic. It does not cover every waveform or glitch. Outside the horizon the first pulse
cannot remain in either chain; collisions can also occur inside it because encoding loses information.</p></section>
<section><h2>Memory and actual recognition</h2>{embedded('separation')}{embedded('prefix_variation')}
<p>Reset probes use 20 low ticks. Continuous probes use every ordered pair of five nominal patterns,
12/20-tick rests, and all five target patterns. No reset occurs at a pattern boundary. Distances compare
states after each of the four updates beginning at the final falling edge. Full audit includes matched
prefix distances, cross-prefix collisions and same-target variation.</p>{embedded('recognition')}
<p>Accuracy here is before stabilization, by exact target and offset. Full class counts and reset decisions
are in selection.json; all reference decisions are in the probe traces. State separation, convergence,
or a high known-event F1 alone do not establish successful known/unknown recognition.</p></section>
<section><h2>Eligibility</h2><div class="scroll"><table><tr><th>Configuration/report</th>
<th>Fingerprints</th><th>Saturation</th><th>Initialization gap</th><th>Rejection reasons</th></tr>
{''.join(audit_rows)}</table></div></section>
<section><h2>Fresh held-out recognition</h2><p>Clean results are separate from pooled clean/jitter/glitches/mixed
results. Known-event matching uses the unchanged six-tick window; duplicates, early, late and wrong events
are false detections. Unknown recall measures decision ticks. Median/p95 latency describes matched events only.
Per-configuration reports show every condition, confusion matrices and the first mixed trace.</p>
<div class="scroll"><table><tr><th>Configuration</th><th>Readout</th><th>Condition</th><th>Known detections</th>
<th>Misses</th><th>False detections</th><th>Precision</th><th>F1</th><th>Unknown recall</th><th>Latency median/p95</th></tr>
{''.join(metric_rows)}</table></div><p>Streaming reload checks passed for every test and nominal probe.
No settings changed after test generation. Floating-point readouts are research diagnostics; this work
changes no RTL, firmware, released specification, electrical claim, clock rate or project gate.</p></section></html>"""
    (output / "report.html").write_text(html)
