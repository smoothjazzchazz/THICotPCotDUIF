# Paired full-profile readout cost result

Float resource/recovery threshold: **met**. The reduced graph removes 256 physical connections, saving 17.49% of MACs and 16.69% of learned parameters.

Both architectures and all 84 protocol/seed configurations were frozen before fresh family 541000000 (`readout_cost_full_v3b`). Every seed is compared on identical waveforms. Previously observed suites are separately scored regressions. The same paired seeds must meet the comparison in both scopes; no failed seed is replaced.

| Arithmetic | UART 8N1 | UART 8E1 | I2C | SPI0 | SPI1 | SPI2 | SPI3 | Threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| float | 5/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | met |
| quantized | 5/6 | 4/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | not met |

Comparison gates are unchanged: within one percentage point on every condition, at least 95% recovery, no worse boundary/rejection counts, and at least 15% lower MACs and parameters in at least five paired seeds. Full hero qualification is stricter and reported separately in QUALIFIED_SHAPES.md.

All per-message paired outcomes, per-condition differences and empirical 95% bootstrap intervals are retained in [paired_readout_cost_result.json](runs/connectivity01/paired_readout_cost_result.json). A zero-width empirical interval for all-success outcomes does not establish zero population failure probability. Results cover the declared generated distributions, not all possible waveforms.

The two shapes share the learned 48-state recurrent backbone within each seed/profile. The reduced head receives the same training waveforms and representative state bank, with the same conditional continuation rule as the intact control. Their recorded optimization exposure differs; this establishes a reproducible pruning/transfer result, not a from-scratch training-efficiency ranking. READOUT_ROUTING_COMPARISON.md retains all intermediate failures and curves.

Including common leak blends gives 16.41% fewer modeled multiplies; the numeric storage subtotal falls 4.43%. The common feature extraction, event interface, assembler, activation table and scheduling costs are unchanged. No routed silicon area or frequency is measured.
