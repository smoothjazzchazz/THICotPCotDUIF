# Reservoir study

Separate opt-in experiments: [mixed leaks](MIXED_LEAKS.md) and
[finite delay chains](DELAY_CHAINS.md). Their runners preserve this study's defaults.

Python study for G1. The question is whether one temporal shape sticks in the nodes well enough to load, decode, and re-emit, and whether the boring settings file can carry UART, SPI, and I2C as firmware. Rules are in [knowledgebase/doctrine.md](../../knowledgebase/doctrine.md) and [knowledgebase/phases.md](../../knowledgebase/phases.md).

Record both listeners. A worse UART result than the edge listener is data, not a failed study.

## Run the comparison

From the repository root, with Python 3.10 or newer:

```sh
python3 -m venv work/study/.venv
work/study/.venv/bin/python -m pip install -r work/study/requirements.txt
work/study/.venv/bin/python -B -m work.study.run_comparison
```

The environment is already installed in this checkout. Open
[`results/latest/report.html`](results/latest/report.html) after the run. Its plots
are embedded, so the HTML can be viewed offline. Adjacent PNG and SVG figures can
be opened or exported separately. Generated results and the environment are
ignored by Git.

VS Code is configured to use `work/study/.venv/bin/python`. If it already has a
different interpreter selected, run **Python: Select Interpreter** from the
Command Palette and choose that path to resolve NumPy and Matplotlib imports.

This first experiment compares **readouts of the same integer reservoir**:

| Method | Input representation | Fitting |
| --- | --- | --- |
| Hamming / 1-bit | Sign bit of every node | Per-class bitwise majority prototype |
| Linear / 1-bit | Exactly the same sign bits | Ridge regression |
| Linear / 6-bit | Full signed node values, divided by 32 | Ridge regression |
| Run-length reference | Durations of two pulses and their gap | Fixed templates; validation selects tolerance |

The linear rows use an **ESN-style training method**, not a separately implemented
tanh ESN. The integer reservoir is the project's LSM-like experimental model,
not a spiking-neuron simulation. Linear coefficients remain floating point; this
is not evidence that a ternary or other hardware readout would achieve the same
results. No RTL, released specification, gate decision, or clock rate is changed.

## Select a reservoir configuration

The original command above uses one fixed configuration. To select a shared
reservoir before fitting the final comparison, run:

```sh
work/study/.venv/bin/python -B -m work.study.run_comparison \
  --select-reservoir --seed 23 --candidate-count 3 \
  --data-seed 23 --test-seed 24 --output work/study/results/selected
```

Open [`results/selected/report.html`](results/selected/report.html). The report
includes a candidate table showing rejected configurations, validation results
and the selected configuration. `selection.json` preserves the full audit.
The original `results/latest/` comparison is left available for inspection.

The process is implemented in [`select_reservoir.py`](select_reservoir.py):

1. **`candidate_configs()` generates settings.** With the command above, seeds
   23, 24 and 25 each produce five candidates. Every candidate keeps 16 nodes,
   six-bit arithmetic, three recurrent tap slots and two feature tap slots.
   Within a seed, the source indices stay fixed; weights and leaks change.

   | Variant | Recurrent connections | Leak shifts and feature weights |
   | --- | --- | --- |
   | `original` | Original generated taps | Original settings |
   | `no_recurrence` | All recurrent weights zero | Original feature weights; leak shifts capped at 1 |
   | `forward_leak0` | At most one existing active tap from a lower-index node | All leak shifts 0; feature weights reduced to ±1 |
   | `forward_leak1` | Same restricted taps | All leak shifts 1; feature weights ±1 |
   | `forward_leak2` | Same restricted taps | All leak shifts 2; feature weights ±1 |

   A lower-index connection still uses the previous tick's state, so chains retain
   delayed information. This restriction avoids loops through multiple nodes;
   nonzero leak shifts still supply each node's own memory. Shift zero cancels
   that retention; larger shifts remove less state per tick. `no_recurrence`
   retains leak-based memory in nodes whose shift is nonzero.

2. **`state_diagnostics()` checks training states.** Reject a candidate if every
   binary fingerprint is identical or more than 50% of node samples hit a state
   limit. Startup ticks are excluded, as in readout fitting.

