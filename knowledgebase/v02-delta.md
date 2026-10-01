# What changed from v0.2 to v0.3

Source: v0.3 section 0. Build the v0.3 column. The v0.2 column is not in scope.

- **Reservoir.** v0.2: optional coprocessor (`RES_MATCH` flag). v0.3: the receive-side symbol layer. All line-coded receive goes through it. A judge must not be able to delete it and still see a PIO clone.
- **Contexts.** v0.2: 2 to 4 barrel contexts plus a timed pin scheduler. v0.3: a single context. Autonomous receive and transmit symbol engines provide the concurrency and the exact pin timing. Barrel threading is out. Extra contexts are Tier 3.
- **Reservoir topology.** v0.2: programmable connectivity, time-multiplexed. v0.3: fixed sparse topology, programmable weights and leaks, fully parallel.
- **Matcher output.** v0.2: template slots plus `RES_MATCH` / `RES_SYNC`. v0.3: prototype classes (Hamming) produce class events with timestamps in an RX FIFO.
- **ALU.** v0.2: ALU-lite only. v0.3: adds a 16-bit programmable CRC/LFSR unit and a shift-tap. USB and CAN need CRCs.
- **Ethernet.** v0.2: 10 Mbit as a stretch. v0.3: simulation and analysis only (v0.3 section 6.4). Not a silicon target.
- **Program RAM.** v0.2: 256-word default. v0.3: 128 words default, 64 as fallback.
