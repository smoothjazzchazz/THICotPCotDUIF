# Challenge

Filed announcement text.

We’re particularly interested in projects with unique functionality, as well as those that demonstrate novel approaches to design and verification methodologies! Winners will receive a fabricated copy of their chip, mounted on a dev boards, so they can test their design in real silicon.

## The challenge

Design an open-source, general-purpose protocol emulator ASIC.

Hardware protocols like UART, SPI, and I2C are simple enough that people routinely “bit-bang” them: toggle pins from software with careful timing instead of using a dedicated peripheral. A protocol emulator is a small chip built to do exactly that: a tiny CPU with an instruction set designed for reading pins, writing pins, counting cycles, and hitting timing precisely enough that you can implement a real protocol in firmware rather than in fixed logic. Something like that is a useful tool for hardware debugging and reverse engineering, which is a good part of what we do.

The hard part is flexibility. The goal isn’t to put a UART block, an SPI block, and an I2C block on one die and call it done. Your chip should be reprogrammable enough to support new protocols after fabrication, within its timing and I/O constraints. For inspiration, look at the PIO state machines on the RP2040 or the PRU cores on TI’s Sitara parts, and consider what you’d do differently.

Start with UART, SPI, and I2C.
Stretch goals include low-speed USB and 10Mbit Ethernet.
Other interesting protocols to consider: JTAG, SWD, PS/2, CAN bus
If you have access to an FPGA, consider using it to test your RTL before the ASIC flow.
Show us anything else your architecture makes possible that we haven’t thought of.
At Jane Street, we use Hardcaml to generate the RTL for our FPGA and ASIC designs. We are excited to see the languages and verification techniques you use, including formal methods, random constrained tests, AI-assisted verification, and more. As AI-assisted chip design becomes more common, we believe verification will be an extremely important aspect of the ASIC design flow going forwards.
