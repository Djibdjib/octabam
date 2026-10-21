# TRACK PATTERNS testing

## Host gate (21 Oct 2026)

`python3 verify.py` on macOS (Apple clang, Homebrew python 3.12,
m68k-elf-gcc 16.2.0): both host suites pass, and the ColdFire unit compiles
and assembles for the 5475 with no calls outside it.

What the suites cover:

- A zeroed state follows the global pattern on every track.
- A queued change lands exactly at the track's own loop start, for lengths
  1–64, with the rest of the pass still on the old pattern.
- The global pattern's trig queues the way back to following; asking for
  what the track already plays withdraws a queued change.
- A global pattern change clears every override and every queued change;
  the same global pattern seen again changes nothing.
- While stopped, a change applies at once and PLAY plays it from step 1.
- The look-ahead names what then plays, across the loop end and after a
  queue (as the key stub has stock rebuild its steps).
- PLAY restarts land a queued change on step 1; the repeated step of a
  MASTER LENGTH restart is a loop start too.
- MIDI tracks (8–15), the popup text (`T5 > A03`, `M2 FOLLOWS`, the bank
  letter), out-of-range tracks and patterns.
- The adapter on fake sequencer memory: transport, playing bank and
  pattern, length source following the track.
- A bank change to the same pattern number (A10 → B10) clears the
  overrides, and the step stock prepares across it is B10's on every track;
  P16 is a pattern like any other.
- The gesture on fake key memory: no TRACK key held leaves the press to
  stock; TRACK 2 held (state 2, as once the PATTERN layer opened over it)
  queues for T2 with the toast `T2 > B05`; the lowest held TRACK key wins;
  MIDI mode addresses M5, not T5; the global pattern's trig makes the track
  follow again; a key past TRACK 8 is not a TRACK key.
- The trig LEDs on fake LED, UI and timer memory: a following track and
  other pages are left as stock drew them; GRID REC's dark half puts only
  the 32 trig LEDs out and names the running light's track (M4 in MIDI
  mode); the playhead is relit only on the page GRID REC shows; outside
  GRID REC the playing pattern's trigs go over stock's running light, page
  2 included, and not in CHROMATIC; MIDI tracks read the MIDI record; the
  PATTERN layer with TRACK 1 held lights T1's pattern, its queued change
  and the global pattern as one with content. Planted defects fail them
  (inverted blink, 6 failures; a key off by one, 3; no running light
  redraw, 2; overwriting stock's LEDs, 3; the page check dropped, 1).

Planted defects fail them: a loop-start test that ignores the repeated step
(5 engine failures), a global change that no longer clears (2 adapter, 9
engine failures).

The hand-written entries in `hooks.s` were disassembled after assembly and
read as written.

## ColdFire port (21 Oct 2026)

Image: native remix `trackpatterns-test` (TRACK PATTERNS + the 14 stock
effects) built in a Modwerk worktree at `c0f513b9` with `make bus`; the six
sites carry their jumps (the rebuild spans padded with `nop`). Emulator
`ot_emu` from the same tree. Project: a copy of the contributor's own,
clock and transport receive off, bank A with `ot_spec.py`: A01 T1 trigs on
steps 1, 5, 9, 13; A03 T1 on 3, 7, 11, 15; both 16 steps at 1X. Script:
NO (the date popup), PLAY, at 4 s a poke of T1's queue (`next[0] = 3`, A03;
no key gesture yet), STOP at 9 s. Watched: T1's counter `0x800064d0`, the
step handler's per-track trig entry `0x46c7a810` (a plain trig writes
`0x1d` at `0x4009d42a`) and `tp_state`.

| | result |
|---|---|
| T1's plain trigs before the change | steps 5, 9, 13, 1, 5, 9, 13 (A01) |
| the queue lands | at 15.97 s, the step T1's counter wraps to step 1: `src[T1] = A03`, `next` cleared |
| T1's plain trigs after it | steps 3, 7, 11, 15, round after round (A03), the global pattern still A01 |

Port evidence only, one track, queued by a poke.

## Gesture, MIDI track, global change (21 Oct 2026)

