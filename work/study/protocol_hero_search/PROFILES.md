# Sources, interface, and test assumptions

Read the project's [source register](../../../knowledgebase/protocols/sources/README.md)
and [previous-model audit](../../../knowledgebase/protocols/model-audit.md).
Previous emitters are useful references, but are not reused: the old UART emitter
lacked independent parity errors and break coverage; its generator-center labels
also vary with hidden timing. Old scorers tolerate shifted events and do not
constitute this study's exact-boundary gate. The isolated pulse demo cannot score
continuous messages. New generators and independent offline decoders are audited.

- UART 8N1/8E1: TI SPRUGP1 framing and error definitions, as filed in the project
  [UART guide](../../../knowledgebase/protocols/uart.md). Lane 0 is RX, unused lanes
  high. Nominal 16 sampled ticks per bit. Start, data and stop events are trained
  at offsets 7,23,... from a visible falling start edge (the earlier of the two
  central sample ticks in a 16-tick cell). Hidden
  jittered cell centers never enter inference. Even parity is checked by assembly.
  Frame acceptance is per character; message grouping exists only in scoring.
- I2C: NXP UM10204 rev.7.0 §§3.1 and 6.1, filed in the
  [I2C guide](../../../knowledgebase/protocols/i2c.md). Lanes SCL/SDA/high;
  single controller, 7-bit address/direction, ninth-clock ACK/NACK. Bits are emitted
  on the *falling* edge ending a completed high clock phase, so the preparatory
  rise before STOP/repeated START cannot become a spurious payload bit. This is a
  declared decision delay, not the external bus's sampling specification. START
  and STOP cancel an incomplete high phase. Data is held through the falling tick.
- SPI: [Analog Devices, Piyu Dhaker, Introduction to SPI Interface](https://www.analog.com/en/resources/analog-dialogue/articles/2018/08/13/15/31/introduction-to-spi-interface.html),
  read 2026-10-12, Table 1 and Figs.2–5. Lane order SCLK/CS/data, active-low CS,
  MSB-first 8-bit words, one receive direction at a time. Mode 0 samples rising;
  mode 1 falling; mode 2 falling; mode 3 rising. CPHA selects first/second edge.
  CS assertion/deassertion supplies boundaries; partial words are rejected by
  event-only assembly. No universal SPI electrical timing is claimed: the modeled
  peer guarantees at least one tick setup/hold and pauses at a legal clock level.
  Manufacturer article retained as link only; no redistribution grant assumed.

All candidates receive nine features: three bipolar levels, three signed edges,
and three ages clipped at 256 ticks and normalized by 256. Ages and previous
levels persist across messages/chunks. One common programmable sampling divider
is represented by the sampled tick; raw-clock electrical behavior is out of scope.

Common output classes: NONE, BIT0, BIT1, START, STOP, INVALID. An event has a
separate occurrence field and optional bit value, observation tick and decision
tick. Repeated bits remain separate events. No sample, tick-based bit counter or
protocol decoder is accessible to the assembler. Protocol-aware offline label
auditors are deliberately separate from the learned inference path.

A shared one-register pulse former emits on transition into a non-NONE class.
Holding one class for several ticks produces one occurrence; returning to NONE
allows another identical bit. This register is continuous across chunks and is
included in costs. No protocol-specific debounce or timing allowance is applied.
Exact boundaries require equality of observed reference decision ticks.

## Declared sampled timing envelope

All durations below are sampled ticks, not an electrical specification or a
claimed silicon frequency. Fractional analog edge placement is represented only
through the sampled levels; rise/fall voltage trajectories are not modeled.

| Profile / condition | Generated timing |
| --- | --- |
| UART nominal | 16 ticks per transmitted bit, continuous fractional phase and adjacent frames |
| UART mismatch | Transmitter period 16 × 0.97 or 16 × 1.03; receiver nominal unchanged |
| UART jitter | Each rounded nominal cell edge independently perturbed by -1, 0 or +1 tick; no accumulated jitter random walk |
| UART gaps | 0–64 high ticks between characters; message-group idle is 17–48 plus 32 trailing ticks |
| I2C nominal | Completed data clocks have 9 low / 8 high ticks, including the explicitly held falling-edge tick |
| I2C duty | 13 low / 5 high ticks |
| I2C stretch | A 15% per-bit chance of 1–96 additional low ticks; no protocol maximum is inferred |
| I2C phase | SDA changes one tick before SCL rises and remains held through its falling tick |
| SPI nominal | 8 idle-polarity / 4 opposite-polarity ticks between ordinary sampling cycles |
| SPI duty | 6 idle-polarity / 9 opposite-polarity ticks |
| SPI pause | A 15% per-bit chance of 1–96 extra idle-polarity ticks |
| SPI phase | Data has one tick of setup to the configured sampling edge, in each of modes 0–3 |
| Startup / idle | Cold state; arbitrary mid-message crop; 4,096-tick idle inserts; recovery after observable synchronization |

The full legal analog timing domain and unbounded stretching/pauses are not
exhaustively tested. The qualification assertion, if ever achieved, is only for
these declared conditions and sampled interface assumptions.
