# SCALES

One catalogue of scales that every module can use, a scale chooser in
stock's list window, and the CHROMATIC trig keys lit with the scale.

- **The catalogue**: 52 scales in 9 families, each a 12-bit mask over the
  semitones above its tonic (IONIAN, written from the tonic up, is
  `1010 1101 0101`: C . D . E F . G . A . B). A scale's ID names it for
  good: a saved ID never changes meaning, a new scale takes the next ID.
- **The chooser**: stock's list window (the one BRAIN and STORE open), in
  two levels: the families, then the chosen family's scales. YES picks a
  row, NO closes it. A module opens it with `sc_pick` and gets the ID.
- **ARP SETUP's KEY** (a MIDI track, FUNC + AMP, encoder F): turned, the
  tonic (OFF, C .. B), the scale kept; pressed and released without a
  turn, the chooser. The sequencer's and the arpeggiator's notes snap to
  the scale (nearest note, ties downward). The field shows the tonic and
  the scale's short name (`C#` `PHRD`).
- **The CHROMATIC keys** light the track's scale in stock's colours: the
  tonic yellow, the scale's other notes red, the rest dark. On a MIDI
  track key 1 is C, as stock's keyboard is; on an audio track with
  [SCALE QUANTIZER](../quantizer/README.md) in the remix, its SCALE on its
  ROOT, key 1 = ROOT, as its keyboard plays.

KEY OFF, SCALE OFF and an audio track without SCALE QUANTIZER keep stock's
C major. `Kind.CF_PATCH`: one DRAM unit (`scales.s`, about 3.1 KB), four
detours, a poke and a pointer.

| family | scales (ID, short name) |
| --- | --- |
| MAJOR | 1 IONIAN (MAJOR) `MAJ`, 2 DORIAN `DOR`, 3 PHRYGIAN `PHR`, 4 LYDIAN `LYD`, 5 MIXOLYDIAN `MIX`, 6 AEOLIAN (MINOR) `MIN`, 7 LOCRIAN `LOC` |
| MELODIC MINOR | 8 MELODIC MINOR `MMIN`, 9 DORIAN b2 `DOb2`, 10 LYDIAN AUGMENTED `LYD+`, 11 LYDIAN DOMINANT `LYDD`, 12 MIXOLYDIAN b6 `MXb6`, 13 LOCRIAN #2 `LC#2`, 14 ALTERED `ALT` |
| HARMONIC MINOR | 15 HARMONIC MINOR `HMIN`, 16 LOCRIAN #6 `LC#6`, 17 IONIAN #5 `IO#5`, 18 DORIAN #4 `DO#4`, 19 PHRYGIAN DOMINANT `PHRD`, 20 LYDIAN #2 `LY#2`, 21 ALTERED bb7 `ALT7` |
| HARMONIC MAJOR | 22 HARMONIC MAJOR `HMAJ`, 23 DORIAN b5 `DOb5`, 24 PHRYGIAN b4 `PHb4`, 25 LYDIAN b3 `LYb3`, 26 MIXOLYDIAN b2 `MXb2`, 27 LYDIAN AUG #2 `LA#2`, 28 LOCRIAN bb7 `LCb7` |
| DOUBLE HARMONIC | 29 DOUBLE HARMONIC `DHAR`, 30 LYDIAN #2 #6 `L#26`, 31 ULTRAPHRYGIAN `UPHR`, 32 HUNGARIAN MINOR `HUNG`, 33 ORIENTAL `ORNT`, 34 IONIAN #2 #5 `I#25`, 35 LOCRIAN bb3 bb7 `LC37` |
| PENTATONIC | 36 MAJOR PENTATONIC `PMAJ`, 37 EGYPTIAN `EGYP`, 38 MAN GONG `MGNG`, 39 RITUSEN `RITU`, 40 MINOR PENTATONIC `PMIN` |
| BLUES | 41 BLUES `BLUS`, 42 MAJOR BLUES `BMAJ` |
| JAPANESE | 43 HIRAJOSHI `HIRA`, 44 IN-SEN `INSN`, 45 IWATO `IWAT`, 46 KUMOI `KUMO`, 47 PELOG `PELG` |
| SYMMETRIC | 48 WHOLE TONE `WHOL`, 49 DIMINISHED W-H `DWH`, 50 DIMINISHED H-W `DHW`, 51 AUGMENTED `AUG`, 52 CHROMATIC `CHRM` |

A family with modes lists them in the order of its parent scale's degrees.
SCALE QUANTIZER's 24 scales are all in the catalogue.

## Service

For other modules: register calls, d0-d1 / a0-a1 scratch, the rest kept.

