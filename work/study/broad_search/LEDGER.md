# Experiment ledger

Post-selection limitation check: the frozen winner was also evaluated on seven
unseen unknown pulse pairs with two idle lengths. This is development diagnosis,
not another confirmation attempt. It produced 83.9% unknown tick recall and two
false known events for `(12,3)`, so general open-set recognition is **rejected**
as an unsupported claim. No model settings changed afterward.
[Saved probe](../results/unseen-unknown-probe/20261005T012713.374377Z/probe.json).

All rows are saved, including failed and repeated configurations. Screening and
validation are development evidence; only the separately frozen confirmation
is new confirmation evidence. F1 values are not comparable across dataset groups.

## broad-screen / 20261005T011146.539052Z

[Saved records](../results/broad-screen/20261005T011146.539052Z/screen.json)

| Configuration / readout | F1 | P / R / unknown | Outcome and reason |
| --- | ---: | --- | --- |
| modular 8 sparse 31 | 37.4% | 33.9% / 41.7% / 41.7% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| modular 16 sparse 31 | 46.1% | 39.6% / 55.2% / 74.5% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| modular 32 sparse 31 | 56.5% | 50.8% / 63.5% / 48.4% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| modular 64 sparse 31 | 51.8% | 51.5% / 52.1% / 66.7% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| modular 128 sparse 31 | 67.0% | 62.7% / 71.9% / 76.0% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| modular 32 ring 31 | 87.7% | 83.2% / 92.7% / 96.4% | promising: passes this development screen; not confirmation |
| modular 32 local 31 | 57.3% | 52.1% / 63.5% / 59.4% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| modular 32 skip 31 | 59.8% | 59.2% / 60.4% / 85.9% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| modular 32 ring parallel 31 | 85.6% | 79.5% / 92.7% / 99.0% | rejected: P/R/unknown below .80 |
| modular 32 ring stacked 31 | 82.2% | 78.3% / 86.5% / 99.0% | rejected: P/R/unknown below .80 |
| modular 32 ring coupled 31 | 83.2% | 79.2% / 87.5% / 100.0% | rejected: P/R/unknown below .80 |
| modular 32 ring specialized 31 | 76.7% | 71.8% / 82.3% / 96.9% | rejected: P/R/unknown below .80 |
| polynomial 8 1 | 47.1% | 33.9% / 77.1% / 27.1% | rejected: nominal reset decisions, prefix/offset decisions, memory collision, P/R/unknown below .80 |
| polynomial 16 1 | 57.1% | 48.9% / 68.8% / 72.9% | rejected: nominal reset decisions, prefix/offset decisions, memory collision, P/R/unknown below .80 |
| polynomial 32 1 | 71.6% | 72.3% / 70.8% / 78.6% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| polynomial 64 1 | 70.7% | 73.9% / 67.7% / 77.1% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| polynomial 128 1 | 63.7% | 68.7% / 59.4% / 75.0% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| polynomial 16 2 | 86.3% | 84.2% / 88.5% / 80.2% | rejected: nominal reset decisions, prefix/offset decisions, memory collision |
| polynomial 24 2 | 96.9% | 95.9% / 97.9% / 97.9% | promising: passes this development screen; not confirmation |
| polynomial 32 2 | 96.9% | 95.0% / 99.0% / 96.9% | promising: passes this development screen; not confirmation |
| ca 64 ring 90 31 | 19.4% | 18.2% / 20.8% / 30.7% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| ca 64 chain 90 31 | 63.4% | 59.6% / 67.7% / 68.8% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| ca 64 ring 110 31 | 13.6% | 13.7% / 13.5% / 65.1% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| ca 64 chain 110 31 | 21.9% | 17.9% / 28.1% / 27.6% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| ca 64 ring 150 31 | 18.3% | 12.2% / 36.5% / 34.9% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| ca 64 chain 150 31 | 12.6% | 11.7% / 13.5% / 95.3% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| delay 8 0.6 0.5 | 65.7% | 59.8% / 72.9% / 52.1% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| delay 16 0.6 0.5 | 55.8% | 44.4% / 75.0% / 80.2% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| delay 32 0.6 0.5 | 69.6% | 72.7% / 66.7% / 76.6% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| delay 64 0.6 0.5 | 63.5% | 63.5% / 63.5% / 75.0% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| delay 32 0 0.5 | 72.5% | 72.2% / 72.9% / 79.7% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| delay 32 0.3 0.5 | 72.6% | 73.4% / 71.9% / 79.7% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| delay 32 0.9 0.5 | 62.0% | 59.6% / 64.6% / 90.1% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| delay 32 0.6 1.0 sin | 61.1% | 60.8% / 61.5% / 78.1% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |
| age_chain | 64.2% | 58.6% / 70.8% / 74.0% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80 |
| level_chain | 60.8% | 47.9% / 83.3% / 72.4% | rejected: nominal reset decisions, prefix/offset decisions, memory collision, P/R/unknown below .80 |
| seed24_forward_leak0 | 37.9% | 30.9% / 49.0% / 50.0% | rejected: nominal reset decisions, prefix/offset decisions, memory collision, P/R/unknown below .80 |
| cycle3210 | 81.9% | 81.4% / 82.3% / 77.1% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80 |