3. **`initial_state_diagnostics()` checks three finite input sequences.** Two
   reservoirs start at opposite state limits and receive identical features.
   The probes are 128 low samples, 128 high samples, and up to 128 samples from
   the first training stream. Over each probe's final 16 ticks, no corresponding
   node may differ by more than one integer count. This permits a small rounding
   residual; it does not guarantee equal sign bits, fading memory on all inputs,
   or enough memory for the task. These screening limits are experimental constants
   near the top of the selection module, not released hardware requirements.

4. **`train_and_select()` fits surviving candidates.** Each gets the same training
   streams, validation streams, ridge grid, decision thresholds and M choices.
   Actual validation detections determine whether its changing states are useful.

5. **`joint_validation_key()` chooses one configuration.** Maximize mean validation
   event F1 across Hamming and full-state linear readouts, giving each equal weight.
   Break ties with their mean balanced accuracy, then fewer false events. Exact
   ties keep the earlier candidate. The one-bit linear diagnostic and conventional
   reference do not influence this choice. All three reservoir readouts subsequently
   use the same selected configuration.

6. **The runner freezes configuration, then generates test streams.** The selector
   accepts only training and validation streams; it never receives test data.
   If every candidate is rejected, the runner saves `selection.json` and stops
   without silently choosing a failed candidate.

`--candidate-count` counts topology seeds, so three seeds mean fifteen candidates.
It is a bounded search, not a guarantee of the best possible reservoir. One
configuration is selected before inference; no topology changes while a stream
is running. Larger candidate searches also increase validation overfitting risk.

`--data-seed` controls training and validation streams. `--test-seed` can separately
reserve fresh test streams; if omitted it defaults to `--data-seed` for backward
compatibility. The first fixed study used test seed 23; the example above uses 24.
Do not compare scores from different test seeds as a controlled before/after result.

## Read the files in this order

1. [`signals.py`](signals.py): generate labeled pulse-order streams and run the
   causal conventional listener.
2. [`../model/reservoir_model.py`](../model/reservoir_model.py): features, integer
   reservoir, both readouts, rejection and stabilization.
3. [`comparison.py`](comparison.py): collect states, fit readouts, select settings,
   match events and compute metrics.
4. [`select_reservoir.py`](select_reservoir.py): generate candidate configurations,
   screen their dynamics, and choose a shared reservoir on validation data.
5. [`run_comparison.py`](run_comparison.py): keep the dataset splits separate,
   freeze configuration, evaluate, and save artifacts.
6. [`report.py`](report.py): plot the results and write the HTML report.

## The first task

Two known classes are short–long pulses (3 high ticks, 3 low, 8 high) and long–short
pulses (8 high, 3 low, 3 high). Unknown pairs have equal nominal widths of 3, 5 or
8 ticks. Every pair is followed by 12–20 low ticks. This is a synthetic line code,
not an implementation of UART, SPI, I2C or any other protocol standard.

Labels are causal: classes 0, 1 or 7 are requested for four ticks beginning at the
final falling edge. Everything else, including incomplete patterns, is background
(class 2). The receiver sees only pin samples, never labels or pattern boundaries.
Reservoir state continues across patterns and resets only between independent
streams. The first 20 ticks are excluded from training and measurement; they are
startup context, not a verified washout period.

Training streams vary durations by ±1 tick and flip each sample with probability
0.005. Validation uses independent streams with ±1 tick and probability 0.01.
Test conditions are clean, ±2-tick variation, 0.02 flip probability, and both.
Noise changes observations while preserving intended labels. Strong perturbations
can make different intended classes generate the same observed waveform.

## Training and evaluation rules

- Without `--select-reservoir`: reservoir seed 23; 12 training streams, 6 validation streams, and
  6 test streams in each of four conditions; 24 patterns per stream. Waveforms
  have a separate `--data-seed` (default 23).
- Prototypes and regression coefficients use training data only. Class 7 has no
  prototype: unknown training examples are all-zero regression targets. Known
  classes and background have one-hot targets. Ridge fitting balances total
  weight across the four target classes; its bias is unpenalized.
- Validation selects ridge strength from 0.0001, 0.01, 1; acceptance score/margin;
  and M from 1, 2, 3. Hamming score floors are -16, -12, -8, -6, -4, -2, 0 and
  margins 0, 1, 2. Linear floors are 0, .2, .4, .6, .8 and margins 0, .1, .2.
  The conventional listener selects summed run error tolerance from 0, 1, 2, 3,
  4, 6 and the same M choices.
