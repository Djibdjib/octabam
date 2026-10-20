# remix `void`

Carries VOID beside the stock FX set minus PLATE REV (VOID's DSP host).

## Hardware

- **VOID V7** (20 Oct 2026): BRAIN tag `VOID V7.RMX` — full `latest` + VOID +
  sidechain handoff from the `void-handoff` working tree (BAL/AC-FDBK, four
  `mpy` sites still on `y0`). Not a published git commit.
- **VOID V8** (tip asm = `471c7d5b` / this PR): same stack, signed `mpy x0,y1`
  at those sites. Flash `VOID V8.RMX` / `OCTATRACK_OCTABAMV8.bin` to match
  this tip's `void.asm`.

Knobs checked on V7: BAL default full input; RATE/SHPE/DPTH AM; DRV+FDBK AC
scrape (was DC-silent before AC); SETUP COLR·HPF·NTYP.
