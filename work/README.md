# Work tree

Code that is not the Tiny Tapeout template lives here. Synthesizable RTL does not. New Verilog files go in `src/` and are added, in the same change, to `info.yaml` `source_files` and to `PROJECT_SOURCES` in `test/Makefile`.

Do not rename `src/project.v` or `tt_um_example`.

- [model/](model/) — simple waveform/controller/transmitter scaffold; not yet the complete golden model or ISA reference
- [study/](study/) — architecture experiments and historical study documentation; see [experimental scope](../knowledgebase/experiments.md)
- [fw/](fw/) — UART, SPI, and I2C programs
- [formal/](formal/) — properties named in v0.3 section 7
- [verification/](verification/) — lockstep and protocol test logs

Gates and pass rules: [knowledgebase/phases.md](../knowledgebase/phases.md).
