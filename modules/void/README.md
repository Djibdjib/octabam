# `void` — VOID

Replaces **COMB FILTER** (FX2 id `0x13`). Code sits in harvested **PLATE REV**
words.

Grit: track input blended with white / pink / brown noise,
amplitude-modulated by an audio-rate LFO, then a mild HP/LP body and a soft
clip. **FDBK** recirculates the post-clip sample into the drive (one-sample
loop). Always wet — there is no dry/wet MIX.

r7 `$40..$4f` stays reserved for a longer FEED delay later.

## Knobs

| page | slot | name | range | what it does |
|---|---|---|---|---|
| 1 | 0 | BAL | 0–127 | input↔noise; **0 = full input (default)**, 127 = full noise |
| 1 | 1 | RATE | 0–127 | LFO rate, expo 2 Hz … 200 Hz |
| 1 | 2 | SHPE | SIN / SQR / SAW | LFO shape |
| 1 | 3 | DPTH | 0–127 | AM depth; 0 = source alone |
| 1 | 4 | DRV | 0–127 | soft-clip after AM+body+FDBK; 0 = bypass |
| 1 | 5 | FDBK | 0–127 | one-sample feedback into DRV; 0 = off |
| 2 | 6 | COLR | 0–127 | body low-pass; 127 = open — **turn down to darken** |
| 2 | 7 | HPF | 0–127 | high-pass before COLR; **0 = bypass, turn up to thin** |
| 2 | 8 | NTYP | WHT / PINK / BRWN | noise colour (as BAL rises) |

Noise peaks around −6 dB at BAL=127. High FDBK + DRV screams (AC feedback —
a raw one-sample loop was railing to DC / silence past ~FDBK 50 with drive).

SETUP top row: COLR · HPF · NTYP.

## Storage and stock firmware

The page descriptor is cloned from **DARK REV** (`donor_desc=0x400d58b8`).
VOID's FX id is stock COMB's (`0x13`): a Part saved under stock COMB knobs
will not match VOID's layout — re-pick VOID or stamp defaults after flashing.

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
| 8 | NTYP (0–2) | MONO |
| 9–10 | (blank) | (blank) |
| 11 | (blank) | MIXF |

Saving on stock with DARK selected writes DARK's names into those slots; the
bytes are the same width. Keep a separate project copy, or re-select effects
and save, before going back to stock.

## Measured

- `verify_void.py`: passthrough; AM / FDBK vs `void_ref.py`; NTYP pink/brown
  diverge from white; COLR closed vs open; FDBK+DRV not DC-silent; max-knob
  ~3 s with rail-hit budget; two FX2 instances each have energy and stay off
  the rail.
- Hardware **VOID V7** (20 Oct 2026): built from the `void-handoff` working
  tree (not a git commit) — same BAL/AC-FDBK law as tip, but four `mpy`
  sites still used `y0` (mpysu risk). Tip `471c7d5b`+ uses `y1` there;
  `void.asm` is otherwise identical through `0b2c1aa6`.
- Hardware **VOID V8** (`471c7d5b` tip asm, BUILD V8): image to re-check after
  the signed-mpy fix — see test-remix README.

On V7 (Ilia's MKII), knobs exercised:

| knob | what was tried |
|---|---|
| BAL | default 0 = full input; raised toward noise (noise was too hot at full) |
| RATE / SHPE / DPTH | AM scrape on input and with BAL up |
| DRV + FDBK | FDBK ≳ 50 with DRV was silence before AC feedback; after AC, high FDBK+DRV keeps scraping |
| COLR / HPF / NTYP | SETUP top row live; HPF thins; NTYP WHT/PINK/BRWN with BAL up |

## Sources

- Carrier: WarpFold-style parabola (LOFI2 RING family).
- Pink: Paul Kellet economy; brown: one-pole leaky integrator.
