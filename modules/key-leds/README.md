# KEY LEDS

In CHROMATIC trig mode the 16 trig keys show a keyboard: stock lights it
as C major whatever the track's KEY, C yellow (keys 1 and 13), the other
white keys red, the black keys dark. KEY LEDS lights the track's scale
instead, in the same colours: the tonic yellow, the scale's other notes
red, the notes outside it dark. Key 1 is still C, as stock's keyboard is;
only the colours move. The scale comes from a source (below): on a MIDI
track, its MIDI ARP SETUP KEY; on an audio track, SCALE QUANTIZER's SCALE
and ROOT (PROJECT > CONTROL > SEQUENCER), whose keyboard starts on ROOT.

- Stock's KEY values: Major and Minor in all twelve keys.
- With [MIDI SCALES](../midi-scales/README.md) in the remix: its Dorian,
  Phrygian, Lydian, Mixolydian and Locrian too.
- With [SCALE QUANTIZER](../quantizer/README.md) in the remix: the audio
  tracks light its SCALE (24 scales) on its ROOT. Its keyboard plays ROOT
  on key 1, so the yellow keys stay 1 and 13 and the pattern follows.
- KEY OFF, SCALE OFF, and an audio track without SCALE QUANTIZER: stock's
  C major, unchanged.

No menu, no setting, nothing saved. `Kind.CF_PATCH`: one DRAM unit
(`key_leds.s`, about 250 B) and one detour.

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

`kl_chromatic` asks `kl_source` for the current track's (`0x80000000`)
scale, on the side `0x80000012` says (audio or MIDI). With an answer it
sets the 32 levels and bits as stock's loop does, then goes where stock
goes after the 16th key (`0x400444f4`, d3 = 0). Without one, the
displaced instructions are replayed and stock's loop runs.

The pass saved d2-d6 / a2-a5 at its entry; the loop keeps its state there,
and the two LED routines are C calls. No branch in the pass lands inside
the displaced span (its loop returns to `0x400442f4`).

## Sources

The display and the scale are apart: the display asks one question, and
the modules that answer it are chosen at build time from the remix
(`remix.inc`, `manifest._sources`).

| entry | input | result in d0 |
| --- | --- | --- |
| `kl_source` | d0 = track 0..7, d1 = 0 audio / 1 MIDI | `mask << 8 \| key1 << 4 \| tonic`: mask bit p = pitch class p is in the scale, key1 = the pitch class trig key 1 sounds, tonic = the scale's (C = 0 .. B = 11); or -1: stock's keyboard |

A C call: d0-d1 / a0-a1 scratch, the rest kept. Today:

| side | in the remix | the source |
| --- | --- | --- |
| MIDI | MIDI SCALES | its own `ms_raw` (the track's KEY byte, by its source rules) and `ms_decode` (tonic and mode, -1 OFF): nothing of its encoding is copied here. The mode indexes `kl_masks`, the seven diatonic modes in `ms_decode`'s order |
| MIDI | otherwise | stock's KEY from the track's live setup lane `0x46c76df1 + 68 * t` (the byte `ms_raw` reads): 1..24 = 12 tonics x Major / Minor, tonic (v - 1) / 2, Minor when v is even; 0 OFF |
| audio | SCALE QUANTIZER | its own `SCALE_AT` (`0x400d2ca8`, the pinned `jmp qz_scale_mask`: the SCALE's pitch classes rotated by ROOT, 0 = OFF) and ROOT (`0x100b14ee`). With a scale on its keyboard is transposed so that key 1 sounds ROOT (its README, "key 1 sounds the root"), so key1 = tonic = ROOT. Nothing of its 24 masks is copied here |
| audio | otherwise | none: stock's keyboard |

A module that knows a track's scale answers here instead of drawing LEDs
of its own: one more `HAVE_<NAME>` in `_sources` and its branch in
`kl_source`, calling the module's own exported routine where it has one.
The display draws key k as pitch class key1 + k (mod 12): the tonic
yellow, the mask's other classes red, the rest dark.

## Guards

- **Audio tracks without a scale are stock.** Without SCALE QUANTIZER, or
  with its SCALE OFF (`SCALE_AT` answers 0), `kl_source` answers -1 and
  stock's loop runs.
- **SCALE QUANTIZER's clamped keys.** In its keyboard's other position a
  few keys clamp at -12 / +12 st and sound the nearest degree there (its
  README, "The sample track's two positions"); they are lit by the pitch
  class key 1 + k names, not by the clamped note.
- **KEY OFF is stock.** KEY 0 replays stock's loop: C major, as without
  the module.
- **A KEY byte out of range is stock.** Without MIDI SCALES, past 24
  (stock clamps there); with it, whatever `ms_decode` refuses (past 84).
  No table is indexed with an unchecked byte.
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
  module's tables: 86 runs per model, all equal. KEY 25..84 pass only
  through MIDI SCALES' `ms_decode` (the stock source refuses them), so the
  run also shows the source is the one chosen. A planted defect (the
  Dorian mask off by one bit) fails it on every Dorian KEY.
- On `test/key-leds` (no MIDI SCALES, the stock source) the same gate
  runs KEY 0..24: 26 runs per model, all equal.
- On `test/key-leds-quantizer` (KEY LEDS + SCALE QUANTIZER), the audio
  side: an audio track in CHROMATIC with SCALE / ROOT set in their
  battery-RAM bytes, every SCALE 0..24 on ROOT C and A and every ROOT in
  MINOR (60 runs, plus KEY 0..24 on the MIDI side: 85 per model), against
  the 24 scales as its README lists their semitones and key k = ROOT + k:
  all equal. A planted defect (key 1 left on C) fails it.
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
- With MIDI SCALES, a followed track's scale is whatever `ms_raw`'s
  source rules give (MIDI Follow and Harmony are not in this tree).