## broader-validation / 20261005T011251.428831Z

[Saved records](../results/broader-validation/20261005T011251.428831Z/validation.json)

| Configuration / readout | F1 | P / R / unknown | Outcome and reason |
| --- | ---: | --- | --- |
| polynomial 20 2 explicit=True | 86.5% | 94.2% / 79.9% / 93.9% | rejected: P/R/unknown below .80, jitter: event_recall 0.625000 < 0.65, mixed: event_recall 0.593750 < 0.65, aggregate: event_recall 0.799479 < 0.8 |
| polynomial 24 2 explicit=True | 87.3% | 96.5% / 79.7% / 94.7% | rejected: P/R/unknown below .80, mixed: event_recall 0.541667 < 0.65, aggregate: event_recall 0.796875 < 0.8 |
| polynomial 28 2 explicit=True | 82.6% | 84.9% / 80.5% / 94.0% | rejected: clean: event_precision 0.793388 < 0.95, clean: false-event limit, mixed: event_recall 0.562500 < 0.65 |
| polynomial 32 2 explicit=True | 85.1% | 88.9% / 81.5% / 93.8% | rejected: clean: event_precision 0.897196 < 0.95, clean: false-event limit, mixed: event_recall 0.593750 < 0.65 |
| polynomial 40 2 explicit=True | 86.7% | 97.1% / 78.4% / 92.6% | rejected: P/R/unknown below .80, jitter: event_recall 0.625000 < 0.65, mixed: event_recall 0.541667 < 0.65, aggregate: event_recall 0.783854 < 0.8 |
| polynomial 24 1 explicit=True | 65.0% | 58.5% / 73.2% / 83.1% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.607595 < 0.95, clean: unknown_recall 0.901042 < 0.95, clean: false-event limit, jitter: event_precision 0.528302 < 0.75, jitter: event_recall 0.583333 < 0.65, jitter: false-event limit, glitches: event_precision 0.646617 < 0.75, glitches: false-event limit, mixed: event_precision 0.518072 < 0.75, mixed: event_recall 0.447917 < 0.65, mixed: false-event limit, aggregate: event_precision 0.585417 < 0.8, aggregate: event_recall 0.731771 < 0.8, aggregate: false-event limit |
| polynomial 24 2 explicit=False | 87.3% | 96.5% / 79.7% / 94.7% | rejected: P/R/unknown below .80, mixed: event_recall 0.541667 < 0.65, aggregate: event_recall 0.796875 < 0.8 |
| modular 32 ring single 31 explicit=True | 83.8% | 88.0% / 79.9% / 95.8% | rejected: P/R/unknown below .80, mixed: event_recall 0.541667 < 0.65, aggregate: event_recall 0.799479 < 0.8 |
| modular 32 ring parallel 31 explicit=True | 83.9% | 82.2% / 85.7% / 94.9% | rejected: glitches: false-event limit, mixed: event_precision 0.656863 < 0.75, mixed: false-event limit, aggregate: false-event limit |
| modular 32 ring stacked 31 explicit=True | 83.4% | 85.1% / 81.8% / 96.5% | rejected: mixed: event_precision 0.701149 < 0.75, mixed: event_recall 0.635417 < 0.65, mixed: false-event limit |
| modular 32 ring coupled 31 explicit=True | 82.9% | 82.6% / 83.1% / 94.3% | rejected: glitches: false-event limit, mixed: event_precision 0.684783 < 0.75, mixed: false-event limit |
| modular 32 ring specialized 31 explicit=True | 78.5% | 77.6% / 79.4% / 94.9% | rejected: P/R/unknown below .80, clean: event_precision 0.857143 < 0.95, clean: false-event limit, jitter: event_recall 0.625000 < 0.65, glitches: event_precision 0.740157 < 0.75, glitches: false-event limit, mixed: event_precision 0.687500 < 0.75, mixed: event_recall 0.572917 < 0.65, aggregate: event_precision 0.776081 < 0.8, aggregate: event_recall 0.794271 < 0.8, aggregate: false-event limit |
| modular 32 ring single 32 explicit=True | 69.9% | 61.3% / 81.5% / 88.8% | rejected: P/R/unknown below .80, clean: event_precision 0.607595 < 0.95, clean: false-event limit, jitter: event_precision 0.650000 < 0.75, jitter: false-event limit, glitches: event_precision 0.627451 < 0.75, glitches: false-event limit, mixed: event_precision 0.560000 < 0.75, mixed: event_recall 0.583333 < 0.65, mixed: false-event limit, aggregate: event_precision 0.612524 < 0.8, aggregate: false-event limit |
| modular 32 ring parallel 32 explicit=True | 74.5% | 66.6% / 84.6% / 95.2% | rejected: prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.671329 < 0.95, clean: false-event limit, jitter: event_precision 0.740000 < 0.75, jitter: false-event limit, glitches: event_precision 0.650685 < 0.75, glitches: false-event limit, mixed: event_precision 0.606061 < 0.75, mixed: event_recall 0.625000 < 0.65, mixed: false-event limit, aggregate: event_precision 0.665984 < 0.8, aggregate: false-event limit |
| modular 32 ring stacked 32 explicit=True | 75.6% | 70.2% / 81.8% / 95.7% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.774194 < 0.95, clean: false-event limit, jitter: event_precision 0.728261 < 0.75, glitches: event_precision 0.691729 < 0.75, glitches: false-event limit, mixed: event_precision 0.602041 < 0.75, mixed: event_recall 0.614583 < 0.65, mixed: false-event limit, aggregate: event_precision 0.702461 < 0.8, aggregate: false-event limit |
| modular 32 ring coupled 32 explicit=True | 74.5% | 67.1% / 83.9% / 95.6% | rejected: prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.671329 < 0.95, clean: false-event limit, glitches: event_precision 0.650685 < 0.75, glitches: false-event limit, mixed: event_precision 0.614583 < 0.75, mixed: event_recall 0.614583 < 0.65, mixed: false-event limit, aggregate: event_precision 0.670833 < 0.8, aggregate: false-event limit |
| modular 32 ring specialized 32 explicit=True | 78.9% | 82.8% / 75.3% / 95.3% | rejected: prefix/offset decisions, P/R/unknown below .80, clean: false-event limit, jitter: event_recall 0.562500 < 0.65, glitches: false-event limit, mixed: event_precision 0.676471 < 0.75, mixed: event_recall 0.479167 < 0.65, aggregate: event_recall 0.752604 < 0.8 |
| modular 32 ring single 33 explicit=True | 68.5% | 60.8% / 78.4% / 94.5% | rejected: P/R/unknown below .80, clean: event_precision 0.607595 < 0.95, clean: false-event limit, jitter: event_precision 0.614583 < 0.75, jitter: event_recall 0.614583 < 0.65, jitter: false-event limit, glitches: event_precision 0.626667 < 0.75, glitches: false-event limit, mixed: event_precision 0.571429 < 0.75, mixed: event_recall 0.541667 < 0.65, mixed: false-event limit, aggregate: event_precision 0.608081 < 0.8, aggregate: event_recall 0.783854 < 0.8, aggregate: false-event limit |
| modular 32 ring parallel 33 explicit=True | 82.3% | 84.2% / 80.5% / 94.7% | rejected: jitter: event_precision 0.744186 < 0.75, mixed: event_precision 0.708861 < 0.75, mixed: event_recall 0.583333 < 0.65 |
| modular 32 ring stacked 33 explicit=True | 78.9% | 79.9% / 77.9% / 93.9% | rejected: prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.905660 < 0.95, clean: false-event limit, jitter: event_precision 0.734940 < 0.75, jitter: event_recall 0.635417 < 0.65, mixed: event_precision 0.739130 < 0.75, mixed: event_recall 0.531250 < 0.65, aggregate: event_precision 0.799465 < 0.8, aggregate: event_recall 0.778646 < 0.8, aggregate: false-event limit |
| modular 32 ring coupled 33 explicit=True | 82.1% | 85.2% / 79.2% / 94.9% | rejected: P/R/unknown below .80, jitter: event_recall 0.635417 < 0.65, mixed: event_precision 0.710526 < 0.75, mixed: event_recall 0.562500 < 0.65, aggregate: event_recall 0.791667 < 0.8 |
| modular 32 ring specialized 33 explicit=True | 81.5% | 82.8% / 80.2% / 94.4% | rejected: nominal reset decisions, jitter: event_recall 0.625000 < 0.65, mixed: event_precision 0.709302 < 0.75, mixed: event_recall 0.635417 < 0.65 |
| modular 32 ring 31 4 explicit=True | 77.4% | 81.7% / 73.4% / 84.5% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, memory collision, P/R/unknown below .80, jitter: event_precision 0.712121 < 0.75, jitter: event_recall 0.489583 < 0.65, mixed: event_precision 0.657895 < 0.75, mixed: event_recall 0.520833 < 0.65, mixed: false-event limit, aggregate: event_recall 0.734375 < 0.8 |
| modular 32 ring 31 6 explicit=True | 82.3% | 87.2% / 77.9% / 91.1% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80, jitter: event_recall 0.572917 < 0.65, mixed: event_precision 0.743243 < 0.75, mixed: event_recall 0.572917 < 0.65, aggregate: event_recall 0.778646 < 0.8 |
| modular 32 ring 31 8 explicit=True | 80.8% | 84.0% / 77.9% / 95.2% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80, jitter: event_recall 0.593750 < 0.65, mixed: event_precision 0.697368 < 0.75, mixed: event_recall 0.552083 < 0.65, aggregate: event_recall 0.778646 < 0.8 |
| modular 32 ring 31 0.2 explicit=True | 82.4% | 83.2% / 81.5% / 96.1% | rejected: mixed: event_precision 0.681818 < 0.75, mixed: event_recall 0.625000 < 0.65, mixed: false-event limit |
| modular 32 ring 31 0.8 explicit=True | 59.8% | 50.8% / 72.7% / 51.7% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.513369 < 0.95, clean: unknown_recall 0.468750 < 0.95, clean: false-event limit, jitter: event_precision 0.530612 < 0.75, jitter: event_recall 0.541667 < 0.65, jitter: unknown_recall 0.588542 < 0.65, jitter: false-event limit, glitches: event_precision 0.508287 < 0.75, glitches: unknown_recall 0.343750 < 0.65, glitches: false-event limit, mixed: event_precision 0.469880 < 0.75, mixed: event_recall 0.406250 < 0.65, mixed: false-event limit, aggregate: event_precision 0.508197 < 0.8, aggregate: event_recall 0.726562 < 0.8, aggregate: unknown_recall 0.516927 < 0.8, aggregate: false-event limit |
| modular 32 ring 31 clip explicit=True | 83.4% | 85.7% / 81.2% / 93.2% | rejected: mixed: event_precision 0.686747 < 0.75, mixed: event_recall 0.593750 < 0.65, mixed: false-event limit |