| entry | input | result |
| --- | --- | --- |
| `sc_count` | | d0 = the number of IDs (52) |
| `sc_mask` | d0 ID | d0 = its mask (bit d = d semitones above the tonic), 0 for no such ID |
| `sc_name` | d0 ID | a0 = its name, as the chooser lists it; d0 = 0 for no such ID |
| `sc_short` | d0 ID | a0 = its 4-character name (NUL-padded), d0 = 0 for no such ID |
| `sc_family` | d0 ID | d0 = its family 0..8, -1 for no such ID |
| `sc_snap` | d0 note 0..127, d1 = ID << 4 \| tonic | d0 = the nearest note of the scale, ties downward; every other register kept |
| `sc_track` | d0 MIDI track 0..7 | d0 = ID << 4 \| tonic of its KEY, -1 for KEY OFF |
| `sc_pick` | d0 the ID shown first, a0 the routine to call | the chooser (UI task only); a0 is called with the chosen ID in d0, as a C routine |

A module that needs a scale asks here rather than carrying its own table,
and one that lets the player choose a scale calls `sc_pick` rather than
drawing its own list. A module's new scales come here, with the next IDs.

## A MIDI track's scale

The KEY (setup record `+0x11`) keeps what stock (1..24: 12 tonics x Major /
Minor) and [MIDI SCALES](../midi-scales/README.md) (25..84: Dorian,
Phrygian, Lydian, Mixolydian and Locrian per tonic) wrote, so a project
saved with either plays the same. A scale outside the seven diatonic modes
also writes its ID in the setup record's `+0x12`, a byte with no parameter
(CTRL1's setup slot 0, `docs/firmware/MIDI_TRACKS.md`); the KEY then holds
the tonic in Major or Minor (Minor when the scale has a minor third and no
major one), which is what stock plays for it. `+0x12` = 0, or past the
catalogue: the KEY's own mode.

The chooser's ID is stored as stock's ARP SETUP writer stores the KEY
(`0x4007a3ea..`): the Part byte, the CS1 mirror, the four unsaved flags,
`0x40027e00`, the live byte.

## How

| site | what |
| --- | --- |
| `0x400442e2` (12 bytes: `clrl %d5; clrl %d4; clrl %d6; lea 0x400135b0,%a3`) | the trig-LED pass's CHROMATIC branch: `kl_chromatic` |
| `0x40056ab8` (6 bytes: `tstl 0x460d1e4c`) | the UI task's per-tick routine: `kl_tick` (the chooser's push, the LED refresh) |
| `0x4007a3e2` (8 bytes: `moveq #5,%d1; cmpl %d0,%d1; bnew 0x4007a4cc`) | ARP SETUP's encoder handler: `sc_encoder`, encoder F |
| `0x4009fb58` (6 bytes: `tstl %fp@(-64); bles 0x4009fb80`) | stock's output quantization: `sc_output` |
| poke `0x400d4096` 25 -> 85 | ARP SETUP KEY's value count |
| pointer `0x400d40c6` `0x4003b790` -> `sc_format` | ARP SETUP KEY's formatter |

