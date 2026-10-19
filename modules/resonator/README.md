# `resonator` — RESONATOR

FX1 station: **4 pitched bandpasses** (Torso S-4 RING filterbank idea, not
a modal / Rings body). Wet is the input through four constant-peak bandpass
peaks. Per-band **GN** levels sit on page 1; pitches and **SCAL** (gain
scale) live on FX SETUP. SCAL 8 is the tame default (GN 64 = 0 dB); SCAL
127 restores build-TN smash headroom. DECY narrows the bands.

Buffer-free (state in r7). `Claims(fx1_only=True)`: FX2 instances dry-pass;
the FX2 chooser hides the row.

## Knobs

| page | slot | name | range | what it does |
|---|---|---|---|---|
| 1 | 0 | GN1 | 0–127 | band 1 level; 64=unity at SCAL 8 |
| 1 | 1 | GN2 | 0–127 | band 2 |
| 1 | 2 | GN3 | 0–127 | band 3 |
| 1 | 3 | GN4 | 0–127 | band 4 |
| 1 | 4 | DECY | 0–127 | high = longer ring / less drive |
| 1 | 5 | MIX | 0–127 | dry/wet; 127 = bands only |
| 2 | 6 | PIT1 | 0–127 | band 1 centre ~40 Hz … ~4 kHz |
| 2 | 7 | PIT2 | 0–127 | band 2 centre |
| 2 | 8 | PIT3 | 0–127 | band 3 centre |
| 2 | 9 | PIT4 | 0–127 | band 4 centre |
| 2 | 10 | SCAL | 0–127 | gain scale; 8=tame, 127≈build-TN |

## Measured

- Render gates in `tools/verify/verify_resonator.py`. Not on hardware.

## Gates

`tools/verify/verify_resonator.py` (manifest `Gate`).

## Sources

- Torso S-4 RING — behaviour target (filterbank, not modal reverb).
- JOS two-zero constant-peak bandpass / Spectrum VOWL form (MIT).
