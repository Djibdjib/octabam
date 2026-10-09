# STEM REC: what's next

Six items from Yves's list of 9 Oct 2026. Each has what happens now, a few
ways to do it, and a recommendation. Nothing here is built.

Sizes are rough. **Small**: a change inside the module and a gate.
**Medium**: a new routine, a new gate and a flash. **Large**: a new part of
the module, or a new module.

The firmware facts behind items 1 and 2 are in
[SAMPLE_SAVE.md section 8](../../docs/firmware/SAMPLE_SAVE.md#8-the-attribute-file-ot-and-the-tempo),
read from the image on 9 Oct 2026.

## 1. The tempo isn't written to the stems

**Now.** STEM REC writes a bare WAV and no `.ot` file. The `.ot` is the
Octatrack's attribute file beside a sample: tempo, trim, loop, timestretch,
gain and slices. Without one, the unit guesses when it loads the file. It
assumes a power of two bars, picked from the length alone, so the tempo it
shows always lands between 80.75 and 161.5 BPM. It never reads the
project's tempo. A 61 s take at 120 BPM loads as 32 bars at 125.9 BPM.

**Check it first.** The guess predicts each of the nine takes of 8 Oct
2026, from its length alone. Load one file from a take into a Flex slot
and read TEMPO on the AUDIO EDITOR's ATTRIBUTES page. If the unit shows
these tempos, though the project's tempo didn't change between takes, the
cause is confirmed.

| take | length | guess |
|---|---|---|
| `261008-1131` | 6.75 s | 4 bars, 142.25 BPM |
| `261008-1421` | 18.08 s | 8 bars, 106.21 BPM |
| `261008-1422` | 62.80 s | 32 bars, 122.29 BPM |
| `261008-1423` | 28.98 s | 16 bars, 132.50 BPM |
| `261008-1424` | 44.63 s | 16 bars, 86.04 BPM |
| `261008-1425` | 69.77 s | 32 bars, 110.08 BPM |
| `261008-1426` | 17.89 s | 8 bars, 107.29 BPM |
| `261008-1856` | 61.35 s | 32 bars, 125.17 BPM |
| `261008-1858` | 4.31 s | 2 bars, 111.50 BPM |

The unit shows tenths, so a guess such as 142.25 can read 142.2 or 142.3.

**Options.**

- **A. Write an `.ot` beside each file.** Recommended. When a take starts,
  STEM REC keeps the project's tempo, as the stock recorder does. When it
  ends, the writer adds `T1.ot` and the rest beside the WAVs: 832 bytes
  each, the tempo as BPM × 24, the trim and loop lengths in bars from the
  firmware's own formula, and the trim end at the file's last sample.
  Fourteen small files at most, after the audio. Item 2 settles the fields
  the tempo doesn't decide. Size: small to medium.
- **B. Put the BPM in the file name**, such as `T1 120.wav`. The loader
  looks for the BPM in the name, but only among half, once and twice its
  guessed bar count. That helps only when a take is exactly a power of two
  bars long. Not worth it.
- **C. Stop on a bar line.** A take of whole bars lets the guess land right
  when the bar count is a power of two and the tempo is in range. Good for
  loops, but it doesn't fix the tempo by itself. Size: small.
- **D. A tempo chunk in the WAV** (`acid`), for DAWs. The Octatrack's
  reader ignores it: it reads `fmt `, `data`, `cue ` and `smpl` only.
  Optional, after A.

**Open.** A tempo change during a take: A keeps the tempo the take started
at. `STATS.TXT` could note a change.

## 2. What else the stock recorder sets

**Now.** A stock SAVE SAMPLE writes two files: the WAV and its `.ot`. The
`.ot` holds the tempo, the trim and loop lengths in bars, the timestretch
mode, the loop mode, the gain, the trig quantization, the trim start and
end, the loop point, up to 64 slices and a checksum. The recorder stamps the
project's tempo into a buffer when it records. STEM REC sets none of these.
Its WAV header is the same 44 bytes as stock's, and its RIFF size is right,
where stock's looks 8 bytes too large (SAMPLE_SAVE.md section 3).

**Not known.** The values the stock recorder gives the timestretch mode, the
loop mode, the gain and the trig quantization. Also the two header longs
the writer copies from RAM.

**Options.**

- **A. A reference `.ot` from the unit.** Recommended, and first. Record
  four bars with the stock recorder at an odd tempo, such as 123.4 BPM, and
  save it from the AUDIO EDITOR. Copy the `.wav` and the `.ot` off the
  card. Decoding that `.ot` answers every field. It also becomes item 1's
  oracle: STEM REC's `.ot` must match it field for field, apart from the
  lengths. No flash and no code.
- **B. Save a recorder buffer under the port.** The same answer without the
  unit, but the save path hasn't run under the port yet. Size: medium.
- **C. Slices at bar lines.** The `.ot` holds up to 64 slices. One slice a
  bar would make a stem ready to slice when it loads. Optional, after
  item 1.

## 3. A status that refreshes by itself

**Now.** MAIN MENU redraws only on a key, so the time, `SAVING` and `DONE`
show at the next key press (STEM_REC.md section 16.1).

**Options.**

- **A. Redraw from the UI task.** Recommended. The UI task is the firmware
  task that reads the keys and draws the screen. TUNER already hooks the top
  of that task's loop and redraws its window from there, about seven times
  a second ([TUNER](../tuner/README.md)). STEM REC would redraw the STEMS
  list from the same place when a label changed and the list is on screen.
  The catch:
  TUNER claims that exact spot, and the build refuses two modules on one
  spot. A remix with both needs a shared hook or another spot in the same
  loop. Size: small to medium.
- **B. Wake the UI task from the writer,** with a message that makes it
  redraw. The UI task's message format must be read first. Size: medium.
- **C. Move to a screen of our own** (item 6). It needs A's hook anyway.

## 4. Double tap YES to arm

**The goal** (Yves, 9 Oct 2026). On the main page, outside any dialog or
menu, one YES arms the stock recording trigs. A double tap should arm STEM
REC as well.

**Now** (read from the image, 9 Oct 2026). Both stock keymaps send YES to
`0x4005e4c8`, on press and on release.

- With no key held, a press sets every one-shot arm bit and shows `ARM
  ALL`. With a track key held, it arms that track and shows `ARM TRK` or
  `ARM REC TRK`.
- The arm only sets bits; it never toggles them. So a second YES repeats
  the same arm and changes nothing. A double tap is safe for the stock
  half.
- A menu or a dialog pushes its own key layer over YES (MAINMENU.md
  section 6c). So this handler hears YES only on the main page, which is
  the scope Yves wants.
- KITS hooks FUNC + YES (`0x4005e3d8`), a different handler. Nothing hooks
  plain YES.

**The design.** A detour at the handler's first instruction. On each press
on the `ARM ALL` path, it reads DMA timer 3, the counter `STATS.TXT`
already uses. If the previous press was less than about 0.4 s earlier,
STEM REC does what its REC row does: it arms, or it starts at once when
the sequencer runs. The stock arm still runs on both taps. The second tap
shows `STEMS ARMED` through the same stock message call that shows `ARM
ALL`, so the two are easy to tell apart. A gate under the port presses YES
twice and checks the state. Size: small to medium, plus a flash.

**Open.**

- **What a double tap does while a take records.** Performers tap YES
  quickly to re-arm one-shots, so a double tap can happen by accident. The
  safe choice: a double tap only arms or starts, and never stops or
  cancels. STOP and the menu still end a take.
- **Track key held.** A double tap with a track key held stays stock
  (`ARM TRK`), unless you want it to arm STEM REC for that track only.

## 5. A stem player machine

**The goal.** One track plays up to 16 files from one folder together, all
starting on the trig, as a one-shot. Yves, 9 Oct 2026: it behaves like
Static tracks, streaming from the card. So there's no RAM limit on length,
and no control per stem.

**Now.** [SYNTH MACHINE](../synth/README.md) shows how a module replaces a
machine's sound. A Flex track whose sample has a marker name
(`FMSYNTH*.wav`) gets a renderer of the module's own in place of the stock
one, and the DSP shapes the result like a sample. SYNTH already references
the STATIC renderer entry too. What isn't known: which task refills a
Static track from the card (STEM_REC.md section 19.2), and how fast the
card reads on the unit.

**Options.**

- **A. Our own streamer, behind a STATIC renderer.** Recommended. A Static
  track whose sample is a marker plays the files in the marker's folder.
  This is STEM REC in reverse. A reader task fills a ring per file from the
  card, and the renderer sums the rings into the track's voice. When the
  track loads, each ring gets the start of its file, so a trig starts at
  once. In a STEM REC take the names are fixed (`T1.wav` to `D.wav`), so
  no folder listing is needed; any other folder needs the file browser's
  listing routine, which isn't read yet. The track's FX, AMP and level
  apply to the sum. It plays at the recorded speed, because the stock
  renderer's timestretch and pitch are bypassed. Size: large.
- **B. Drive the stock Static streamer** for several files on one track.
  This needs the stock streaming task found and read first. Size: large,
  most of it reading the firmware.
- **C. Today, with no code.** Up to eight stems on eight Static tracks, or
  `MAIN.wav`, the mix, on one.

**Measure first.** Sixteen stereo files need 2.8 MB/s from the card at 16
bits, 4.2 MB/s at 24 bits. Reads aren't measured on the unit, and they'd
share the card and its file lock with the Static tracks that play. On a
busy project the card already falls behind STEM REC's writes (STEM_REC.md
section 17.3). A probe that reads sixteen files in a loop while a busy
project plays, and writes its rate to a text file like `STATS.TXT`, says
whether A can work before any of it is built. Size: small to medium, plus
a flash.