## jitter-training / 20261005T011420.632152Z

[Saved records](../results/jitter-training/20261005T011420.632152Z/validation.json)

| Configuration / readout | F1 | P / R / unknown | Outcome and reason |
| --- | ---: | --- | --- |
| polynomial 20 2 aug=False explicit=True | 86.2% | 89.5% / 83.1% / 91.9% | promising: passes this development screen; not confirmation |
| polynomial 20 2 aug=True explicit=True | 89.0% | 91.7% / 86.5% / 94.2% | promising: passes this development screen; not confirmation |
| polynomial 24 2 aug=False explicit=True | 87.7% | 93.3% / 82.8% / 90.3% | promising: passes this development screen; not confirmation |
| polynomial 24 2 aug=True explicit=True | 89.4% | 91.2% / 87.8% / 93.8% | promising: passes this development screen; not confirmation |
| polynomial 28 2 aug=False explicit=True | 88.1% | 92.2% / 84.4% / 91.9% | promising: passes this development screen; not confirmation |
| polynomial 28 2 aug=True explicit=True | 88.9% | 94.6% / 83.9% / 93.1% | promising: passes this development screen; not confirmation |
| polynomial 32 2 aug=False explicit=True | 86.9% | 95.1% / 80.1% / 92.4% | rejected: prefix/offset decisions, jitter: event_recall 0.614583 < 0.65, mixed: event_recall 0.625000 < 0.65 |
| polynomial 32 2 aug=True explicit=True | 86.1% | 88.9% / 83.5% / 93.6% | rejected: clean: event_precision 0.927536 < 0.95, clean: false-event limit, mixed: event_recall 0.645833 < 0.65 |
| polynomial 24 2 aug=True explicit=False | 88.9% | 94.8% / 83.6% / 93.2% | promising: passes this development screen; not confirmation |