The encoder and output sites and the poke are MIDI SCALES' own, which
SCALES takes over (it reads MIDI SCALES' values and plays its modes).

**The push.** Stock does nothing on encoder F's push in ARP SETUP (under
the port, 30 Oct 2026: the KEY byte written by the turn, never by the
push). `kl_tick` watches the push switch's key record (code `0x3d`,
`0x46c7d8de + 0x10 + code * 0x18`, as CXOSC reads it) while ARP SETUP is
open (`0x400cfebe` nonzero) in MIDI mode; a release with no F turn since
the push (stock's quick edit turns with the knob pushed) and no list,
dialog or text editor open (`0x460e5e30`, `0x460e5cd0`, `0x460e7612`)
opens the chooser. The window opens from the UI task, as STORE's does.

**The chooser** calls `0x4006d94c(count, sel, &sel, labels, handlers)`
twice: the 9 families on the shown scale's family; a family's handler
opens its scales, on the shown scale's row when it is in that family. Each
list is a run of one table of name pointers, so nothing is built at run
time.

**The turn.** `sc_encoder` maps the KEY to an ordinal (OFF, C .. B), adds
stock's detent accumulator's step (`0x40032510(5, movement, 1024)`, four
counts a step, one step a report, as MIDI SCALES does), and gives stock's
store the change in d5. The mode is kept; from OFF it is `+0x12`'s
scale's (Major for none).

**The output.** `sc_output` snaps the note at `(a2)` for track d7 when the
scale is one stock does not play (MIDI SCALES' modes, `+0x12`'s IDs);
stock's Major / Minor and OFF go to stock's own path.

**The keys.** `kl_chromatic` asks `kl_source` for the current track's
(`0x80000000`) scale and sets the 32 levels and bits as stock's loop does,
then goes where stock goes after the 16th key (`0x400444f4`, d3 = 0);
without an answer stock's loop runs. Stock runs the pass when a key or a
mode change asks the LED dispatcher (`0x4007e998(slot)`), not when a KEY,
a SCALE or a ROOT is turned, so `kl_tick`, in CHROMATIC, asks `kl_source`
each tick and calls `0x4007e998(0)` when the answer differs from the one
the keys show.

## Sources

The keys ask one question; the answers are chosen at build time
(`remix.inc`, `manifest._sources`).

| entry | input | result in d0 |
| --- | --- | --- |
| `kl_source` | d0 = track 0..7, d1 = 0 audio / 1 MIDI | `mask << 8 \| key1 << 4 \| tonic`: mask bit p = pitch class p is in the scale, key1 = the pitch class trig key 1 sounds, tonic = the scale's (C = 0 .. B = 11); or -1: stock's keyboard |

| side | in the remix | the source |
| --- | --- | --- |
| MIDI | always | `sc_track`: the KEY and `+0x12`, key 1 = C |
| audio | SCALE QUANTIZER | its own `SCALE_AT` (`0x400d2ca8`, the pinned `jmp qz_scale_mask`: the SCALE's pitch classes rotated by ROOT, 0 = OFF) and ROOT (`0x100b14ee`); its keyboard plays ROOT on key 1 (its README), so key1 = tonic = ROOT |
| audio | otherwise | none: stock's keyboard |

A module that knows a track's scale answers here instead of drawing LEDs
of its own: one more `HAVE_<NAME>` in `_sources` and its branch in
`kl_source`, calling the module's own routine.

## Guards

- **Every table index is checked.** An ID outside 1..52 is refused by
  every service entry; a KEY past 84 or 0 is OFF; `+0x12` past 52 means
  the KEY's own mode.
- **Stock's scales stay stock's.** KEY 1..24 with `+0x12` = 0 goes to
  stock's output path, as without the module.
- **The push is only a press.** A push with a turn is stock's quick edit;
  nothing opens over an open list, dialog or text editor, or outside ARP
  SETUP on a MIDI track.
- **`+0x12` survives stock.** Stock 1.40C loads it (values past 127 load
  as 127; the IDs stop at 52) and SAVE PROJECT writes it; CTRL1 SETUP's
  YES (`0x4003fe14`) writes back the value its window read when it opened
  (`0x40059620`). BRAIN's MIDI templates leave it out (a byte with no
  parameter). On stock, a track with an ID in `+0x12` plays the KEY's
  Major or Minor.
- **Only the CHROMATIC branch.** The other trig modes, the running light
  and every other LED are untouched.

## Conflicts

MIDI SCALES, declared: both own ARP SETUP's KEY (the same encoder and
output detours and poke). SCALES reads MIDI SCALES' KEY values and plays
its modes, so a project made with MIDI SCALES keeps its scales.
BLACKPYRAMIDS_303 detours the trig-LED pass at `0x40044006`, a different
span.

## Measured

- `tools/verify/verify_scales.py`, its model built from music (each
  family's modes as rotations of its parent scale, the others as semitone
  lists, SCALE QUANTIZER's 24 from its README), not from the module's
  tables:
  - the linked code under unicorn, the image's own bytes: every ID's mask,
    family and names, the refusals; `sc_snap` for every ID x tonic x note
    (79,872); `sc_track` for every KEY 0..255 x 9 `+0x12` values; the
    installed output on 8 tracks (3,072 notes, stock's paths included);
    the installed encoder for every KEY 0..84 x 5 `+0x12` x 7 movements
    (2,975); the formatter's two strings and its bounds;
  - under the ColdFire port, MKI and MKII, on `test/scales`: the trig
    LEDs from the panel stream for every KEY 0..84 and every ID 8..52 on a
    tonic, a KEY turned while CHROMATIC is shown; the chooser driven from
    ARP SETUP's keys for each of the 52 IDs, the KEY and `+0x12` read back
    from the Part, the CS1 mirror and the live copy; reopened (YES YES
    keeps the scale), NO, F turned while pushed (no list), the list left
    open after a plain push; CTRL1 SETUP's YES. Under `--watch-mem` the
    commit-all (`pc 0x4003fe74`) writes `+0x12` back with the chosen ID.
    132 LED and 57 chooser runs per model, all equal.
  - On `test/scales-quantizer`, the audio side as well: every SCALE 0..24
    on ROOT C and A and every ROOT in MINOR, key k = ROOT + k.
- Planted defects: the CS1 store removed fails every chooser run's CS1
  read-back; the dispatcher call removed fails `refresh-midi`.
- `+0x12` and `+0x13` under stock 1.40C (a 16-bank project, every value
  0..255 in every bank, Part and track): load, SAVE PROJECT, load on stock,
  save, load on octabam: each value kept, 128..255 loaded as 127.
- The keys' display and refresh (KEY LEDS, the module this one grew from)
  on the user's MKII (OCTABAM22, 30 Oct 2026): the keys follow KEY, SCALE
  and ROOT, MIDI and audio, without a key press.

## Inferred, open

- The chooser, the KEY's turn and the snapped notes are not run on a unit
  yet.
- The short names in the KEY field: the formatter's two 5-byte strings
  draw 4 characters under the port (`PHRD`); lowercase `b` in names
  (`DOb2`) is drawn by the port's font as the unit's is assumed to.
- CTRL1 SETUP opened on one track and its YES pressed after the track
  changed writes the first track's `+0x12` (and CC numbers) to the second:
  stock's commit-all writes its window's values to the current track.
