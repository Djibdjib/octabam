# The one-cable hardware matrix

One remix, many configurations, on a unit with a single USB cable to a Mac and
nothing else: program change over USB MIDI selects a layout, MIDI START and a
host clock play it, the unit's USB audio stream is the capture, and LOAD METER
(vendor request `0xc0/0x57`) is the load readout. First run 24 Oct 2026
(`octabam-bus`, image A1, 28 layouts, about 10 minutes, no crash or freeze).
Tools: `tools/hw/ot_matrix.py`, `ot_stimuli.py`, `load_meter.py`,
`usb_transport_probe.py`, `usb_counters.py`. What none of it proves is under
"Limits".

## Once

- A fresh project made on the unit (PROJECT > NEW), copied off the card, and
  `python3 tools/hw/ot_matrix.py audit <dir>` finding nothing. Projects that
  descend from a working project fail the audit and are refused by `--clean`.
- `.venv/bin/python3 -m pip install pyusb libusb-package sounddevice numpy`
  (`brew install portaudio` for `sounddevice`).
- The unit's image: `make image REMIX=<remix> BUILD=<tag>`, the `.bin` on the
  card root, PROJECT > SYSTEM > OS UPGRADE (BUILDING.md section 5). Leave one
  `.bin` on the root: the upgrade took the first by name when there were
  several.

## Per remix

```bash
python3 tools/hw/ot_matrix.py plan <remix>                 # the layouts, and how many projects
python3 tools/hw/ot_matrix.py proj <fresh> <dest-prefix> <remix> --clean \
        --stimuli hits,pink,two_tones,sweep                # <dest-prefix>_01 ... up to 31 layouts each
```

Copy each `<dest-prefix>_NN` to the card (PRESETS/), load it on the unit, then:

```bash
python3 tools/hw/ot_matrix.py run <dest-prefix>_NN <label> [--only 0,5-9]
python3 tools/hw/usb_transport_probe.py      # START / STOP over USB, one layout, before a long run
python3 tools/hw/load_meter.py --for 10      # LOAD METER summary
```

`python3 tools/hw/ot_matrix.py report out/hw/matrix/<label>/report.json ...` prints a Markdown table per run.
`run` adds layout 0 (BASE) when `--only` leaves it out. Reports go to
`out/hw/matrix/<label>/report.json`: per layout the flags, the audio metrics,
LOAD METER's summary and its per-reading series; flagged layouts also leave a
WAV. A run holds the unit on one layout per 12 s of play, 3 s of tail and any
wait for the previous tail to fade (up to 15 s).

Layouts per remix, from `plan` (24 Oct 2026): `octabam-core` 24, `octabam-inserts`
70 (110 with `--pairs`), `octabam-bus` 27, plus BASE in each project. Two
cautions before a run: the `dear` settings can put a constant, up to full-scale
DC on MAIN, CUE and the headphones after STOP (below), so mute or turn down
what is connected; and when the card is mounted on the Mac, unmount it (not
eject) before leaving DISK MODE on the unit, since a read/write mount with
pending Mac writes coincided with two freezes (24 Oct 2026,
`FAILURE_MODES.md`).

## Predicting the combinations

A pair (an FX1 and an FX2 effect on the same track) or a split (one effect on
tracks 1-4, another on 5-8) is not run by default. LOAD METER reports each of
the 16 effect slots' cost, and a core's busy time is its base plus the sum of
its slots' costs: on the first runs (24 Oct 2026, 97 layouts of `octabam-bus`
and `octabam-inserts`) the sum matched the measured per-core busy to 0.14
points at the 95th percentile; the worst misses were layouts with one of 16
slots missing from the window. The same effect costs the same on either core's
slots (within 1.5 %) and on FX1 or FX2 (within 0.1 point).

```bash
python3 tools/hw/ot_matrix.py predict octabam-inserts \
        --reports out/hw/matrix/ins01/report.json out/hw/matrix/ins02/report.json out/hw/matrix/ins03/report.json \
        --select pick.json
python3 tools/hw/ot_matrix.py proj <fresh> <dest-prefix> octabam-inserts --clean --stimuli ... \
        --pairs --split --select pick.json
```

`predict` ranks every pair and split layout by predicted core busy and writes
the ones at or above `--threshold` (0.85) plus `--validate` (6) spread over the
rest, to check on the unit that the sum holds. It does not predict the
ColdFire's share (EUCLID's hook adds about 7 points), audio faults that need
the combination, or what the unit does past 100 % busy. A layout predicted
over 100 % overloaded the unit (24 Oct 2026: SPECTRUM FX1 + LOFI2 FX2 `dear`, predicted 105 %; the frame
interrupt fell to half rate and stayed there), so `predict` leaves those out unless `--include-overload`.
No single-slot run has gone past 98.8 %.

## Flags

Every flag is against BASE of the same project; thresholds are the constants at
the top of `ot_matrix.py`, first guesses not validated on a unit. A flag means
"differs from BASE past a threshold", not "broken".

| flag | meaning |
|---|---|
| CRASH | no audio in the first 2 s of play where BASE had some (sequencer stuck); the run stops |
| FREEZE | every channel silent for 1 s where BASE was not |
| CLICKS | isolated discontinuities: more events than BASE, in at most 10 % of the 512-sample blocks |
| ROUGH | the same events in more of the blocks: a rough or heavily modulated signal |
| STATIC | 8-16 kHz power 6 dB or more above BASE's |
| LEVEL | rms 3 dB or more from BASE's |
| CLIP | samples at full scale |
| DC / RINGS | the last half second of the tail is above -70 dBFS and BASE's is not; DC when the level is a held constant |
| OVERLOAD | the frame interrupt ran under 80 % of 2,756 a second: the DSP missed its frames; the unit stays degraded and the run stops (power-cycle) |
| LOAD | frame-interrupt share or a DSP core's busy/period at 90 % or more, from 2 s into play |

## Limits

- LOAD METER counts timer ticks; none of its figures has been compared with an
  independent measurement. It is absent from `octabam-core` (the 14 stock effects
  leave no DSP words), so that remix gets audio flags only.
- All eight voices start on step 1, so the ColdFire's longest run (about 93 % of
  a frame) is the start-up spike, and the ColdFire share is the same in every
  layout. DSP figures are the discriminating ones.
- BASE is one baseline per project; a fault BASE has too is invisible.
- The stimuli are synthetic (`ot_stimuli.py`): a fault that needs real material
  to show (a smeared transient in a reverb tail) may not.
- The first run's findings: MODULATION on all eight tracks reaches about 99 % DSP-0
  busy; four `dear` MODULATION layouts hold DC after STOP. The measurements are in
  the run's report, not repeated here.
