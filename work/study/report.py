"""Portable HTML and scientific plots for one frozen comparison run."""

import base64
from html import escape
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "thic-study-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from work.study.comparison import METHODS
from work.study.signals import CLASS_IDS, CLASS_NAMES


COLORS = ("#237c79", "#7498ad", "#c15e30", "#626775")


def save_figure(figure, output, name):
    figure.savefig(output / f"{name}.png", dpi=150, bbox_inches="tight")
    figure.savefig(output / f"{name}.svg", bbox_inches="tight")
    plt.close(figure)


def write_report(output, result, streams, states, traces):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "white"})
    aggregate = result["aggregate"]
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout="constrained")
    metrics = ("event_f1", "balanced_accuracy", "unknown_recall")
    locations = np.arange(3)
    for i, (method, title) in enumerate(METHODS.items()):
        values = [aggregate[method][key] * 100 for key in metrics]
        axes[0].bar(locations + (i - 1.5) * .19, values, width=.18,
                    label=title, color=COLORS[i])
        axes[1].plot(list(result["conditions"]),
                     [entry[method]["event_f1"] * 100
                      for entry in result["conditions"].values()],
                     marker="o", label=title, color=COLORS[i])
    axes[0].set_xticks(locations, ["Event F1", "Balanced\ntick accuracy", "Unknown\nrecall"])
    axes[0].set_title("Held-out streams · all conditions")
    axes[1].set_title("Detection under signal perturbations")
    for ax in axes:
        ax.set_ylim(0, 105)
        ax.set_ylabel("Percent")
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
    axes[1].legend(fontsize=8, loc="best")
    save_figure(figure, output, "comparison")

    figure, axes = plt.subplots(2, 2, figsize=(9, 8), layout="constrained")
    for ax, (method, title) in zip(axes.flat, METHODS.items()):
        counts = np.asarray(aggregate[method]["confusion"])
        # Normalize each target class separately so background cannot dwarf the others.
        percentages = 100 * counts / np.maximum(1, counts.sum(axis=1, keepdims=True))
        ax.imshow(percentages, vmin=0, vmax=100, cmap="Blues")
        for row in range(4):
            for col in range(4):
                ax.text(col, row, f"{percentages[row, col]:.0f}%\n({counts[row, col]})",
                        ha="center", va="center", fontsize=8,
                        color="white" if percentages[row, col] > 55 else "#24333b")
        ax.set_xticks(range(4), CLASS_NAMES, rotation=25, ha="right")
        ax.set_yticks(range(4), CLASS_NAMES)
        ax.set_title(title)
        ax.set_xlabel("Predicted class")
        ax.set_ylabel("Target class")
    save_figure(figure, output, "confusion")

    # Always show the first mixed-condition stream, never a selected success.
    stream = streams[0]
    stop = min(240, len(stream.levels))
    categorical = {value: i for i, value in enumerate(CLASS_IDS)}
    figure, axes = plt.subplots(7, 1, figsize=(12, 12), sharex=True,
                               height_ratios=[1, 1, 1, 1, 1, 1, 2.3], layout="constrained")
    axes[0].step(range(stop), stream.levels[:stop], where="post", color="#24333b")
    axes[0].set_ylabel("Input")
    axes[0].set_title(f"First mixed test stream · seed {stream.seed} · dots are emitted events")
    axes[1].step(range(stop), [categorical[x] for x in stream.targets[:stop]], where="post",
                 color="#24333b")
    axes[1].set_ylabel("Target")
    for ax, (method, title), color in zip(axes[2:6], METHODS.items(), COLORS):
        prediction = traces[method]["predictions"][0][:stop]
        ax.step(range(stop), [categorical[x] for x in prediction], where="post", color=color)
        events = [event for event in traces[method]["events"][0] if event["emit_tick"] < stop]
        ax.scatter([event["emit_tick"] for event in events],
                   [categorical[event["class_id"]] for event in events], s=17, color=color)
        ax.set_ylabel(title.replace(" / ", "\n"))
    for ax in axes[1:6]:
        ax.set_yticks(range(4), ["SL", "LS", "bg", "?"])
        ax.set_ylim(-.3, 3.3)
    for ax in axes[:6]:
        for window in stream.windows:
            if window["start"] < stop:
                ax.axvspan(window["start"], min(stop, window["end"]), color="#b6cbd2", alpha=.25)
        ax.grid(axis="x", alpha=.15)
    axes[6].imshow(states[0][:stop].T, aspect="auto", interpolation="nearest",
                   origin="lower", cmap="coolwarm", vmin=-32, vmax=31,
                   extent=[0, stop, -.5, states[0].shape[1] - .5])
    axes[6].set_ylabel("Reservoir node\n−32 blue / +31 red")
    axes[6].set_xlabel("Receiver tick (no hardware clock frequency assumed)")
    axes[6].set_xlim(0, stop)
    save_figure(figure, output, "trace")

    rows = []
    for method, title in METHODS.items():
        entry = aggregate[method]
        latency = entry["median_latency_ticks"]
        rows.append(f"<tr><th>{escape(title)}</th>"
                    f"<td>{entry['event_f1']:.1%}</td>"
                    f"<td>{entry['balanced_accuracy']:.1%}</td>"
                    f"<td>{entry['unknown_recall']:.1%}</td>"
                    f"<td>{entry['false_events_per_1000_ticks']:.2f}</td>"
                    f"<td>{latency if latency is not None else '—'}</td></tr>")

    def embedded_plot(name, alt):
        # Put the image bytes in the HTML so the report's plots travel with the file.
        data = base64.b64encode((output / f"{name}.png").read_bytes()).decode()
        return f'<img alt="{escape(alt)}" src="data:image/png;base64,{data}">'

    settings = {name: {"ridge": entry.get("ridge"),
                       "hold_ticks": entry.get("receiver", entry)["hold_ticks"],
                       "decision": entry["receiver"]["decision"] if "receiver" in entry
                       else {"tolerance": entry["tolerance"]}}
                for name, entry in result["selected"].items()}
    diagnostics = result["training_state_diagnostics"]
    diagnostic_note = (
        "All training samples have the same binary fingerprint. The one-bit readouts cannot "
        "distinguish the classes in this representation; rejecting every sample is not successful recognition."
        if diagnostics["distinct_binary_fingerprints"] == 1 else
        "Check whether the available fingerprints separate the desired classes; variation alone does not guarantee recognition."
    )
    selection = result.get("reservoir_selection")
    search_note = "No reservoir search was performed."
    search_details = ""
    if selection:
        search_note = (f"Selected {escape(selection['selected_candidate'])} from "
                       f"{len(selection['candidates'])} candidates using training and validation only.")
        candidate_rows = []
        for candidate in selection["candidates"]:
            validation_f1 = (f"{candidate['selection_key'][0]:.1%}"
                             if candidate["selection_key"] is not None else "—")
            status = "; ".join(candidate["rejection_reasons"]) or "evaluated"
            if candidate["name"] == selection["selected_candidate"]:
                status = "selected"
            candidate_rows.append(
                f"<tr><th>{escape(candidate['name'])}</th>"
                f"<td>{candidate['training']['saturated_state_fraction']:.1%}</td>"
                f"<td>{candidate['training']['varying_sign_bits']}</td>"
                f"<td>{candidate['initial_state']['maximum_tail_gap']}</td>"
                f"<td>{validation_f1}</td><td>{escape(status)}</td></tr>")
        search_details = (
            '<section><h2>Reservoir selection</h2><p>' + search_note + '</p>'
            '<p>Candidates are screened for sign-bit variation, clipping and residual initial-state '
            'dependence. Passing candidates are ranked by the mean validation event F1 of Hamming '
            'and full-state linear readouts. These are finite experimental checks, not formal guarantees.</p>'
            '<div class="table"><table><tr><th>Candidate</th><th>Saturation</th><th>Varying bits</th>'
            '<th>Residual gap</th><th>Mean validation F1</th><th>Status</th></tr>'
            + ''.join(candidate_rows) + '</table></div><p>Full audit: '
            '<a href="selection.json">selection.json</a>.</p></section>')
    html = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reservoir readout comparison</title>
