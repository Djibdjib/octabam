# KEY LEDS

In CHROMATIC trig mode the 16 trig keys show a keyboard: stock lights it
as C major whatever the track's KEY, C yellow (keys 1 and 13), the other
white keys red, the black keys dark. On a MIDI track whose MIDI ARP SETUP
KEY is set, KEY LEDS lights that KEY instead, in the same colours: the
tonic yellow, the scale's other notes red, the notes outside it dark. Key
1 is still C, as stock's keyboard is; only the colours move.

- Stock's KEY values: Major and Minor in all twelve keys.
- With [MIDI SCALES](../midi-scales/README.md) in the remix: its Dorian,
  Phrygian, Lydian, Mixolydian and Locrian too.
- KEY OFF, and every audio track: stock's C major, unchanged.

No menu, no setting, nothing saved. `Kind.CF_PATCH`: one DRAM unit
(`key_leds.s`, 266 B) and one detour.

## How

Stock's trig-LED pass `0x40043fdc` branches on the trig mode
(`0x460d16f0`); its CHROMATIC branch (mode 1, `0x400442da`) runs a loop
over keys k = 0..15: n = k mod 12; n = 0 sets the key's red and green
LEDs to level 15 (yellow), otherwise n is bumped past E (n > 4: n + 1)
and an even n is red at 15, an odd n dark. That is C major, computed, with
no read of any KEY. Each LED is a level (`0x400135b0(id, level)`, the
`0x3n <id>` panel message) and a bitmap bit (`0x400131a0(id)`); trig k's
red is id 2k, its green 2k + 1 (`tools/panel/KEYMAP.md`, "LED colours").

| site | what |
|---|---|
| `0x400442e2` (12 bytes: `clrl %d5; clrl %d4; clrl %d6; lea 0x400135b0,%a3`) | the CHROMATIC branch's first instructions: `kl_chromatic` |

`kl_chromatic`, in MIDI mode (`0x80000012`), reads the current track's
(`0x80000000`) KEY byte from its live setup lane, `0x46c76df1 + 68 * t`
(the byte MIDI SCALES' `ms_raw` reads). KEY 1..84 decodes as MIDI SCALES
does (`ms_decode_table`): 1..24 are stock's pairs, tonic (v - 1) / 2,
Minor when v is even; 25..84 five modes per tonic. The seven masks are
MIDI SCALES' `ms_masks` (radiohagen, MIT). It sets the 32 levels and bits
as stock's loop does, then goes where stock goes after the 16th key
(`0x400444f4`, d3 = 0). KEY 0, an audio track or a value past 84: the
displaced instructions are replayed and stock's loop runs.

The pass saved d2-d6 / a2-a5 at its entry; the loop keeps its state there,
and the two LED routines are C calls. No branch in the pass lands inside
the displaced span (its loop returns to `0x400442f4`).

## Guards

- **Audio tracks are stock.** The detour reads `0x80000012` first; in
  audio mode stock's loop runs, so SCALE QUANTIZER's keyboard and every
  audio track keep stock's LEDs.
- **KEY OFF is stock.** KEY 0 replays stock's loop: C major, as without
  the module.
- **A KEY byte out of range is stock.** Past 84 (no writer produces one:
  stock clamps at 24, MIDI SCALES at 84), stock's loop runs; no table is
  indexed with it.
- **Only the CHROMATIC branch.** The other trig modes (TRACKS, SLOTS,
  SLICES), the running light and every other LED are untouched.
- **Nothing persists.** The module writes no Part, project or settings
  byte; it reads the KEY each pass.

## Conflicts

None declared. BLACKPYRAMIDS_303 detours the same pass at `0x40044006`
(the trig-mode dispatch, SLOTS / SLICES dark), a different span; the build
refuses an overlap by itself.

## Measured

- `tools/verify/verify_key_leds.py` under the ColdFire port, MKI and MKII,
  on `test/key-leds-scales` (KEY LEDS + MIDI SCALES): MIDI mode, track 1,
  TRACK + the trig-mode list to CHROMATIC, the track's KEY byte set before;
  the trig LEDs decoded from the panel stream (both colours' levels) for
  every KEY 0..84, and an audio track. Compared with a model built in the
  gate from the modes as rotations of the major scale, not from the
  module's tables: 86 runs per model, all equal. A planted defect (the
  Dorian mask off by one bit) fails it on every Dorian KEY.
- On `test/key-leds` (no MIDI SCALES) the same gate runs KEY 0..24.
- KEY 0 and the audio track decode to stock's C major (keys 1 and 13
  yellow, the white keys red), the same as the stock image.

## Inferred, open

- Not run on a unit yet. The colours are the panel stream's levels; that
  red 15 / green 15 is the yellow and red 15 the red a player sees is
  KEYMAP.md's measurement against the manual, not this module's.
- When the pass runs again after a KEY turn in ARP SETUP while CHROMATIC
  is on: the gate sets the KEY before entering CHROMATIC. If the keyboard
  only updates at the next LED pass (a page change, a track change), that
  is stock's refresh, not changed here.
- MIDI Follow, Harmony and other writers of the KEY lane are not in this
  tree; the module shows whatever byte the lane holds.