## quantized-memory / 20261005T011611.751866Z

[Saved records](../results/quantized-memory/20261005T011611.751866Z/validation.json)

| Configuration / readout | F1 | P / R / unknown | Outcome and reason |
| --- | ---: | --- | --- |
| polynomial 20 2 readout=None | 89.9% | 91.4% / 88.5% / 95.1% | promising: passes this development screen; not confirmation |
| polynomial 20 2 readout=8 | 90.0% | 91.2% / 88.8% / 95.1% | promising: passes this development screen; not confirmation |
| polynomial 20 2 readout=10 | 89.9% | 91.2% / 88.6% / 95.1% | promising: passes this development screen; not confirmation |
| polynomial 20 2 readout=12 | 89.9% | 91.3% / 88.5% / 95.1% | promising: passes this development screen; not confirmation |
| polynomial 20 2 readout=16 | 89.9% | 91.4% / 88.5% / 95.1% | promising: passes this development screen; not confirmation |
| polynomial 24 2 readout=None | 90.3% | 91.4% / 89.3% / 94.8% | promising: passes this development screen; not confirmation |
| polynomial 24 2 readout=8 | 90.1% | 91.3% / 88.9% / 94.9% | promising: passes this development screen; not confirmation |
| polynomial 24 2 readout=10 | 90.6% | 91.6% / 89.6% / 95.0% | promising: passes this development screen; not confirmation |
| polynomial 24 2 readout=12 | 90.3% | 91.4% / 89.3% / 94.9% | promising: passes this development screen; not confirmation |
| polynomial 24 2 readout=16 | 90.3% | 91.4% / 89.3% / 94.8% | promising: passes this development screen; not confirmation |
| age_chain | 67.2% | 64.4% / 70.4% / 75.9% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.854283 < 0.95, clean: unknown_recall 0.847656 < 0.95, clean: false-event limit, jitter: event_precision 0.579470 < 0.75, jitter: event_recall 0.455729 < 0.65, jitter: false-event limit, glitches: event_precision 0.688911 < 0.75, glitches: false-event limit, mixed: event_precision 0.408602 < 0.75, mixed: event_recall 0.445312 < 0.65, mixed: false-event limit, aggregate: event_precision 0.643644 < 0.8, aggregate: event_recall 0.703776 < 0.8, aggregate: unknown_recall 0.758952 < 0.8, aggregate: false-event limit |
| level_chain | 70.9% | 63.3% / 80.4% / 71.2% | rejected: nominal reset decisions, prefix/offset decisions, memory collision, P/R/unknown below .80, clean: event_precision 0.745631 < 0.95, clean: unknown_recall 0.740885 < 0.95, clean: false-event limit, jitter: event_precision 0.520548 < 0.75, jitter: event_recall 0.643229 < 0.65, jitter: false-event limit, glitches: event_precision 0.716256 < 0.75, glitches: false-event limit, mixed: event_precision 0.530837 < 0.75, mixed: event_recall 0.627604 < 0.65, mixed: false-event limit, aggregate: event_precision 0.633265 < 0.8, aggregate: unknown_recall 0.712402 < 0.8, aggregate: false-event limit |
| seed24_forward_leak0 | 43.7% | 29.8% / 82.0% / 78.4% | rejected: nominal reset decisions, prefix/offset decisions, memory collision, P/R/unknown below .80, clean: event_precision 0.371014 < 0.95, clean: unknown_recall 0.826172 < 0.95, clean: false-event limit, jitter: event_precision 0.331069 < 0.75, jitter: false-event limit, glitches: event_precision 0.270164 < 0.75, glitches: false-event limit, mixed: event_precision 0.238074 < 0.75, mixed: false-event limit, aggregate: event_precision 0.298200 < 0.8, aggregate: unknown_recall 0.784342 < 0.8, aggregate: false-event limit |
| cycle3210 | 78.2% | 78.1% / 78.4% / 67.9% | rejected: nominal reset decisions, prefix/offset decisions, initial-state residue, P/R/unknown below .80, clean: event_precision 0.854283 < 0.95, clean: unknown_recall 0.744141 < 0.95, clean: false-event limit, jitter: unknown_recall 0.636068 < 0.65, glitches: event_precision 0.745293 < 0.75, glitches: false-event limit, mixed: event_precision 0.671620 < 0.75, mixed: event_recall 0.588542 < 0.65, mixed: unknown_recall 0.594401 < 0.65, mixed: false-event limit, aggregate: event_precision 0.780551 < 0.8, aggregate: event_recall 0.783854 < 0.8, aggregate: unknown_recall 0.678548 < 0.8, aggregate: false-event limit |

