# Current findings

**Full multi-protocol physical shapes independently qualified: 2. The required two are established.**

Start with [QUALIFIED_SHAPES.md](QUALIFIED_SHAPES.md) for the frozen full-profile gates, demonstration weights and remaining seed failures. The readout-routing comparison and its costs are in [READOUT_ROUTING_COMPARISON.md](READOUT_ROUTING_COMPARISON.md).

A narrower physical result is independently confirmed: the64-node24→20→20 sparse→ring→ring graph with one aligned inter-layer route per node matches the sparse baseline on I2C and all SPI modes, across six seeds in float andQ3.12, while saving23.62% MACs and22.10% parameters. UART is absent from that confirmation. See [REPORT.md](REPORT.md) for frozen evidence and resource limits.

These UART candidates are exploratory checkpoint portfolios. All rows use the same enlarged8,864-group development suite. Different training recipes/exposures mean this is not a matched topology ranking or fresh proof. Pending replication seeds are marked explicitly.

| Candidate | Nonlinear units / stored states | MACs / parameters | Profile | Full development passes | Remaining seeds |
| --- | ---: | ---: | --- | ---: | --- |
| Sparse24 → ring16 → ring24, registered returns | 64 / 64 | 840 / 910 | uart_n | 3/6 | 71, 101, 131 |
| Sparse24 → ring16 → ring24, registered returns | 64 / 64 | 840 / 910 | uart_e | 3/6 | 47, 71, 131 |
| Sparse16 → ring16 → ring16 +16 nonlinear readout units | 64 / 48 | 1464 / 1534 | uart_n | 5/6 | 47 |
| Sparse16 → ring16 → ring16 +16 nonlinear readout units | 64 / 48 | 1464 / 1534 | uart_e | 5/6 | 47 |
| Plain48 control, first leak0.5 | 48 / 48 | 600 / 654 | uart_n | 3/6 | 11, 47, 71 |
| Plain48 control, first leak0.5 | 48 / 48 | 600 / 654 | uart_e | 2/6 | 11, 47, 71, 101 |
| First-layer-gated64 (48 states +16 gates) | 64 / 48 | 696 / 766 | uart_n | 6/6 | none |
| First-layer-gated64 (48 states +16 gates) | 64 / 48 | 696 / 766 | uart_e | 5/6 | 101 |
| Sparse16 + two ring16 branches + reduced16-unit readout | 64 / 48 | 1208 / 1278 | uart_n | 5/6 | 47 |
| Sparse16 + two ring16 branches + reduced16-unit readout | 64 / 48 | 1208 / 1278 | uart_e | 5/6 | 47 |

The primary graph already failed a properly audited fresh confirmation: only3/6 no-parity and1/6 parity seeds passed. That failure remains frozen. V3 adds independent startup cases and requires the same five seeds to pass both new fresh tests and the old failure corpus.

`dense_full_v3a` completed fresh/regression scoring; see its frozen joint qualification record.
`first_gate_full_v3a` completed fresh/regression scoring; see its frozen joint qualification record.
`first_gate_full_v3b` completed fresh/regression scoring; see its frozen joint qualification record.
`readout_cost_full_v3a` completed fresh/regression scoring; see its frozen joint qualification record.
`readout_cost_full_v3b` completed fresh/regression scoring; see its frozen joint qualification record.

Structural comparisons show that true rings can replace sparse layers for clocked reception at lower cost; registered routing and access to earlier layers matter at tight setup. UART also needs reliable internal phase and recovery. Frozen-state, extra-idle and layer-state interventions expose cold-state dependence in some seeds; changing output weights alone does not consistently repair it.

Matched cold-prefix training fixes one primary no-parity seed through state changes, while its parity counterpart worsens. Small trust-region output fitting closes four full training/development configurations, but other sources fail larger independent-start training pools. Broader linear fitting can repair selected failure states and simultaneously destroy ordinary traffic; all such failed iterates are retained. These are learned-state/recipe diagnostics, not physical-capacity proofs.

The completed allocation comparison trades eight slow-ring states for eight conditional first-layer gates:64-state primary versus its56-state subgraph versus56states+8gates. All18 declared native/refinement fits completed; only one plain56 no-parity fit passes whole development. It did not establish the replicated meaningful threshold. GATE_ALLOCATION_COMPARISON.md retains the curves and failures.

The later readout comparison keeps the learned48-state backbone fixed and removes256 actual hidden-input edges. Retaining every fast-ring parent works better in the tested projection than retaining every first-layer parent at the same edge count. Paired conditional supervised fitting and balanced startup coverage are recorded separately; this is transfer/pruning evidence, not an equal-iteration or from-scratch efficiency claim.

See [STARTUP_REFINEMENT.md](STARTUP_REFINEMENT.md) for causal traces and paired curves, [LABEL_DIAGNOSTIC.md](LABEL_DIAGNOSTIC.md) for the raw-class versus event-pulse finding, [COVERAGE_V10.md](COVERAGE_V10.md) for balanced cold-start training, [REPRODUCE.md](REPRODUCE.md) for commands, and `runs/connectivity01/ACTIVE.md` for resumable work. Costs are modeled operations/storage, not silicon area or timing; clock_hz remains0.
