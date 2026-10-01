# JTAG and SWD

status: missing

Blocks treating JTAG or SWD as implemented. v0.3 says both are expressible by the core alone — TCK generation and shift — which under v0.31 means the degenerate symbol-layer configuration plus TX-table symbols. No trained-reservoir role.

Required:

- Which of JTAG or SWD, if either, the Tier 1 programs will actually include.
- The shift and TMS or SWDIO sequence that program will follow, from a source named in this file.

Do not add a TCK rate here. The figure in v0.3 section 6.3 is an estimate.