- Selection maximizes validation event F1, then balanced tick accuracy, then
  minimizes false events. Configuration is written before generating test data.
  Optional reservoir selection runs the additional process above. Neither mode
  tunes settings using test results.
- Every readout gets the same states. All reported inference results use the
  saved settings. Reload checks compare actual streaming node states, decisions
  and events against the cached-state evaluation for every test stream.
- Event F1 covers the two known patterns. Match a correct-class event only if it
  emits in the six ticks beginning at the intended final falling edge. Match each
  expected pattern once; count duplicates, early, late or wrong events as false
  positives. The matching window is fixed across M. Event timestamps retain
  class-run onset, which can differ from the waveform label onset.
- Balanced tick accuracy averages recall over all four classes. Unknown recall
  alone is insufficient: predicting class 7 everywhere gets 100% unknown recall
  and zero known detections. Latency statistics describe matched events only.
- The trace figure always shows the first mixed-condition test stream. All other
  test traces are saved too; the figure is not selected for favorable behavior.

Artifacts in the output folder:

- `report.html`, `comparison.png/.svg`, `confusion.png/.svg`, `trace.png/.svg`
- `config.json`: explicit topology, weights, readouts, decision settings and M
- `selection.json` (selection runs): all candidate configurations, training
  diagnostics, rejection reasons, validation metrics, ranking keys and chosen ID
- `metrics.json`: results by condition and aggregate, validation results, seed
  splits, source hashes, dependency versions, config hash, selection audit and
  reload check status
- `traces.json.gz`: all test inputs, intended labels, node states, scores,
  candidate classes and timestamped events for all listeners

The report also shows training-only sign-bit diversity and saturation. With the
original unmodified seed-23 settings, all post-startup training samples share one sign fingerprint.
That is an observed failure of this representation/configuration, not evidence
that Hamming or reservoir computing fails generally. Fixed mode preserves that
baseline; selection mode records why it was rejected before looking at test data.

## Assessment of the selected run (2026-10-04)

**The selection process improved the experiment, but the current reservoir still
lacks the memory and rejection behavior needed for reliable signal recognition.**
The recommendation is to keep the linear readout as the main diagnostic tool and
focus next on what information survives in the reservoir. Adding nodes or training
data is premature.

This assessment describes the selection command above: topology seeds 23–25,
training/validation seed 23, test seed 24, and the default stream counts. Evidence
is in the local [report](results/selected/report.html),
[metrics](results/selected/metrics.json), and
[selection audit](results/selected/selection.json). These generated artifacts are
ignored by Git; this section records the observed result, not a guarantee for
future runs.

The architecture distinction matters. The experiment compares three readouts
attached to **one integer reservoir**. The LSM-like approach uses sign bits and
Hamming-distance prototypes; the ESN-style approach uses ridge-trained linear
weights. There is no separate conventional ESN reservoir or spiking LSM here.
The results evaluate representation and readout choices, but cannot establish
that ESNs outperform LSMs generally.

| Readout | Event F1 | Event precision | Unknown recall |
| --- | --- | --- | --- |
| Hamming, sign bits | 25.8% | 17.4% | 2.0% |
| Linear, sign bits | 39.5% | 25.9% | 73.4% |
| Linear, full states | 49.2% | 33.6% | 0.0% |
| Run-length reference | 75.0% | 94.5% | 87.4% |

Event F1 balances missed detections against false detections. The full-state
linear readout catches 92.2% of expected known events, but only about one-third
of its emitted detections are correct. Its zero unknown recall is particularly
concerning for a waveform translator expected to identify unfamiliar inputs.
Its higher F1 does not make it an acceptable receiver yet.

Moving from Hamming prototypes to learned linear weights improves F1 by 13.7
percentage points while preserving exactly the same sign-bit inputs. Preserving
node magnitudes adds another 9.8 points. This suggests limitations in both the
prototype classifier and the binary representation. Hamming remains a potentially
economical implementation target, but should not be the only way to judge
reservoir quality. Floating-point linear results still need quantization and
hardware-cost evaluation before informing a hardware readout choice.

The most revealing finding concerns memory. Selection chose
`seed24/forward_leak0`, with all 16 sign bits varying and no training-state
clipping. That resolves the original collapse. However, in
[`IntegerReservoir.step()`](../model/reservoir_model.py), shift zero cancels each
node's own previous value. The selected connections provide only short chains
of delayed features, with a longest path of three ticks.

