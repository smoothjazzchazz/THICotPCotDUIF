# Preserved harness failures

Before training, the first UART corpus audit (profile uart_n, seed 101, 16,384
minimum ticks) rejected group 3790–5021, expected bytes
`116,215,101,62,219,145,149,244`, decoded `116,57,70`. The draft generator added
independent duration jitter on every cell, creating a cumulative phase random
walk. That is a different condition from bounded one-tick edge jitter and can
exceed the sampling margin at the combined ±3% corner. The declared jitter
condition is now an independent ±1 tick perturbation of each nominal edge, with
no accumulated jitter. The audit rejection was before any fitting; no learned
trial or acceptance threshold was removed or altered. Random-walk jitter is
outside the declared envelope, not a passed condition.

The exhaustive all-byte audit then rejected UART 8E1 at the -3%/one-tick-jitter
corner (seed 173). A causal reference receiver sampling at offsets 8,24,...,168
can hit the next start when a rounded 170-tick frame loses two ticks to bounded
edge jitter. Sampling at 7,23,...,167 uses the earlier central tick and covers the
declared combined corner. This is a label-reference correction before training,
not a learned receiver repair. Initial generated data are retained in
`runs/preflight_rejected_center8/`; the main run is regenerated after this change.

During finalist continuation, full JSON history rewrites every epoch became an
unnecessary quadratic I/O cost in multi-thousand-epoch fits. Eight in-progress
fits were paused after preserving their last committed checkpoint, complete
history, and continuation controller. The original progress/logs and any
uncommitted checkpoint are retained under `runs/run01/maintenance_checkpoint_io/`.
Training resumes the exact weights, Adam moments, exposure count and block state;
only history storage changes to an append-only journal with JSON snapshots every
30 epochs. Worker count increases from eight to sixteen. No acceptance threshold
or training example changes. A zero-to-zero loss is explicitly not treated as a
2% loss decrease in the corrected continuation predicate.