**Stock first.** On the image above (no gesture site yet, so the keys are
stock): hold TRACK 1, hold PATTERN, press TRIG 3 while playing. Stock
queued A03 for every track (`0x800065c0 <- 2` at `0x400a06dc`) and played
it at the pattern's end. TRACK 1's key state (`0x46c7d8ee + 24 * 0x10`)
went 1 on the press (pc `0x40031936`), then 2 when the PATTERN layer opened
over it (`0x400312e8`), and 0 on the release (`0x4003180c`). So the
combination has no meaning of its own in stock, and the trig still reaches
the PATTERN layer's handler with the TRACK key still marked as held.

**Image:** the same remix rebuilt with the seventh detour (`0x40056b50 ->
tp_pattern_key`) and the bank-aware tick. `tp_state` at `0x40a95f2c`.

**Project** `STEPTPM`: a copy of `STEPTP` plus A02 T1 trigs on 2 and 10
(`ot_spec.py`), and M1's trig mask written into the bank file's MTRA
records (tag + 9, as the TRAC records): A01 M1 on 1 and 9, A03 M1 on 5 and
13. `.work` and `.strd` checksummed and read back.

**Script:** NO, PLAY; at 3 s hold TRACK 1, hold PATTERN, TRIG 3; at 5 s the
MIDI key (MIDI mode), then the same gesture; at 6.8 s the MIDI key again; at
10 s PATTERN + TRIG 2 with no TRACK key held; STOP at 14 s. Watched: the
playing and queued pattern, `0x80000012`, `src`/`next` of T1 and M1, the
engine's global id, the per-track trig entry `0x46c7a810[0]` (a plain trig
writes `0x1d`: at `0x4009d42a` for T1, at `0x4009d0fc` in the MIDI step
handler for M1), the counters `0x800064d0` and `0x800064d8`.

