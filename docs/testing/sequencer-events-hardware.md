# EUCLID / SEQUENCER EVENTS hardware regression

Purpose: compare EUCLID's existing transport behavior with the same module
subscribed to SEQUENCER EVENTS. This PR introduces the dispatcher and migrates
EUCLID; it does not change EUCLID's DSP or add HARM, Follow or Loopback.
Hardware status starts **NOT RUN**. A successful build or emulator run does not
fill in a hardware result.

## What to copy and connect

The private package contains `EUCL BASE 94.RMX` (upstream Inserts) and
`EUCL EVENTS 94.RMX` (the candidate) in `BRAIN/REMIXES/`, plus separate `set/EUC-BASE/` and `set/EUC-CAND/` projects.
The source revision and SHA-256 for each are in `images.json`.

1. Back up your current project. Stop playback, enter USB DISK MODE and copy
   both RMX files into the card's `/BRAIN/REMIXES/` directory.
2. Copy both supplied project folders, including each `AUDIO` subfolder, into an
   existing Set on the card. Do not merge either into another project. If the name
   already exists, preserve that folder and use a fresh copy with a different name.
3. Safely eject before leaving USB DISK MODE. In MAIN MENU > BRAIN > REMIX
   SWITCH, choose `EUCL BASE 94`. Confirm that exact name is running.
4. Load `EUC-BASE`. Use MAIN L/R into headphones or your usual stereo monitor
   path at a low starting volume. No external sound source or MIDI cable is
   required. The project uses its included two-second stereo PCM loop at 120 BPM.
5. Select `EUCL EVENTS 94` through the same Remix Switch menu, confirm its
   running name, and load the separate supplied `EUC-CAND` project.
   Run the same steps on these separate copies. Never reuse the baseline's
   edited project as the candidate's starting point.

All four prepared patterns use Part 1 and 16 steps at 1x speed; unused patterns
and MIDI trigs are empty. Scenes have no locks and LFO depths are zero.

| Pattern | Prepared path | Initial controls |
| --- | --- | --- |
| A01 | T1, EUCLID in FX1 | AMP / GATE, 8 steps, 3 pulses, RATE 1/16, ROT 0 |
| A02 | T5, EUCLID in FX2 | LP / ENV, 16 steps, 5 pulses, RATE 1/16, ROT 0 |
| A03 | T1 and T5 together | Both prepared paths, on opposite DSP cores |
| A04 | T2, EUCLID in both FX1 and FX2 | AMP/GATE followed by LP/ENV |

Select a pattern using PTN plus its numbered trig. Select its active track
with T1, T5 or T2. FX1/FX2 opens the relevant page; double-press opens SETUP.
For each case record baseline and candidate separately in `RESULTS.md`.
Budget roughly 20–30 minutes for both images, plus the persistence/soak case.

## Cases

### E01 — Identity and normal playback

Check the running image name and project name. Play A01 for eight bars, then
A02, A03 and A04 for eight bars each. A01 should pulse in amplitude; A02 should
have rhythmic filter movement; A03 exercises both at once; A04 exercises both
slots on one track. There must be no new silence, frozen modulation, crash or
persistent loud artifact compared with baseline. Record a short stereo clip of
each pattern if you have a recorder. Exact RAND values are not used here.

### E02 — Fresh PLAY resets

On A01, STOP, wait one second, then PLAY. Repeat 20 times at different points
in the rhythm. Repeat on A02 and A03. Each fresh start must begin the same
EUCLID phase as the baseline; instances must not retain a phase from the previous
run or intermittently miss a reset. Check A04 five times as well. Record one
30-second clip containing several restarts, or a video showing transport and audio.

### E03 — Pause and resume uses the second PLAY path

While A01 plays, press PLAY to pause; wait a second and press PLAY to resume.
Repeat 20 times, including pauses between pulses. Repeat on A03 and A04.
The native pattern resumes from its paused position; EUCLID resets its own
phase on this resume path. Compare that combination with baseline rather than
expecting the pattern cursor to return to step 1. Both active instances must
resume without sticking, losing a reset or producing a new transient.

### E04 — Changes while running

On A01, change ROT through 0, 1 and 3; PULSE through 0, 3 and 8; and STEPS
through 8, 7 and 16 (these are displayed lengths). Double-press FX1 and change
RATE from 1/16 to 1/8 and back. Repeat one STOP/PLAY and one pause/resume after
each change. Zero pulses should return to the base level, not freeze the UI.
On A02, cycle TYPE through LP/BP/HP/AMP/NOTCH at modest resonance. Change OUT
through ENV/GATE/RAND/LOOP and back. RAND is deliberately variable: compare
responsiveness, mode transitions and reset behavior, not sample-identical audio.

### E05 — Pattern and Part context

Return to the fresh project copy if earlier edits changed the starting values.
Play A01, switch to A02, A03 and A04, then back to A01; repeat five cycles.
Patterns should change normally and the intended tracks/slots must respond.
Press PART to open Part Quick Select. Highlight Part 2 and press YES to link
it to the current pattern. Part 2 already has the same prepared effect assignments.
Change EUCLID's ROT there. Use PART, the arrows and YES to switch between
Parts 1 and 2 while stopped and while playing,
then repeat fresh PLAY and pause/resume. Each Part must retain its own parameter
values; transport resets must still work. Record any difference seen on baseline.

### E06 — Saved state, cold start and short session

Save the test project (FUNC+PROJ on MKII, or PROJECT > SAVE), wait for writing to finish,
load another project and reload the saved test. Check the effect assignments and
saved controls, then repeat E02/E03 once. Power off normally, wait ten seconds,
power on and confirm the running image name. If necessary select the intended
RMX again before testing. Reload the saved project and repeat E02/E03.
Finally play A03 for ten minutes, occasionally changing patterns and pausing.
Record elapsed time and any stuck phase, unexpected silence or crash.

## Capture and acceptance

Optional Mac capture from an already connected audio interface:

```sh
python3 tools/hw/capture_hw.py --list
python3 tools/hw/capture_hw.py -d <input-index> -t 30 -o /absolute/new/path/E02-candidate.wav
```

Choose the input receiving the Octatrack, not the Mac microphone. Use different
filenames for every capture; the recorder can overwrite a named output file.
A phone video is useful for the relationship between button presses and audio.

PASS means the stated expected behavior was observed on the named physical
image. FAIL needs the exact case, controls, reproduction and evidence filename.
NOT RUN/BLOCKED stays explicit. If both images fail identically, record an
existing behavior; do not call the candidate accepted by silently skipping it.
There is no required new sound: this migration should preserve EUCLID behavior.
Do not declare the shared MIDI-output notifications physically tested by these
EUCLID-only cases; synthetic dispatch tests cover them in software.

The local PR draft remains unpublished until hardware results are added. Include
device model, image hashes, test date, cases, captures and unresolved differences.
Generate another pristine project with `tools/hw/euclid_hardware.py --source
<private-template> --out <new-directory>`; the source is never modified.
