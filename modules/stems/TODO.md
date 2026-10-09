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

**Check it first.** Take `261008-1858` should load as 2 bars at 111.5 BPM,
and take `261008-1131` as 4 bars at about 142.2 BPM, whatever the project's
tempo was. Load one file from each into a Flex slot and read TEMPO on the
AUDIO EDITOR's ATTRIBUTES page. If both match, the cause is confirmed.

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

**Which one?** Three readings, each a different build:

1. Arm from anywhere, without opening MAIN MENU.
2. Inside STEMS, a double tap on any row arms, so you don't scroll back to
   REC.
3. A guard: arming takes two taps, so a stray press doesn't arm.

**Now.** YES confirms in every stock dialog and list, so a double tap
anywhere would also confirm whatever is open. The firmware already times
double presses of the page and track keys (MAINMENU.md section 6).

**Options.**

- **For reading 1, a key chord.** Recommended over a double tap. Hold one
  key and press another, a pair no stock screen uses, as TUNER does with
  UP + TEMPO. The pair comes from the stock keymaps (MAINMENU.md section 6),
  checked under the port. Size: medium.
- **For reading 1, also MIDI.** A CC or a program change arms and stops. No
  key conflicts, and a DAW can drive it. Size: small to medium.
- **For reading 2,** a second YES within about 0.4 s arms. On a track row
  the first tap has already toggled the track, so the second toggles it
  back before it arms. On the REC row one tap still arms. Size: small.
- **For reading 3,** REC asks for a second YES within about 0.4 s. Size:
  small.

## 5. A stem player machine

**The goal.** One track plays up to 16 files from one folder together, all
starting on the trig, as a one-shot.

**Now.** [SYNTH MACHINE](../synth/README.md) shows the pattern. A Flex track
whose sample has a marker name (`FMSYNTH*.wav`) gets a renderer of the
module's own in place of the stock one, and the DSP shapes the result like a
sample. Flex is the machine that plays from RAM; Static streams from the
card. Flex RAM is about 85 MiB: sixteen stereo stems at 16 bits fit about
30 s each, and eight fit about a minute. At 24 bits, two thirds of that.

**Options.**

- **A. A Flex renderer that sums slots.** Recommended for a prototype. A
  Flex track whose sample is a marker, such as `STEMS*.wav`, plays its own
  slot and the next slots, summed, from their starts, on each trig. The
  stock loads the files. The track's FX, AMP and level apply to the sum.
  SYNTH's hook has run on the unit. Limit: RAM. Size: large.
- **B. A folder loader,** to go with A. A STEMS action puts a take's files
  into consecutive Flex slots, so nobody assigns sixteen slots by hand. The
  stock load path isn't read yet. Size: medium to large.
- **C. Stream from the card:** STEM REC in reverse. A reader task fills a
  ring per file, and the renderer mixes them. No RAM limit, but sixteen
  files at 16 bits need 2.8 MB/s from the card. Reads aren't measured, and
  on a busy project the card already falls behind STEM REC's writes
  (STEM_REC.md section 17.3). Size: large.
- **D. Today, with no code.** `MAIN.wav` is the mix already. Load it on one
  Static track. There's no control per stem.

**Questions.** Should each stem get a level or a mute? PLAYBACK has six
knobs, so sixteen stems would need groups. Must the stems follow the
sequencer's tempo (timestretch), or play at their recorded speed?

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
  time and the ring's fill, and it opens on REC or on item 4's chord. The
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
4. Item 6 B, then A: the status window, then the full screen. Item 4's
   chord opens it.
5. Item 5 as its own module, after a prototype of A measured under the
   port.

Items 1 to 3 build on PR #644 (zero copy): the writer that would write the
`.ot` files is the one in that PR.