| | result |
|---|---|
| before any change | T1 on steps 1, 5, 9, 13 and M1 on 1, 9 (A01) |
| TRACK 1 + PATTERN + TRIG 3 | `next[T1] = A03` (15.31 s); no global queue written; the toast reads `T1 ▸ A03` over the A01 screen (the display draws `>` as ▸) |
| T1's loop start | `src[T1] = A03` at 15.97 s; then T1 on 3, 7, 11, 15 round after round; M1 still on 1, 9 |
| MIDI mode, the same gesture | `0x80000012 = 1`; `next[M1] = A03` (17.81 s), T1 untouched |
| M1's loop start | `src[M1] = A03` at 19.13 s; then M1 on 5, 13; T1 still on A03 |
| PATTERN + TRIG 2, no TRACK held | stock's global queue (`0x800065c0 = 1`, 22.11 s); A02 plays at 22.27 s; at the next step the engine clears `src` and `next` of T1 and M1 and records A02 |
| after the global change | T1 on 2, 10 (A02's); M1 silent (A02 has no M1 trigs); no stray A03 step at the change |

Not run yet: MIDI out notes (M1 has no channel in the project copy, so
UART0 carried MIDI clock only) and note-offs across a switch; a bank change
under the port (host-tested only); the latched PATTERN (a tap, then TRACK +
TRIG); TRACK pressed after PATTERN; the rebuild path (an edit while a track
is on another pattern); a different length per track; Play Modes built
alongside; cycle counts; any unit.

## Unit build 1 (21 Oct 2026)

`make image REMIX=trackpatterns-test BUILD=1` in the Modwerk scratch
worktree (`c0f513b9`), module source = this repository at `3c581df`, from
the contributor's own OS 1.40C (`.syx` `0a8d2d2b35c2…`, `.bin`
`34695b606eb0…`, Elektron's files). Version string `OCTABAM1`.

| file | SHA-256 |
|---|---|
| `OCTATRACK_OCTABAM1.bin` (card path) | `ec04c849fb85513ba3d9c3863af501233bb61e7edd3387c2cea598506cce2db4` |
| `OCTATRACK_OS1.40C_OCTABAM1.syx` (MIDI path) | `a54d8d1810a198c93f8368b0f151ce69678cd1432e41744b87cc5ced9adad9d0` |
| `mainos_bus.bin` (the OS section the emulator runs) | `906085659919a8b41394f7e4ce253258cccb52418a63d34d6a8555b5e6aa7849` |

The card file's checksum validates (`bin_decode.py`). The gesture run above
repeated on this exact `mainos_bus.bin` gives the same 72 events at the same
times, booted as an MKI (the emulator's default, as every run above) and
with `--mkii`.

### On the unit: MKII, 21 Oct 2026, reported by pgstath

Image `OCTABAM1` above, flashed from the card. Test project as in the plan:
bank A, T1 trigs A01 1/5/9/13, A02 2/10, A03 3/7/11/15; M1 trigs A01
1/9, A03 5/13; all 16 steps. Only what the contributor reported:

| # | test | result |
|---|---|---|
| 1 | stock PATTERN + TRIG 3 switches every track to A03 at the pattern's end | pass |
| 2 | hold TRACK 1, hold PATTERN, TRIG 3: popup `T1 ▸ A03`, screen stays A01, T1 switches at its own loop start | pass |
| 3 | TRACK 1 + PATTERN + TRIG 1: `T1 FOLLOWS`, T1 back on A01 at its loop start | pass |
| 4 | MIDI mode, M1 to A03; note-offs across the switch | not tested |
| 5 | with T1 on A03, PATTERN + TRIG 2 (no TRACK held): A02 at the pattern's end, T1 on A02's trigs | pass |
| 6 | the gesture while stopped, then PLAY | not tested |
| 7 | latched PATTERN, TRACK after PATTERN, chains, GRID REC | not tested |
| 8 | save, power cycle | not tested |

Not reported: how long it ran, other tracks, CPU load, cycles.

## Build 2: the trig LEDs (21 Oct 2026, emulator only)

`make image REMIX=trackpatterns-test BUILD=2`, same tree and OS; adds the
eighth detour `0x4007e9b6 -> tp_led_pass`. `tp_state` at `0x40a96304`.

| file | SHA-256 |
|---|---|
| `OCTATRACK_OCTABAM2.bin` | `53ccd9fe47002bc4a387a1bc343d77fc6f75f5bc5953172d6a45d7c041aa4ef3` |
| `OCTATRACK_OS1.40C_OCTABAM2.syx` | `f4ed7ea63a741b9818e13b4e623ec0c06e61e1520e6c0c7cf1f0aa957dda1ee2` |
| `mainos_bus.bin` | `56372a524128051a1eb5210a97a1cc678b1b03689a4867e47145a2afa3e03851` |

**Stock first** (`STEPTPM`, playing A01): outside GRID REC the trig keys
show only the running light (both LEDs of the playhead's key, moving every
100 ms at 152 BPM); GRID REC shows A01's T1 trigs on keys 1, 5, 9, 13 (first
LEDs) plus second LEDs the project's own data sets; with PATTERN held, A01's
key lights its first LED and A02, A03 their second (patterns with content).

**Run** (`--mkii`, then the same as an MKI): play; the gesture puts T1 on
A03 (lands at 15.97 s); 3 s later GRID REC on for 2 s, off; then TRACK 1 +
PATTERN held for 0.8 s. Watched: the trig LED bytes `0x460ba98c..f` (state
rebuilt every 50 ms), `src[T1]`, GRID REC, PATTERN held.

| | result |
|---|---|
| T1 on A03, outside GRID REC | A03's trigs (LEDs 4, 12, 20, 28: keys 3, 7, 11, 15) on for about 500 ms, off for about 500 ms; the running light moves through both halves |
| T1 on A03, GRID REC | stock's A01 view for about 500 ms, then about 500 ms with only the running light, repeating |
| TRACK 1 + PATTERN held | LEDs 1, 3, 4: A03 (key 3) as the current pattern, A01 and A02 as patterns with content |
| MKI against MKII | the same LED timeline (event times within 1 ms) |
| the gesture run of build 1, repeated (`--mkii`) | the same 72 events and values in the same order, trigs at the same times; the overrides clear 20 ms earlier at the global change (22.27 s, not 22.29 s), because the LED pass now notices the new pattern first |

Not run under the emulator: MIDI mode's LEDs (host-tested only), patterns
longer than 16 steps, the cycle cost of the LED pass.

### On the unit: MKII, 21 Oct 2026, reported by pgstath

Image `OCTABAM2` above (`53ccd9fe…`), the test project and steps as for
build 1, plus the four LED checks. The contributor reported every test
below as passed; nothing more detailed was reported.

| # | test | result |
|---|---|---|
| 1 | stock PATTERN + TRIG 3 switches every track to A03 at the pattern's end | pass |
| 2 | hold TRACK 1, hold PATTERN, TRIG 3: popup `T1 ▸ A03`, screen stays A01, T1 switches at its own loop start | pass |
| 3 | TRACK 1 + PATTERN + TRIG 1: `T1 FOLLOWS`, T1 back on A01 at its loop start | pass |
| 4 | MIDI mode, TRACK 1 + PATTERN + TRIG 3: `M1 ▸ A03`, M1's notes move from 1, 9 to 5, 13 at its loop start, no hanging note across the switch | pass |
| 5 | with T1 on A03, PATTERN + TRIG 2 (no TRACK held): A02 at the pattern's end, T1 on A02's trigs | pass |
| 6 | the gesture while stopped, then PLAY: T1 plays A03 from step 1 | pass |
| 7 | a tapped (latched) PATTERN then TRACK + TRIG, TRACK pressed after PATTERN, a chain (PATTERN + two trigs), GRID REC editing | pass |
| 8 | save, power cycle: the project intact, every track following the global pattern again | pass |
| L1 | T1 on A03, outside GRID REC: A03's trigs blink about once a second, the playhead keeps moving | pass |
| L2 | GRID REC: A01's trigs blink | pass |
| L3 | hold TRACK 1 + PATTERN: A03's key lit as the current pattern | pass |

Not reported: how long it ran, which colour each LED of a pair shows,
other tracks than T1 and M1, CPU load, cycles.

## Build 3: from this tree (21 Oct 2026)

`make image REMIX=trackpatterns BUILD=3` in octabam at `828edcac` with this
module (branch `trackpatterns`), from the contributor's own OS 1.40C (MAIN
OS section `164f3122…`). The eight detours land on the same addresses as
build 2; `tp_state` at `0x40a96304`. The card file's checksum validates.

