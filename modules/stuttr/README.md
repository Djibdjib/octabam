# `stuttr` — STUTTR

A per-track **chance grain repeater**. Input always writes into the stock FX
instance ring. On each RATE tick, CHNC may grab the last SIZE grain and
HOLD-loop it; miss stays dry. While holding, MODE sets playback rate and
REV rolls reverse per grain wrap. MIX 0 is bit-exact dry.

Re-select the effect after a flash if an old Part still has stale page
bytes (e.g. leftover JITR/FDBK/DECY from the prior topology).

## Knobs

| page | slot | name | range | what it does |
|---|---|---|---|---|
| 1 | 0 | SIZE | 0–127 | grain length; **(kn+1)²** words (≈ 0.1–180 ms on FX2) |
| 1 | 1 | RATE | 0–127 | how often CHNC may attempt a grab (slow→fast) |
| 1 | 2 | CHNC | 0–127 | 0 = never; 127 = always grab on tick; miss = stay dry |
| 1 | 3 | HOLD | 0–127 | after a hit: how long to keep repeating before dry |
| 1 | 4 | REV | 0–127 | per-**repeat** reverse probability (0 = always forward) |
| 1 | 5 | MIX | 0–127 | dry/wet of the stutter vs live |
| 2 | 6 | MODE | FWD / HALF / QUART / RND | 1× / ½× / ¼× / per-repeat random rate |
| 2 | 7 | SYNC | FREE / 16 / 8 / 4 | divisions of the RATE attempt clock |

## Behaviour

```
dry ──RATE tick──► CHNC roll ──miss──► dry
                      │
                     hit
                      ▼
              grab SIZE grain
                      ▼
         HOLD-loop (MODE rate, REV rolls)
                      ▼
                     dry
```

- **SIZE** words = `(kn+1)²` (min 8, even, clamp to maxlen). Same quadratic
  map as before so mid dial is useful.
- **HOLD** duration = `(kn+1)² × 16` samples (at least one full grain). Wet
  stays full until HOLD expires, then hard return to dry — no mid-stutter fade.
- **HALF / QUART** hold each stereo frame for 2 / 4 samples (pitched-down feel).
- **RND** picks FWD / HALF / QUART on each grab and each grain wrap.
- Grab start is always the last SIZE behind the write head (no JITR).

## Ring length (SIDECHAIN window)

`Claims.buffer_words = 15862` — same ceiling as GATE VERB / WAVE / BBD
(`+$3DFD`, #785). The last `$202` words of the T3/T7 FX2 slots are
SIDECHAIN_COMPRESSOR's cross-core keybus; a 16,384-word ring would write
into them. Init sets maxlen to 15,862 on FX2 (3,072 on FX1).

## Storage and stock firmware

The page descriptor is cloned from **DARK REV**; the FX id is **MULTIBCOMP**
(`0x19`, `replaces=` — stock null stub, not a free-pool id). A Part saved
with STUTTR keeps that id and the eight page bytes. Stock 1.40C runs
MULTIBCOMP (null stub) on that id. If the same page bytes are loaded under
DARK REV, they read as DARK's knobs:

| our slot | our name | stock DARK |
|---|---|---|
| 0–5 | SIZE…MIX | TIME, SHVG, SHVF, HP, LP, MIX |
| 6 | MODE (0–3) | PRE |
| 7 | SYNC (0–3) | BAL |

Keep a separate project copy, or re-select effects and save, before going
back to stock.

## Measured

Local render gates (`verify_stuttr`): MIX 0 bit-exact; CHNC 0 stays dry;
CHNC 127 + HOLD engages; SIZE loop gaps; HALF lengthens gaps vs FWD;
REV 127 reverses; every named knob renders.

## On the unit

Prior MKII flash (remix `glitch` **BUILD G4**, 19 Oct 2026) exercised the
**previous** always-loop topology (JITR/FDBK/DECY/LOOP–SCRAM). This
chance-engage redesign is port-proven; hardware re-proof pending.

## Open

- Project-BPM tempo sync
- Hardware re-proof of the chance-engage page

## Gates

`tools/verify/verify_stuttr.py` (manifest `Gate`).
