# Provenance and evidence scope

The study follows the repository `AGENTS.md`, `knowledgebase/README.md`, doctrine,
authority, architecture and phase rules. v0.3 as amended by v0.31 remains the
released design. The new mechanisms are research alternatives only.

The initial audit read the existing broad-search report, shared signal/fitting/
resource helpers, polynomial memory and modular reservoir code. Their source
hashes are saved in [provenance.json](artifacts/provenance.json).

| Local origin | Reused idea | Suite implementation / difference |
|---|---|---|
| `../polynomial_memory/reservoir.py` | Signed input delay plus pair products | Two lanes, causal end snapshots, configurable stride and fresh per-family fits |
| `../shared/signals.py` | Continuous pulses with noisy samples and intended labels | Five new contracts, independent idle periods, midstream crops, malformed-prefix probes |
| `../shared/broad.py` | Balanced ridge readout, score/margin rejection, integer coefficients | Three classes at observable gates, shared selection grid, independent seed partitions |
| `../modular_reservoirs/reservoir.py` | Matched-total-node modules and multiple timescales | Suite-local sparse integer states and shifts; no float tanh dynamics |
| `../shared/resources.py` | Count storage and operations separately | Whole two-lane framing, support, fixed-width binary datapath and serial scheduling costs |

No existing research runner was invoked, no outside helper was modified, and no
outside project module was imported. Code here adapts local mechanisms rather
than copying a complete prior experiment. No external hardware or protocol source
was fetched. New run-threshold memory, paired feature groups and support checks
are local hypotheses; no new general reservoir-computing algorithm is claimed.

The existing study Python environment supplied NumPy 2.5.3 and Matplotlib 3.11.2.
Per-run manifests record the interpreter version, source hashes and thread count.
`run.sh` uses `-B`, one BLAS thread, and suite-local caches/temp files. During the
initial dependency-version probe, Matplotlib briefly created a fallback cache
under `/tmp`; it automatically removed it on interpreter exit. Every subsequent
invocation used the wrapper. No persistent outside-suite file changed.

The saved repository-boundary audit covers the research run before the user
authorized local commits. Its original HEAD and Git metadata are historical
evidence, preserved without rerunning or replacing the audit during commit staging.

Development artifacts retain their original hashes and results. A pre-freeze
scoring correction made transactions include all inter-group idle emissions;
event precision/recall and selection were unchanged. Resource accounting also
added explicit 16-bit study timestamps and estimated synchronizer storage before
freeze. Use confirmation's accounting for final costs, rather than silently mixing
early and final estimates. The binary token movement estimate was conservatively
112 bits in the frozen generic counter; the final hardware note distinguishes
its actual 80-bit packed binary payload. This did not change inference.

`artifacts/frozen/recipe.json` locks architecture and adaptation before transfer
training. `lock.json` locks fitted configurations, source hashes and inputs before
confirmation. The matching original inference sources are copied under
`artifacts/frozen/source/`. Later analysis/verification scripts do not alter those
sources or configurations. The cold reproduction is a separately launched copy
within this suite and confirms exact retraining/replay at the same seeds.

No named-protocol compliance, post-route timing, on-chip learning, measured area,
formal proof, RTL lockstep or project-gate completion is asserted.
