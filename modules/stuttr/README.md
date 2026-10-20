# `stuttr` — STUTTR

A per-track buffer glitch insert. Input is written into the stock FX
instance ring; RATE re-grabs a slice; SIZE loops it until the next grab.
JITR nudges each grab's start; DECY fades each grain into dry. MIX 0 is
bit-exact dry. Re-select the effect after a flash if an old Part still
has stale page bytes (e.g. leftover CHNC).

## Knobs

| page | slot | name | range | what it does |
|---|---|---|---|---|
| 1 | 0 | SIZE | 0–127 | slice length; **(kn+1)²** words (≈ 0.1–180 ms on FX2) |
| 1 | 1 | RATE | 0–127 | re-grab clock (slow→fast). If RATE is faster than SIZE, SIZE never finishes a loop |
| 1 | 2 | JITR | 0–127 | 0 = exact grab; higher = random start further behind write |
| 1 | 3 | FDBK | 0–127 | recirculate into the write head |
| 1 | 4 | DECY | 0–127 | fade into dry; **0 = hold**, higher = faster (**step = kn²**) |
| 1 | 5 | MIX | 0–127 | dry/wet; after DECY dry returns (no mute between grabs) |
| 2 | 6 | MODE | LOOP / REV / DROP / SCRAM | playback flavour |
| 2 | 7 | SYNC | FREE / 16 / 8 / 4 | internal clock divisions |

## SIZE / DECY curves

Both knobs use a **quadratic** map so the useful stutter range is not
crammed into 0–20:

- SIZE words = `(kn+1)²` (min 8, even, clamp to maxlen). kn 32 ≈ 12 ms,
  kn 64 ≈ 48 ms, kn 127 = full FX2 ring under the #785 rule (~180 ms).
- DECY step = `kn²` (0 = hold). kn 32 ≈ 186 ms fade, kn 64 ≈ 46 ms, kn 96 ≈
  23 ms — mid dial still sustains.

## Ring length (SIDECHAIN window)

`Claims.buffer_words = 15862` — same ceiling as GATE VERB / WAVE / BBD
(`+$3DFD`, #785). The last `$202` words of the T3/T7 FX2 slots are
SIDECHAIN_COMPRESSOR's cross-core keybus; a 16,384-word ring would write
into them. Init sets maxlen to 15,862 on FX2 (3,072 on FX1). The ring does
**not** need the full 16k; 15,862 is the measured maximum that stays clear
of the window.

## JITR

On each grab, start is pulled further back by a random even offset up to
about `(SIZE/2) * (kn/128)` words (≈ half SIZE at 127). The LFSR state is
kept in 16 bits and stored from a clean accumulator (no A2-stale / saturating
store). `max_off` is computed at block rate so the sample loop stays
cycle-countable.

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

Local render gates (`verify_stuttr`), including a JITR=127 grab-start
distribution check (not constant).

## On the unit

Ilia's MKII, 19 Oct 2026, remix `glitch` **BUILD G4** (`OCTABAMG4` /
`GLITCH G4.RMX`; that image also carried SHATTER, filed separately): every
STUTTR page-1/page-2 knob exercised (SIZE, RATE, JITR, FDBK, DECY, MIX,
MODE, SYNC). MULTIBCOMP `0x19`, 15,862-word ring, no build tag.

## Open

- Project-BPM tempo sync

## Gates

`tools/verify/verify_stuttr.py` (manifest `Gate`).
