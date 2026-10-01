# 6×4 tile acceptance

status: missing

Blocks the G0 check that 6×4 is accepted by the flow. v0.3 sets `tiles: "6x4"` and marks it **[VERIFY]**: the template comment lists sizes only up to 8×2. The design must fit 6×4 and must not depend on 8×4.

The announcement's own budget is filed in [../../competition/area.md](../../competition/area.md): 24 tiles, about 200 µm × 150 µm per tile, about 0.7 mm², about 1K logic cells per tile. That text is not a measurement from this flow.

Required:

- Whether the CMOS5L Tiny Tapeout flow accepts `6x4` in `info.yaml`.
- The area and cell budget the flow actually allows, from that source, before the announcement estimate or the **[EST]** budget in v0.3 section 6.1 is treated as a routed result.

`info.yaml` already sets `6x4` because the announcement requires it. That setting is not confirmation that the flow accepts it.
