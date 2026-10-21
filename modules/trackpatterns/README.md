# `trackpatterns` -- TRACK PATTERNS

Each of the 16 tracks (T1–T8, M1–M8) can play its own pattern of the playing
bank, clip style, as on the Korg SQ-64. Hold [TRACK n], hold [PATTERN], press
[TRIG k]: track n plays pattern k from the end of its own loop, in time, while
every other track and the global pattern carry on. The sound stays the
playing Part's.

By pgstath (MIT, as octabam). Source also at
[pgstath/TrackPatterns](https://github.com/pgstath/TrackPatterns). `Kind.CF_PATCH`:
one DRAM unit (`trackpatterns.s`, generated from `trackpattern.c`,
`adapter.c` and `hooks.s` by `generate.py`) and eight detours. A remix with
this module carries the platform loader and its 10 MiB arena reserve, unless
another DRAM module already brings them.

## What it does

| Situation | Behaviour |
| --- | --- |
| Pick a track's pattern | Hold [TRACK n], hold [PATTERN], press [TRIG k]; a popup names it (`T1 > A03`). MIDI mode addresses M1–M8 |
| When it lands | At the end of that track's own loop; while stopped, at once |
| Back to normal | The global pattern's trig for that track (`T1 FOLLOWS`), or any global pattern change, a bank change included, which clears every override |
| Length | A track loops at its source pattern's length (its own under SCALE MODE PER TRACK, the pattern's under NORMAL) |
| Sound design, tempo, speed | The playing Part; the playing pattern's tempo and track speed |
| Trig LEDs | For the current track on its own pattern: outside GRID REC (TRACKS trig mode), where stock shows only the running light, that pattern's trigs blink slowly; in GRID REC the stock trigs (the global pattern the keys edit) blink as a warning. The running light stays. TRACK n + PATTERN lights the pattern T_n plays |
| Editing, recording | The global pattern, as stock |
| Saving | Not saved: after a reload or power cycle every track follows the global pattern |

## How

The tick hands each track's step to the step handler with a pattern
argument; TrackPatterns replaces it with the track's own and lands a queued
change when the track's stock step counter wraps. The rebuild after an edit
and the per-track advance's length compare follow the same choice. A track
with nothing set gets exactly what stock passes, and the step stock
prepares across a global or bank change follows stock.

| site | what |
|---|---|
| `0x400a2d76`, `0x400a39c0` | the tick's pattern argument, audio and MIDI |
| `0x4009dc8c`, `0x4009e3e2` | the rebuild after an edit (8 bytes, padded) |
| `0x400a3d88`, `0x400a3ea8` | the per-track advance: the length the counter wraps at |
| `0x40056b50` | the PATTERN layer's trig press: with a TRACK key held (the stock key-state table `0x46c7d8ee + 24·code`), the trig queues for that track, opens the toast and has stock prepare every track's step again |
| `0x4007e9b6` | the LED dispatcher `0x4007e998`, after a page's LED callback: the trig LEDs above |

`INVESTIGATION.md` has every address, where it came from and what was read
or measured, and names the stock instructions each detour displaces.

## Measured

- `modules/trackpatterns/verify.py` (the gate): the engine and the glue on
  the host, on fake firmware memory: a change landing at the track's own
  loop start for lengths 1–64, MASTER LENGTH's repeated step, PLAY
  restarts, the way back to following, global and bank changes clearing,
  the look-ahead, MIDI tracks, the popup text, the gesture and the trig
  LEDs. Planted defects fail it. With `m68k-elf-gcc` on the PATH it also
  checks that `trackpatterns.s` matches the C and assembles for the 5475.
- Under the ColdFire port (`ot_emu`, a project with distinct trigs on A01,
  A02 and A03 for T1 and M1): the gesture moved T1, then M1, from A01 to A03
  at each track's own loop start with no global queue written; the trig
  entries of the step handler followed; a global change to A02 cleared both;
  the trig LEDs blinked as above with the running light kept; the same as an
  MKI and as an MKII. `TESTING.md`.
- `make check REMIX=trackpatterns` (`remixes/test/trackpatterns/`).

## On the unit

- 21 Oct 2026, the contributor's MKII, image `OCTABAM3` built from this
  tree (`make image REMIX=trackpatterns BUILD=3`; hashes in `TESTING.md`):
  stock PATTERN + TRIG, the gesture on T1 and on M1, following again, a
  global change clearing, the stopped case, a latched PATTERN, chains, GRID
  REC, save and power cycle, and the three trig LED checks: all reported as
  passed. The same tests passed earlier that day on images built from this
  source in Modwerk's copy of octabam (`OCTABAM1`, `OCTABAM2`). Not reported:
  run length, LED colours, other tracks.

## Inferred, open

- Cycles and memory are not measured (the unit is 3,448 bytes in Modwerk's
  build: code 3,364, state 84). The work per track step is a few dozen
  instructions plus the engine's bookkeeping; not counted.
- Not run in one image with OCTAKIT (`kits`), which detours the PATTERN
  layer's trig handler's entry (`0x40056b2c`, before this module's
  `0x40056b50`), or with DIRECT JUMP / DIRECT_JUMP_KYOTI, which change how a
  cued pattern lands. The ledger finds no shared byte with any of them.
- Patterns longer than 16 steps, other trig modes than TRACKS for the LEDs,
  MIDI note-offs across a switch on a unit with a long note: not checked
  beyond the reports above.
- The track's speed (scale) stays the playing pattern's; overrides are not
  saved; trig LEDs and editing in GRID REC address the global pattern.

## Credits

The sequencer addresses build on devilfish707's Play Modes investigation
(Octaplay), which cites octabam (Sam Banks), Tim Hastie's DIRECT JUMP and
SCALE QUANTIZER, the KYOTI notes (Zac-Kyoti) and EUCLID; the LED model on
octabam's `docs/firmware/PANEL.md` (Tim Hastie's panel work).
