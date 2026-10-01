# How much fits

Filed announcement text. These are the contest's stated budgets, not a place-and-route result from this repo.

## How much fits?

An 6x4 allocation is 24 tiles. At approximately 200um × 150um per tile, that’s about 0.7 mm² of nominal tile area. As a rough estimate, budget for about 1K logic cells per tile. You may need to get creative to fit the functionality you want.

For instruction memory, SRAM can be more area-efficient than flip-flops. Tiny Tapeout has examples of SRAM running on this process node you can reference.

Run synthesis early, check the mapped cell area, and leave room for clock-tree buffers and routing. Then run the full place-and-route flow and check timing. A design that looks small enough after synthesis can still be difficult to route or too slow at your chosen clock frequency.