<style>
body{{margin:0;background:#f3f5f4;color:#24333b;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1150px;margin:auto;padding:36px 24px}}h1{{font-size:34px;line-height:1.2}}
h2{{margin-top:30px}}.tag{{color:#237c79;font-weight:700;letter-spacing:.08em;font-size:12px}}
section{{background:white;padding:24px;margin:20px 0;border-radius:12px;border:1px solid #dce4e4}}
img{{width:100%;height:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}
td,th{{padding:10px;text-align:left;border-bottom:1px solid #e3e9e9}}.table{{overflow-x:auto}}
pre{{overflow:auto;background:#f3f5f4;padding:16px}}a{{color:#176b77}}
.note{{border-left:4px solid #c15e30;padding-left:16px}}li{{margin:6px 0}}
</style><main>
<div class="tag">TEMPORAL PROTOCOL MACHINE / PYTHON STUDY</div>
<h1>What can the same reservoir recognize?</h1>
<p>One integer reservoir, three readouts, and a conventional pulse-timing reference.
All model settings are frozen before the test streams are generated.</p>
<p class="note">This compares Hamming and ESN-style linear <strong>readouts</strong> on the project's
shared integer reservoir. It is not a comparison of a spiking LSM against a separate tanh ESN.
The linear coefficients are floating point and have not been mapped to hardware.</p>
<section><h2>Held-out results</h2>
<p>{result['test_streams']} independent test streams, {result['test_patterns']} patterns,
reservoir seed {result['reservoir_seed']}. {search_note}</p>
<p class="note">{diagnostic_note}</p>
<div class="table"><table><tr><th>Method</th><th>Event F1</th><th>Balanced tick accuracy</th>
<th>Unknown recall</th><th>False events / 1k ticks</th><th>Median latency</th></tr>
{''.join(rows)}</table></div>
{embedded_plot('comparison', 'Accuracy and event detection across clean, jittered and corrupted signals')}
<p>Event F1 combines precision and recall for short–long and long–short detections. Each expected
pattern can match only one event emitted in the six ticks starting at its final falling edge.
Extra, early, late and wrong-class events count as false detections. Median latency is in ticks
and includes successful matches only. Balanced accuracy averages recall across all four targets,
so background cannot dominate it. Unknown recall measures class 7 on unknown target ticks.</p>
</section>{search_details}<section><h2>Where classifications go wrong</h2>
{embedded_plot('confusion', 'Confusion matrices with row percentages and sample counts')}
<p>Rows are the intended class; columns are the predicted class before stabilization.</p>
<p><strong>Training-state diagnostic:</strong> {diagnostics['varying_sign_bits']} of 16 sign bits vary;
{diagnostics['distinct_binary_fingerprints']} distinct binary fingerprints;
{diagnostics['saturated_state_fraction']:.1%} of node samples are clipped at a state limit.
These diagnostics use training streams only.</p>
</section><section><h2>Watch one stream</h2>
{embedded_plot('trace', 'Input, desired labels, each readout, emitted events and reservoir node states')}
<p>SL = short–long, LS = long–short, bg = background, ? = unknown.
Shaded windows are the four ticks after a complete pattern. Dots show event emission times;
the saved events also carry the earlier start-of-class-run timestamp.</p>
</section><section><h2>What this experiment means</h2><ul>
<li>The task is two pulses: widths (3, 8) or (8, 3), with a three-tick gap. Unknown patterns
use (3, 3), (5, 5) or (8, 8). Background includes incomplete patterns.</li>
<li>Training uses ±1-tick duration variation and occasional sample flips; validation independently
selects ridge strength, acceptance thresholds and stabilization. Tests include clean inputs,
±2-tick duration variation, 2% sample flips, and both perturbations together.</li>
<li>Noise preserves intended labels. At severe jitter, known and unknown waveform distributions
can overlap, so some samples are intrinsically ambiguous.</li>
<li>Hamming versus linear/1-bit tests readout flexibility. Linear/1-bit versus linear/6-bit
tests the value of retaining node magnitudes. All use identical state histories.</li>
<li>State resets only at stream boundaries. The first 20 ticks establish startup context and
are excluded from scoring. This is not a proof that initial-state dependence has vanished.</li>
<li>The single-lane feature encoding, arithmetic choices and timing are experimental. There is
no synchronizer, hardware pipeline, finite FIFO, area measurement, protocol compliance result,
pass-through equivalence proof or completed G1 gate here.</li></ul>
<details><summary>Frozen settings</summary><pre>{escape(json.dumps(settings, indent=2))}</pre></details>
<p>Recorded checks: configuration reload reproduced states, decisions and events for the test
streams; both reservoir readouts and the conventional listener were recorded.</p>
<p>Artifacts: <a href="metrics.json">metrics and provenance</a> ·
<a href="config.json">loadable study settings</a> ·
<a href="traces.json.gz">all test samples, states, scores and events</a> ·
<a href="comparison.svg">exportable comparison figure</a></p>
</section></main></html>"""
    (output / "report.html").write_text(html)
