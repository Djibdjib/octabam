# STEM REC: Yves's six notes of 26 Oct 2026, implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Do all six of Yves's notes of 26 Oct 2026 for STEM REC, and build one image for his unit that checks what the port can't.

**Architecture:** Each note changes one part of `modules/stems/stems.s` and the gate that sees it. Five notes are code: the take folder, the log file, the `.ot` writer, the window's redraw and the double tap of YES. Note 3 is a comparison and a proposal, with no code. Two new detours join the module's three: one in the UI task's loop, one on the main page's YES handler.

**Tech Stack:** ColdFire GNU as (`modules/stems/stems.s`), the remix schema (`modules/stems/manifest.py`), Python gates under the ColdFire port (`tools/verify/verify_stems.py`, `tools/verify/verify_stems_menu.py`), builds in WSL at `/home/yvez/stemsnext`.

**Spec:** [modules/stems/TODO.md](../../../modules/stems/TODO.md), section "Yves's notes of 26 Oct 2026, for the next iteration", with the items it points to (1, 3, 4) for the design.

## Global Constraints

- Branch `stems-next` (Windows worktree `.claude/worktrees/stems-next`, WSL tree `/home/yvez/stemsnext`), on top of PR #927. Git on Windows, builds and gates in WSL; move commits to WSL with `git fetch origin +refs/heads/stems-next:refs/heads/stems-next` in stemrec2, then `git -C /home/yvez/stemsnext reset --hard stems-next` (the WSL tree holds no work of its own).
- Locally run only the gate scripts the change reaches: `verify_stems.py`, `verify_stems_menu.py` (CI's quick reach skips STEM REC's gates). No whole-remix check, no reach, no refhash.
- Long runs: `PYTHONUNBUFFERED=1`, logs under `/home/yvez/xcheck/`, name the log path when the run starts.
- One heavy WSL job at a time (3.8 GB).
- No Elektron byte in the repository. Takes from the unit stay in `C:\Projects\Stem recordings`.
- Never push or post without Yves's OK.
- Docs to the Microsoft style guide: short sentences, every term defined, no spaced dashes. Separate measured from inferred.
- New code follows `stems.s`'s own idiom: the `stems_` prefix, a `|` comment on each line that needs one, interrupts masked around any test-and-set of `stems_state`.

## Review Focus

1. **Two takes in the same minute** with the flat folder: the second gets a number, `<YYMMDD-HHMM>-2`, and overwrites nothing of the first, whichever tracks each one armed (Yves, 27 Oct 2026: a number replaces the `SAME MINUTE` refusal). Test in Task 1.
2. **A card with no `/BRAIN` folder** (BRAIN never ran on it): the log must make `/BRAIN` and `/BRAIN/STEMS`. A failed log write must not change the take's status or its files. Test in Task 2.
3. **A double tap of YES while a take records, or with a track key held, or inside a menu**: it must never stop or cancel a take, and with a track key held it stays stock (`ARM TRK`). Test in Task 5.
4. **The window closed or evicted between two UI messages** (TEMPO and TUNER share its window class 5): the redraw must never draw into a destroyed window. Test in Task 4.
5. **A file with no samples on the card, or a tempo change during a take**: no `.ot` for an empty file; the `.ot` keeps the tempo the take started at. Test in Task 3.

---

### Task 0: The take runs' baseline

The take runs of `verify_stems` fail on main since `5822ebcc` (bisected 21 Oct 2026). Task 1 may fix them. Measure first, so Task 1 can say which.

**Files:** none changed.

- [ ] **Step 1:** In `/home/yvez/stemsnext`: `PYTHONUNBUFFERED=1 .venv/bin/python3 tools/verify/verify_stems.py stems --only=full,stream,all14 > /home/yvez/xcheck/stemsnext-t0.log 2>&1; echo $?`
- [ ] **Step 2:** Record each check's PASS or FAIL and the first failure's detail in the ledger (`.superpowers/sdd/stems-next.md` in the main checkout, ignored). Expected: the take runs FAIL as on main.

### Task 1: The flat take folder (note 6)

Takes go to `<set>/AUDIO/_STEMS/<YYMMDD-HHMM>-<file>.wav`: `-T1.wav` to `-T8.wav`, `-MAIN.wav`, `-CUE.wav`, `-AB.wav`, `-CD.wav`, `-A.wav` to `-D.wav`. One folder, made once. No project in the path or the name. Why `AUDIO/_STEMS` and not `/STEMS`: the unit's file browser roots at the set's audio pool (`<set>/AUDIO`), so a folder at the card's root is out of its reach (inferred from the audio pool's design; the unit check in Task 7 confirms it). Takes already on cards stay where they are.