**Open.** Static plays 24-bit files from a 16-bit cache (BuMa's reading of
the code, STEM_REC.md section 19.1). A stem player could do the same, or sum all 24 bits.

## 6. A STEM REC screen

**Now.** STEMS is an 18-row list with seven rows on screen. The sources,
the format, the status and the peak all sit in that list, and the status
refreshes only on a key.

**Options.**

- **A. A full screen of our own.** Recommended as the goal. octalab's
  CAPTURE page draws one with stock calls that octalab documents (its
  `INPUT.md` section 10), and it owns the keys while it's open. One screen
  could hold the sources as a grid, the format, the state, the time, the
  ring's fill as a bar, and the time left on the card. The 16 trig keys
  could toggle the sources, with their LEDs showing which are on
  ([KEYMAP.md](../../tools/panel/KEYMAP.md) has the key and LED map). It
  ticks from item 3's hook. Every part has a precedent. Size: large.
- **B. A status window only.** Recommended as the first step. A window the
  size of TEMPO's, over any page, as TUNER's is. It shows the state, the
  time and the ring's fill, and it opens when a take arms or starts. The
  settings stay in MAIN MENU. Size: medium.
- **C. Tidy the list.** Fold the sources into one row that opens a short
  list of its own. It doesn't fix the status by itself. Size: small to
  medium.

**Open.** STEM REC doesn't read the card's free space yet (README,
"Limits"). The time left needs it.

## Order of work

1. Item 2 A: a reference `.ot` from the unit. No code.
2. Item 1 A: write the `.ot`, checked against that reference.
3. Item 3 A: redraw from the UI task.
4. Item 4: the double tap of YES.
5. Item 6 B, then A: the status window, then the full screen.
6. Item 5: the card read probe on the unit, then A as its own module.

Items 1 to 3 build on PR #644 (zero copy): the writer that would write the
`.ot` files is the one in that PR.
