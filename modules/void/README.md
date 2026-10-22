# `void` — VOID

Replaces **COMB FILTER** (FX2 id `0x13`, `replaces="COMB FILTER"`). In any remix
that carries VOID, COMB is off the FX chooser; a Part saved with stock COMB
opens without that effect (re-pick VOID or stamp defaults). Code sits in
harvested **PLATE REV** words.

Grit: this track’s input blended with white noise (shape with COLR/HPF; WID
for stereo), amplitude-modulated by an audio-rate LFO or (SETUP **SRC=NBR**)
the previous track’s keybus envelope. HPF/COLR/DRV/FDBK/AM hit the **noise**
only; dry is unfiltered. Always wet — no dry/wet MIX.

r7 `$40..$4f` stays reserved for a longer FEED delay later.

## Knobs

| page | slot | name | range | what it does |
|---|---|---|---|---|
| 1 | 0 | BAL | 0–127 | dry↔noise (**0 = exact dry**, 127 = pure noise) |
| 1 | 1 | RATE | 0–127 | LFO rate; idle when SRC=NBR |
| 1 | 2 | COLR | 0–127 | noise low-pass ~30 Hz..16 kHz; 127 = open |
| 1 | 3 | HPF | 0–127 | noise high-pass before COLR; **0 = bypass** |
| 1 | 4 | DRV | 0–127 | soft-clip on **noise** only; 0 = bypass |
| 1 | 5 | FDBK | 0–127 | one-sample AC feedback on **noise** only |
| 2 | 6 | SHPE | SIN / SQR / SAW | LFO shape; idle when SRC=NBR |
| 2 | 7 | DPTH | 0–127 | AM depth on **noise** only (LFO or nbr uni) |
| 2 | 8 | WID | 0–127 | mono → stereo grit (2nd noise, same HPF/COLR/DRV) |
| 2 | 9 | SRC | LFO / NBR | AM source (NBR = previous track keybus) |

**SRC=NBR:** noise opens from the previous track’s SC keybus level and stops
when that goes quiet (no LFO free-run). Default **SRC=LFO** keeps RATE/SHPE
on any track. AM and DRV/FDBK hit **noise only**:
`wet = (1−BAL)·dry + BAL·noise''`. BAL=0 is always exact dry; BAL=127 =
AM’d noise. SETUP **WID**: 0 = mono; >0 = second white → same HPF/COLR/DRV
(no FDBK) → same AM; `L/R = mid ± (w/2)·side` (mono sum keeps mid/LFO).

Noise peaks around −6 dB at BAL=127. High FDBK + DRV screams (AC feedback —
a raw one-sample loop was railing to DC / silence past ~FDBK 50 with drive).

SETUP: SHPE · DPTH · WID / SRC · · .

## Storage and stock firmware

The page descriptor is cloned from **DARK REV** (`donor_desc=0x400d58b8`).
VOID keeps COMB's id (`0x13`) but not COMB's knob layout — page bytes from a
COMB Part will not match VOID's names.

If the same page bytes are loaded under DARK REV, they read as DARK's knobs:

| our slot | our name | stock DARK |
|---|---|---|
| 0 | BAL | TIME |
| 1 | RATE | SHVG |
| 2 | SHPE (0–2) | SHVF |
| 3 | DPTH | HP |
| 4 | DRV | LP |
| 5 | FDBK | MIX |
| 6 | COLR | PRE |
| 7 | HPF | BAL |
| 8 | WID | MONO |
| 9 | (blank) | (blank) |
| 10 | (blank) | (blank) |
| 11 | (blank) | MIXF |

Saving on stock with DARK selected writes DARK's names into those slots; the
bytes are the same width. Keep a separate project copy, or re-select effects
and save, before going back to stock.

## Measured

- `verify_void.py`: passthrough; AM / FDBK vs `void_ref.py`; WID mono/stereo
  + 0→1 continuity + L/R anti-corr at full; COLR closed vs open; FDBK+DRV
  not DC-silent; max-knob true 3 s rail budget; two FX2 instances; live
  neighbour auto-drives AM (RATE ignored); BAL0 ignores DRV/FDBK/DPTH/WID.
- Hardware **VOID V9** (21 Oct 2026, tip `dd89e2e2`+): BRAIN `VOID V9.RMX` —
  COLR 30 Hz..16 kHz / HPF 20 Hz..8 kHz tables. See test-remix README.
- Hardware **V215 N7** (22 Oct 2026, Ilia's MKII): neighbour AM + Y-direct
  keybus (no X:$500); matrix then env-gated BAL crossfade.
- Hardware **LATEST NN** (22 Oct 2026, Ilia's MKII): noise-only AM/DRV/FDBK
  (no DIV); white noise + COLR/HPF; WID = second filtered/driven side,
  `L=(1−w)·mid+w·side`, `R=(1−w)·mid−w·side`. Prior handoffs on the way:
  **V215 NA** (pre-DIV scrape), **LATEST NL** (WID raw-side), **LATEST NM**
  (filtered side, L=mid / R-open — left pull). See test-remix README.