**Files:**
- Modify: `modules/stems/stems.s` (`fmt_dir`, `fmt_pool`, `fmt_proj`, `fmt_file`, `nm_main` to `nm_d`, `stems_ensure_parents`, `stems_make_folder`, `stems_start`'s exists check, the comments that name the old path)
- Modify: `modules/stems/manifest.py` (the docstring's path), `modules/stems/README.md`
- Test: `tools/verify/verify_stems.py` (`stems_pool`, `new_entries`, `wav_check`, `card_files`' docstring, every caller that joins a take folder and a file name)

**Interfaces:**
- Produces: `stems_path` holds the take's prefix `<set>/AUDIO/_STEMS/<YYMMDD-HHMM>` (no trailing slash). `stems_make_file` appends `-<name>.wav` to it in `stems_fpath`. Tasks 2 and 3 rely on both.
- Produces (Python): `stems_pool(fx) -> str` returns `f"{fx['set']}/AUDIO/_STEMS/"`; `new_entries(files, fixture) -> list[str]` returns the new takes' names (`YYMMDD-HHMM`) from the file names; `take_file(fx, take, name) -> str` returns `f"{stems_pool(fx)}{take}-{name}"`.

- [ ] **Step 1: Update the gate first.** In `verify_stems.py`, change `stems_pool`, add `take_file`, make `new_entries` group files by the prefix before the first `-` after the minute, and route every take-file lookup through `take_file`. Add a run `sameminute` (or extend the run that covers `ERR_EXISTS`: `grep -n "SAME MINUTE\|ERR_EXISTS" tools/verify/verify_stems.py`) with three takes in one minute, the clock held still: take 1 arms T1, take 2 arms T2, take 3 arms T1. Checks: `"same minute: take 2 is <name>-2"`, `"same minute: take 3 is <name>-3"`, `"same minute: take 1's file is unchanged"` (its bytes after take 3 equal its bytes after take 1), and each take's status is `OK`. `new_entries` parses names with `^(\d{6}-\d{4}(?:-\d+)?)-(.+)\.(wav|ot)$`.
- [ ] **Step 2: Run it against the old module** (`--only=stream`). Expected: FAIL, `stream: one new take` finds none under `AUDIO/_STEMS/`.
- [ ] **Step 3: Change the module.** `fmt_pool` = `/AUDIO/_STEMS`; `stems_ensure_parents` makes that one folder; `stems_make_folder` (rename `stems_make_prefix`) writes `<set>/AUDIO/_STEMS/<name>`; `fmt_file` = `-T%d.wav`, the bus names `-MAIN.wav` and so on; the same-minute check becomes a number: a name is taken when any of the 14 possible files (`-T1.wav` to `-D.wav`, whatever this take arms) or its log exists, and then `stems_name` gets `-2`, `-3` and so on up to `-99`, written after the 11 characters of the minute (the clock is read once, so the minute can't change between tries); `ERR_EXISTS` stays only for a minute with 99 takes. Split `stems_make_file` so one routine formats a file by its kind (0 to 13) for both the check and the opens; drop the take folder's `mkdir`. `stems_project` and `stems_proj_ok` go if nothing else calls them (`grep -n`).
- [ ] **Step 4: Build and run:** `make bus REMIX=stems`, then the Task 0 command with log `stemsnext-t1.log`. Expected: every check that passed in Task 0 passes; record whether the take runs that failed now pass.
- [ ] **Step 5: If the take runs still fail,** stop and debug with superpowers:systematic-debugging before Task 2: every later task's gate is a take run.
- [ ] **Step 6: Commit** `stems: one flat folder, AUDIO/_STEMS/<take>-<file>.wav (note 6)`.

### Task 2: The take's log under /BRAIN/STEMS (note 5)

`STATS.TXT` leaves the take folder and becomes `/BRAIN/STEMS/<YYMMDD-HHMM>.TXT`, the same lines. Written as now: from STEM REC's own task, through the file layer's raw routines, after the audio. BRAIN writes its files from its engine task through the buffered API, so the two never share a routine; they share the card's file lock, as STEM REC's WAV writes already do.

**Files:**
- Modify: `modules/stems/stems.s` (`nm_stats`, `stems_stats`' path, a new `fmt_log` `"/BRAIN/STEMS/%s.TXT"`, `/BRAIN` and `/BRAIN/STEMS` made with `stems_mkdir_missing`)
- Modify: `modules/stems/README.md`, `docs/firmware/STEM_REC.md` where it names `STATS.TXT`'s place
- Test: `tools/verify/verify_stems.py` (`stats_check`)

**Interfaces:**
- Consumes: `stems_name` (`YYMMDD-HHMM`, Task 1 keeps it).
- Produces: `stats_check(card_path, tag, ...)` reads `BRAIN/STEMS/<take>.TXT`.

- [ ] **Step 1:** `stats_check` reads the new path; add check `"<tag>: no STATS.TXT beside the WAVs"`. Add a run on a fixture card with no `/BRAIN` (the default fixture has none; check with `card_files`), and one on a card where `/BRAIN/STEMS` is a FILE, which must leave the take's status `OK` and its WAVs whole.
- [ ] **Step 2:** Run `--only=stream`. Expected: FAIL, no log under `BRAIN/STEMS/`.
- [ ] **Step 3:** Change `stems_stats`: build the path in `stems_fpath`, make the two folders, write. A failed log changes nothing else (no `stems_status` write).
- [ ] **Step 4:** Build; run `--only=full,stream,all14` and the new runs. Expected: PASS.
- [ ] **Step 5: Commit** `stems: the take's log in /BRAIN/STEMS/<take>.TXT (note 5)`.

### Task 3: The .ot writer (note 1)

Bring in the online session's writer (`5b175689`, `635b719b`, `7aa20c87` on the fork's `claude/bold-feynman-5y3cli`) and correct it to the firmware read (`docs/firmware/SAMPLE_SAVE.md` section 8):

| field | the fork | now |
|---|---|---|
| tempo | `0x80001814` | `0x8000181c`, the long the stock recorder stores (8.2) |
| gain | 72 for a track or an input, 96 for MAIN and CUE | 72 (+12 dB) for every file, until a take measures otherwise (note 1: MAIN equals the sum of the stems within 7 steps) |
| checksum | the sum of bytes 16 to 829 | the sum of bytes 20 to 829 (8.1); the same while bytes 16 to 19 are zero, which the fork writes |

Each `.ot` sits beside its WAV: `<take>-T1.ot` and so on (Task 1's names, `.wav` swapped for `.ot`).

**Files:**
- Modify: `modules/stems/stems.s` (cherry-picked, then corrected), `modules/stems/README.md`, `docs/firmware/SAMPLE_SAVE.md` (a line on STEM REC's writer as a user of 8.1)
- Test: `tools/verify/verify_stems.py` (`ot_fields`, `ot_check`)

**Interfaces:**
- Consumes: `stems_make_file` (Task 1), `stems_fsmp[]` (per file: its samples on the card).
- Produces: `stems_otfiles` (after `stems_stats`), `stems_ltempo` (the tempo latched at the take's start).

- [ ] **Step 1:** `git cherry-pick 5b175689 635b719b 7aa20c87`; resolve conflicts against Task 1's paths.
- [ ] **Step 2: Correct the gate first.** `ot_fields`' `want_sum` = `sum(data[20:830]) & 0xffff`; `ot_check` wants gain 72 for every file and the tempo from `TEMPOx24` (unchanged); call `ot_check` from `all14` too, so MAIN and CUE are checked. Add the run `tempochange`: poke `0x8000181c` mid-take, and check every `.ot` carries the tempo before the poke. Add the check that a file with no samples on the card has no `.ot` (in `nocard`'s or `cut`'s run, whichever leaves one; else note it untested).
- [ ] **Step 3:** Run `--only=stream,all14`. Expected: FAIL on gain (MAIN 96) and on the tempo word.
- [ ] **Step 4: Correct the module.** `.equ TEMPO_PUB, 0x8000181c`; one `OT_GAIN` = 72; the checksum loop from offset 20.
- [ ] **Step 5:** Build; run `--only=full,stream,all14,tempochange`. Expected: PASS, each `.ot` 832 bytes.
- [ ] **Step 6: Commit** `stems: an .ot beside each WAV, the take's tempo, +12 dB (note 1)`, crediting the online session's two commits in the message.

### Task 4: The window refreshes by itself (note 2)

Two faults. `stems_enter` resets rows 0 and 1 to `REC` and `READY` when the window opens (`47013ec7`). And nothing redraws the window while it's open.

The fix: `stems_enter` leaves the labels alone (it keeps `ui_key = -1`, so the task rewrites them on its next pass). A new detour in the UI task's loop redraws the window when the labels changed. TUNER and SCOPE claim the loop head `0x40056c72`. The new site is the six bytes after that loop's `queue_receive` returns, `0x40056c7c`: `2040 588f 7110` (`movea.l %d0,%a0 / addq.l #4,%sp / mvs.b (%a0),%d0`), no PC-relative operand. It runs once per UI message, as TUNER's site does.

**Files:**
- Modify: `modules/stems/stems.s` (`stems_enter`; new `stems_ui_tick`, `stems_drawn` long), `modules/stems/manifest.py` (`UI_RECV_SITE = 0x40056C7C`, `UI_RECV_STOCK = bytes.fromhex("2040588f7110")`, `Detour(..., "stems_ui_tick", kind="jmp")`)
- Modify: `docs/firmware/STEM_REC.md` section 16.1 (the screen now redraws by itself), `modules/stems/README.md`
- Test: `tools/verify/verify_stems_menu.py`

**Interfaces:**
- Produces: `stems_ui_tick`: replays the three displaced instructions, then, if `stems_win` ≠ 0 and `ui_key` ≠ `stems_drawn`, saves every register it uses, calls `stems_draw`, stores `ui_key` in `stems_drawn`; jumps to `0x40056c82` with `d0` and `a0` as the stock left them.

- [ ] **Step 1: Measure the site's rate.** Under the port, `ot_emu --watch-pc 0x40056c7c` over 10 s of a playing project. Expected: at least 4 hits a second (TUNER's redraw runs about 7 a second from the head). Fewer means the site is wrong: stop and read the loop's message sources.
- [ ] **Step 2: The gate's new checks**, in `verify_stems_menu.py`:
  - `"<model>: opened during a take, the window shows the take"`: arm, play, open STEMS; rows 0 and 1 read `STOP` and `REC mm:ss`, and the screen matches them.
  - `"<model>: the window redraws itself while recording"`: no key for 2 s of emulated time; the status row's pixels change, and the screen equals what a redraw draws (`redraw(p)` then `p.screen()`).
  - `"<model>: a closed window is never drawn"`: close STEMS, let the take run 2 s; `stems_draw` never runs (`--watch-pc` on it, or a counter poke) and nothing faults.
- [ ] **Step 3:** Run against the old module. Expected: the first two FAIL.
- [ ] **Step 4:** Implement; build `stems`, and a scratch remix of `stems` + TUNER + SCOPE (local only, never committed) to show the claims don't collide.
- [ ] **Step 5:** Run `verify_stems_menu.py stems`, then `verify_stems.py stems --only=labels,labelsbehind`. Expected: PASS.
- [ ] **Step 6: Commit** `stems: the window shows the take and redraws itself (note 2)`.

### Task 5: Double tap YES to arm (note 4)

On the main page, outside any menu or dialog, a second YES within 0.4 s of the first arms STEM REC, or starts it at once if the sequencer plays. The stock arm runs on both taps, as now. Scope (Yves): arming when stopped; a double tap while playing starts the take, as the REC row does. A double tap never stops or cancels a take. With a track key held, YES stays stock.

**Files:**
- Modify: `modules/stems/stems.s` (new `stems_yes_key`, `stems_yes_t` long), `modules/stems/manifest.py` (`YES_SITE = 0x4005E4C8`, its stock bytes read from the image with `scripts/disasm.sh emac 0x4005e4c8 16`, a `jmp` detour)
- Modify: `docs/firmware/MAINMENU.md` section 6 (STEM REC's detour on the handler), `modules/stems/README.md`
- Test: `tools/verify/verify_stems_menu.py`

**Interfaces:**
- Consumes: `stems_action` (arms from IDLE; in the UI task, as the handler is), `DTCN3` (132 counts a microsecond).
- Produces: `stems_yes_key`: on a press (the handler's edge argument; read which stack slot from the disassembly) with `0x460d1aec` = 0, `0x800000b8` = 0 and `0x460d1736` = 0, reads `DTCN3`. If `stems_state` is IDLE and the previous such press was under `52,800,000` counts (0.4 s) earlier, calls `stems_action` and clears the stamp; else stores the stamp. Then the stock handler. `STEMS ARMED` through `0x4005a2b8` after the stock's `ARM ALL`, so it's the message left on screen.

- [ ] **Step 1: Read the handler** with `scripts/disasm.sh emac 0x4005e4c8 64` (gate: `0x40003664` must print `msacl`). Record its first instructions, the edge argument's slot and `0x4005a2b8`'s arguments (from the `ARM ALL` call) in the ledger. Check DTCN3 under the port runs at 132 counts per emulated microsecond (the STATS gates' hook times imply it; confirm in `tools/emu/ot_emu` sources).
- [ ] **Step 2: The gate's new checks:** on the main page, stopped: YES, then YES 0.2 s later → `stems_state` = ARMED and the screen's message reads `STEMS ARMED`; one YES → IDLE; two YES 1 s apart → IDLE; a double tap while RECORDING → RECORDING; a double tap with T1 held → IDLE and stock's `ARM TRK`; a double tap with MAIN MENU open → IDLE; a double tap while playing → RECORDING within one frame.
- [ ] **Step 3:** Run against the old module. Expected: the first and last FAIL.
- [ ] **Step 4:** Implement; build.
- [ ] **Step 5:** Run `verify_stems_menu.py stems`. Expected: PASS.
- [ ] **Step 6: Commit** `stems: a double tap of YES arms STEM REC (note 4)`.

### Task 6: STEM REC's load figures against BRAIN's (note 3)

No code. A field by field table, then a proposal for Sam (BRAIN is his module).

What the code shows (27 Oct 2026, `modules/brain/brain.c` `build_load`, `build_card`, `cpu_update`; `stems.s` `stems_stats`):

| STEM REC, per take | BRAIN's PERFORMANCE, live since boot | the same? |
|---|---|---|
| ring peak, the PEAK row | none | no: BRAIN lacks it |
| card writes, total ms, longest | CARD: WRITES (commands, KB), SLOWEST (any command, ms) | overlaps, but per take and STEM REC's own writes against every command since boot |
| card fastest write, rec and save rates | none | no |
| writer longest sleep | none | no |
| hook mean and longest | none: the hook runs in the level-6 transfer chain, so CPU charges it to the task it interrupts | no: BRAIN lacks it |
| hook and the stock frame routine | LOAD: WORST FRAME is the level-5 frame interrupt, another routine | no |
| card UDMA, MWDMA, cluster | none | no |
| the writer task | CPU: not among the 11 named tasks, so OTHER | BRAIN lacks it |

So nothing is dropped from `STATS.TXT`: no field is a duplicate. The proposal for BRAIN: a STEMS row on PERFORMANCE (the ring's fill and the hook's last time, read from `stems_peak` and `stems_st_hmax` when the image has STEM REC), and STEM REC's writer named in CPU (its TCB is `stems_tcb`).

**Files:**
- Modify: `modules/stems/README.md` (the table, under the log's section)
- Create: the proposal draft in the session's scratchpad, not in the repository; posted only with Yves's OK.

- [ ] **Step 1:** Check each row against the code once more (the two files above), and correct the table where it's wrong.
- [ ] **Step 2:** Write the README section and the draft.
- [ ] **Step 3:** `make verify-docs` in WSL. Expected: 0 problems.
- [ ] **Step 4: Commit** `stems: its load figures against BRAIN's PERFORMANCE (note 3)`.

### Task 7: Docs, the TODO and an image for the unit

**Files:**
- Modify: `modules/stems/TODO.md` (each note: done, with its commit; what's left), `modules/stems/FLASH.md` (the unit check list below), `docs/contributing/FAILURE_MODES.md` if a gate run found a new failure mode
- Not modified: `CHANGELOG.md` (it records flashed images; the entry comes after Yves flashes)

- [ ] **Step 1:** Rebase `stems-next` onto `origin/main` (or onto main after #927 merges); rerun `verify_stems.py stems --only=full,stream,all14` and `verify_stems_menu.py stems`. Expected: PASS.
- [ ] **Step 2:** `make image REMIX=stems BUILD=<n>` in WSL; record the `.syx` and `.bin` sha256 in FLASH.md.
- [ ] **Step 3:** The unit check list in FLASH.md, for Yves: the browser reaches `AUDIO/_STEMS` and lists a folder of several takes; a take's files load at the project's tempo and at the stems' level; the window counts while recording, with no key; a double tap of YES arms, and one YES doesn't; `/BRAIN/STEMS/<take>.TXT` is on the card; and item 2 A, a stock `.ot`: record four bars at 123.4 BPM with the stock recorder, save it, copy the `.wav` and `.ot` to `C:\Projects\Stem recordings`.
- [ ] **Step 4:** `make verify-docs`. Expected: 0 problems.
- [ ] **Step 5: Commit** `stems: the notes of 26 Oct done; the unit check list`.