| file | SHA-256 |
|---|---|
| `OCTATRACK_OCTABAM3.bin` | `a3712dbb2cbefb26895ed42255f5e6e3809379a85bc8297516c5370398200569` |
| `OCTATRACK_OS1.40C_OCTABAM3.syx` | `bc205ce0868578a672939137ff147ebb9bbd17b4eacaa0e1c30fcd6752875ee0` |
| `mainos_bus.bin` | `70b0e299869f576525b33a753d0b5c434ebf789fde08ca68aa1ed7f50e90545c` |

Under this tree's `ot_emu --mkii`, the gesture run and the LED run of build
2 repeated on this exact image: the same 72 events and values in the same
order, every event about 30 ms later (the load ends later); the LEDs as
build 2's (A03's trigs blinking about 500 ms on, 500 ms off outside GRID
REC, A01's in GRID REC, the running light kept; TRACK 1 + PATTERN lighting
LEDs 1, 3, 4).

### On the unit: MKII, 21 Oct 2026, reported by pgstath

Image `OCTABAM3` above (`a3712dbb…`), flashed after build 2's tests, with
the same test project and steps. The contributor reported every test below
as passed; nothing more detailed was reported.

| # | test | result |
|---|---|---|
| 1 | stock PATTERN + TRIG 3 switches every track to A03 at the pattern's end | pass |
| 2 | hold TRACK 1, hold PATTERN, TRIG 3: popup `T1 ▸ A03`, screen stays A01, T1 switches at its own loop start | pass |
| 3 | TRACK 1 + PATTERN + TRIG 1: `T1 FOLLOWS`, T1 back on A01 at its loop start | pass |
| 4 | MIDI mode, TRACK 1 + PATTERN + TRIG 3: `M1 ▸ A03`, M1's notes move from 1, 9 to 5, 13 at its loop start, no hanging note across the switch | pass |
| 5 | with T1 on A03, PATTERN + TRIG 2 (no TRACK held): A02 at the pattern's end, T1 on A02's trigs | pass |
| 6 | the gesture while stopped, then PLAY: T1 plays A03 from step 1 | pass |
| 7 | a tapped (latched) PATTERN then TRACK + TRIG, TRACK pressed after PATTERN, a chain (PATTERN + two trigs), GRID REC editing | pass |
| 8 | save, power cycle: the project intact, every track following the global pattern again | pass |
| L1 | T1 on A03, outside GRID REC: A03's trigs blink about once a second, the playhead keeps moving | pass |
| L2 | GRID REC: A01's trigs blink | pass |
| L3 | hold TRACK 1 + PATTERN: A03's key lit as the current pattern | pass |

Not reported: how long it ran, which colour each LED of a pair shows,
other tracks than T1 and M1, CPU load, cycles.

## Not yet

On the unit: a long run, more tracks at once, other trig modes than
TRACKS. Anywhere: the track's speed from its own pattern, persistence,
cycle counts, memory accounting.