## memory-ablations / 20261005T011727.898570Z

[Saved records](../results/memory-ablations/20261005T011727.898570Z/validation.json)

| Configuration / readout | F1 | P / R / unknown | Outcome and reason |
| --- | ---: | --- | --- |
| polynomial 20 1 explicit=True | 63.2% | 51.6% / 81.5% / 73.6% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80, clean: event_precision 0.543140 < 0.95, clean: unknown_recall 0.847656 < 0.95, clean: false-event limit, jitter: event_precision 0.460036 < 0.75, jitter: unknown_recall 0.647786 < 0.65, jitter: false-event limit, glitches: event_precision 0.579278 < 0.75, glitches: false-event limit, mixed: event_precision 0.460211 < 0.75, mixed: event_recall 0.625000 < 0.65, mixed: false-event limit, aggregate: event_precision 0.515545 < 0.8, aggregate: unknown_recall 0.736491 < 0.8, aggregate: false-event limit |
| polynomial 20 2 explicit=False | 90.2% | 92.1% / 88.4% / 95.0% | promising: passes this development screen; not confirmation |
| polynomial 20 2 age explicit=True | 71.8% | 71.3% / 72.4% / 88.8% | rejected: P/R/unknown below .80, clean: event_precision 0.854283 < 0.95, clean: false-event limit, jitter: event_precision 0.632588 < 0.75, jitter: event_recall 0.515625 < 0.65, jitter: false-event limit, mixed: event_precision 0.521678 < 0.75, mixed: event_recall 0.485677 < 0.65, mixed: false-event limit, aggregate: event_precision 0.712821 < 0.8, aggregate: event_recall 0.723958 < 0.8, aggregate: false-event limit |
| polynomial 20 2 readout=4 | 50.7% | 91.7% / 35.1% / 96.6% | rejected: nominal reset decisions, prefix/offset decisions, P/R/unknown below .80, clean: event_recall 0.500000 < 0.95, jitter: event_recall 0.205729 < 0.65, glitches: event_recall 0.485677 < 0.65, mixed: event_recall 0.210938 < 0.65, aggregate: event_recall 0.350586 < 0.8 |
| polynomial 20 2 readout=6 | 88.8% | 91.3% / 86.4% / 95.1% | promising: passes this development screen; not confirmation |

## Confirmation attempts

| Attempt | Outcome | Evidence |
| --- | --- | --- |
| 1 | confirmed improvement | [Saved status](../results/broad-confirmation/20261005T012024.954575Z/status.json) |