A direct probe started each waveform from reset with 20 low samples, two high
pulses separated by three low samples, and four trailing low samples. Known
`(3, 8)` and unknown `(8, 8)` produced **identical node states at the final falling
edge and throughout the following three ticks**. The same happened for known
`(8, 3)` versus unknown `(3, 3)`. The readout receives identical snapshots when it
needs different decisions. More output-layer training cannot recover that missing
distinction.

This exposes a weakness in the selector: varying states, limited clipping, and
forgetting initialization do not establish useful task memory. Its finite probes
need an accompanying check that relevant earlier inputs remain distinguishable.

The ESN-style quadratic training objective remains useful because it makes fitting
a fixed representation straightforward. The code already solves ridge regression
directly; additional epochs would not help. Reservoir design remains a separate
problem, consistent with the distinction between memory, state expansion, and
readout fitting in [Lukoševičius's practical ESN guide](https://mantas.info/get-publication/?f=Practical_ESN.pdf).

The reference's lead is credible: it explicitly retains the pulse durations that
define this task. It is an appropriate benchmark. The
[project doctrine](../../knowledgebase/doctrine.md) nevertheless prioritizes
configurable temporal recognition over defeating conventional decoders. The
reservoir should earn its complexity through useful loaded behaviors and
dependable rejection.

Recommended next steps, not yet implemented:

1. **Repair memory first.** Add the paired-waveform check to candidate diagnostics.
   Explore controlled retention and longer delayed paths while keeping 16 nodes
   initially. Require the first pulse to remain distinguishable when the second
   ends.
2. **Make rejection part of selection.** Choose validation requirements for
   false-event rate and unknown recall before optimizing F1. The current objective
   permits a winner that never recognizes unknown inputs.
3. **Separate architecture experiments.** Add a conventional ESN backend behind
   the same input/state interface once the task is understood. Keep the integer
   model as the hardware-oriented candidate and compare under equal tuning budgets.
4. **Strengthen evaluation before scaling.** Repeat across independent training
   and test seeds, evaluating competitors on identical held-out streams. The
   earlier and selected reports used different test seeds, so they cannot
   establish a controlled improvement.

The next milestone is to **reliably distinguish clean known and unknown pulse
pairs, including pairs sharing the same final pulse, before increasing model size**.

## Extend the experiment

For the separate, opt-in mixed per-node leak experiment, see
[`MIXED_LEAKS.md`](MIXED_LEAKS.md). It keeps seed24's selected connections and
weights fixed, adds task-memory probes and stricter eligibility, and writes to a
new results directory. The commands, candidates and selection policy above are
unchanged.

For new waveform families, add a task adapter that produces `SignalStream` records from waveform
samples and independently defined target windows. Keep training and evaluation
separate. Multi-pin inputs, framing, real protocol coverage, hardware arithmetic,
and the pass-through proof are subsequent work, not hidden assumptions here.

For a separate reproducible run:

```sh
work/study/.venv/bin/python -B -m work.study.run_comparison \
  --seed 23 --data-seed 23 --output work/study/results/pulse-order-seed23
```

Use training/validation diagnostics to develop reservoir settings. Once test
results inform a change, those streams are development evidence: reserve fresh
test streams for the next final evaluation. A single seeded synthetic task is
not a general ranking of LSMs, ESNs or conventional decoders.

## Verification

```sh
work/study/.venv/bin/python -B -m unittest discover -s work/model -p 'test_*.py' -v
work/study/.venv/bin/python -B -m unittest discover -s work/study -p 'test_*.py' -v
python3 -B work/tools/check_template.py
```

The new tests were AI-authored. Hand-computed state transitions check simultaneous
updates, negative shifts, clipping and integer deadbands. Independent expected
events check stabilization, timestamp wrap and duplicate false positives. A clean
run-length reference must exactly reproduce the generator's labels. Serialization
and uncached replay check that the configurations being plotted can be loaded.
These checks do not constitute formal proof, RTL lockstep, protocol validation or
a completed project gate.

Selection tests additionally check reproducible candidates, unchanged tap indices,
persistent-feedback rejection, no fallback when all candidates fail, disjoint
training/validation seeds, and equal selection weight for the two primary readouts.
Their ranking test uses deliberately opposed validation scores to check that the
best full-state linear result alone cannot choose the reservoir.
