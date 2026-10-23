#!/usr/bin/env python3
"""A remix in many configurations, stamped in advance, stepped over USB MIDI, measured over USB audio.

One USB cable to the unit and nothing else: program change selects a
layout, MIDI START plays it, the unit's own USB audio stream is the
capture, and LOAD METER (vendor request 0xc0/0x57, tools/hw/load_meter.py)
is the load readout where the image carries it.

    python3 tools/hw/ot_matrix.py plan REMIX [--pairs]
    python3 tools/hw/ot_matrix.py proj SRC DEST_PREFIX REMIX [--pairs] [--pattern A2]
                                  [--stimuli hits,pink,...] [--stim-tracks 1-8]
    python3 tools/hw/ot_matrix.py run PROJECT_DIR LABEL [--midi Octatrack] [--audio Octatrack]
                                  [--pc-channel 1] [--bpm 121] [--play 12] [--tail 3] [--only 0,4-9]
    python3 tools/hw/ot_matrix.py audit PROJECT_DIR      # trigs, locks, odd part records, LFOs, sample paths: none in a fresh project
    python3 tools/hw/ot_matrix.py selftest      # the detectors on synthetic audio; no unit

LAYOUTS. Effect selection cannot be driven over MIDI, but every effect id
and knob byte lives in the project and a pattern selects a part
(tools/hw/ot_ladder.py). A project here holds 32 layouts: 8 banks, and in
each bank patterns 1-4 playing parts 1-4, one layout per part. Program
change `16 * bank + (pattern - 1)` selects one. `plan` prints the layouts a
remix gets; `proj` writes them to DEST_PREFIX_01, _02, ... (32 to a
project), each with OCTABAM_MATRIX.json beside the project files.

  Layout 0 of every project is BASE: no effect of ours, the baseline every
  other layout's level, high band and click count are compared with.
  octabam-core / octabam-inserts: each FX2 effect on all eight tracks
    alone, then each FX1 effect on all eight alone, each at its manifest
    defaults, at its `dear` settings, and in each MODE (with and without
    `dear`). --pairs adds every FX1 x FX2 pair on all eight tracks at `dear`.
  octabam-bus: the bus rig as the ladder's RIG rung has it on FX2 (BusDelay
    on T1, BusVerb on T5, SEND elsewhere), then each FX1 station on all
    eight tracks in the same variants, and the stock DELAY on T8's FX2.

MATERIAL. By default every pattern plays SRC's pattern A2 (--pattern). With
--stimuli the project plays synthetic material instead (tools/hw/ot_stimuli.py):
the WAVs are written beside the project files, FLEX slots 1..N name them
(PATH is the bare file name) with their trim records in markers.work, the
--stim-tracks tracks (default all eight) take them round-robin as looping FLEX
machines, and each pattern is one trig on step 1 of 64 steps at 1X, so at 120
BPM (recorded in OCTABAM_MATRIX.json as `bpm`, which `run` uses) a stimulus
restarts exactly when its 2, 4 or 8 s ends. The stimuli's expected levels and
events are in OCTABAM_STIMULI.json. The project has no .ot attribute files.

SETTINGS. Every project gets the [SETTINGS] and [STATES] keys a run depends on
stamped as text (STORAGE.md section 5): CLOCK and TRANSPORT RECEIVE on, SEND off,
PROGRAM CHANGE RECEIVE on at --pc-channel (default 1) and SEND off, MIDI_TRIG_CH1-8
= channels 1-8, auto channel and soft thru off, per-pattern tempo off, metronome off,
TEMPOx24 = 120 BPM with --stimuli; the project opens on A01 with no mute, solo or cue
mask. --setting KEY=INT stamps any other key (MAIN_LEVEL, MASTER_TRACK, GAIN_AB, ...);
the keys that changed, with their old and new values, are in OCTABAM_MATRIX.json as
`settings_changed`. Audio-level keys not named here keep the template's values.

CLEAN. With --clean, SRC is a project the unit created and nobody edited, and
nothing of the template's content survives except its first pattern and first part
as the container: all 16 banks are rebuilt, every pattern empty but the stamped ones
(trigs and locks cleared, LEN 64 at 1X), every part record the template's with
only the stamped layouts on top, banks I-P and the unused patterns left empty.
`audit PROJECT` lists what is not default (trigs, parameter locks, part records
that differ from bank A's first, LFO depths, sample paths); --clean refuses a
template it finds edited unless --allow-dirty-template. Every project on this
machine's ~/octa fails the audit (they descend from one working project), so
a fresh one has to be created on the unit (PROJECT > NEW) and copied off.
BASE keeps the bus remix's SEND on FX2 at level 0 rather than id 0 (an FX2 stored as 0
gets no page from the firmware, ot_project.make_clean_project).

THE RUN. For each layout: STOP, program change, the page-1 CCs of the
layout's modules asserted over MIDI (the ladder's rule), START with a
continuous 24 ppqn clock, `--play` s, STOP, `--tail` s. One CoreAudio input
stream stays open for the whole run (a stream opened and closed per layout
is the churn usb_probe.py chases); each layout's samples are analysed and
dropped, and kept as a WAV only when flagged. LOAD METER is polled every
0.25 s through the play phase.

FLAGS per layout, against BASE of the same project, all thresholds initial
and not validated on a unit (constants at the top of this file):

  CRASH     no channel above -80 dBFS in the first 2 s of play where BASE had audio:
            the sequencer stuck on step 1. The run stops: only a power cycle clears it.
  FREEZE    every channel at or below -80 dBFS for 1 s or more at times BASE had audio;
            reported with its second; the transport is restarted and the run goes on.
  CLICKS    discontinuity events (|second difference| far above its neighbourhood's
            median) more than BASE's by CLICK_EXTRA and CLICK_RATIO.
  STATIC    8-16 kHz power up STATIC_DB or more over BASE's.
  LEVEL     rms differs from BASE's by LEVEL_DB or more.
  CLIP      samples at full scale.
  LOAD      LOAD METER's frame-interrupt share or a DSP core's busy/period above LOAD_FRAC.

What it cannot see: what the material is (a gap in a loop looks like a
dropout only when BASE has none at that time), a fault that BASE has too,
anything the USB stream hides (the module's rate and fill are in
usb_counters.py), and the unit's analog outputs.
"""
import argparse
import json
import pathlib
import re
import shutil
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent)); import toolpath  # noqa: E402,F401

DEAD_DBFS = -80.0
WIN_S = 0.25
FREEZE_S = 1.0
CRASH_S = 2.0
CLICK_EXTRA, CLICK_RATIO = 10, 3.0
CLICK_SKIP_S = 0.2        # the segment's first samples are a cut, not a click (all 255 'clicks' of layout 2, 24 Oct 2026, were in the first 12 ms)
SETTLE_DBFS, SETTLE_MAX_S = -70.0, 15.0   # wait for the previous layout's tail to fade before the next segment
STATIC_DB, LEVEL_DB = 6.0, 3.0
LOAD_FRAC = 0.90
BANKS = "ABCDEFGH"
PER_PROJECT = 32


# ---------------------------------------------------------------------------
# layouts
# ---------------------------------------------------------------------------
def _variants(m):
    """[(label, knobs)]: the manifest defaults, `dear`, and each MODE, with and without `dear`."""
    out = [("def", {})]
    dear = dict(getattr(m, "dear", None) or {})
    if dear:
        out.append(("dear", dear))
    slot = getattr(m, "mode_slot", None)
    if slot is not None:
        for k in range(m.params[slot].count or 0):
            out.append((f"mode{k}", {slot: k}))
            if dear:
                out.append((f"mode{k}+dear", {**dear, slot: k}))
    return out


def _unique(m, variants):
    """Drop variants whose stamped bytes are the same as an earlier one's."""
    import ot_project as P
    seen, out = set(), []
    for label, knobs in variants:
        b = P.module_defaults(m, knobs)
        if b not in seen:
            seen.add(b)
            out.append((label, knobs))
    return out


def layouts(remix_name, pairs=False):
    """-> [(name, kind, {track: (fx1 spec, fx2 spec)})]; a spec is (module key, knobs) or None."""
    import ot_ladder as L
    from remix import registry, stock
    remix, mods = registry.remix(remix_name), registry.modules()
    is_bus = "REVERB SERVER" in remix.modules
    # an FX2 stored as 0 gets no page from the firmware and SEND reads a stale word (ot_project.make_clean_project)
    none = {t: (None, L._sends({}).get(t)) for t in range(1, 9)} if "SEND" in remix.modules else \
        {t: (None, None) for t in range(1, 9)}
    out = [("BASE", "base", none)]

    fx1_keys = remix.fx1 or tuple(k for k in stock.p_spans("A") if mods[k].menu.fx2_id in stock.fx1_ids())
    if is_bus:
        rig = L._sends(L._RIG_AUX, verb=True, delay=True)
        fx2_keys = []
    else:
        fx2_keys = [k for k in remix.modules if mods.get(k) is not None and mods[k].menu is not None
                    and k not in remix.hidden]
        rig = {}

    def all_tracks(fx1=None, fx2=None):
        return {t: (fx1, fx2 if fx2 is not None else rig.get(t)) for t in range(1, 9)}

    if is_bus:
        out.append(("RIG", "base", all_tracks()))
        if "DELAY" in remix.modules:
            out.append(("RIG + T8 DELAY", "fx2", {**all_tracks(), 8: (None, ("DELAY", {}))}))
    for k in fx2_keys:
        for label, knobs in _unique(mods[k], _variants(mods[k])):
            out.append((f"{k} FX2 {label}", "fx2", all_tracks(fx2=(k, knobs))))
    for k in fx1_keys:
        for label, knobs in _unique(mods[k], _variants(mods[k])):
            out.append((f"{k} FX1 {label}", "fx1", all_tracks(fx1=(k, knobs))))
    if pairs and not is_bus:
        for k1 in fx1_keys:
            for k2 in fx2_keys:
                d1, d2 = dict(getattr(mods[k1], "dear", None) or {}), dict(getattr(mods[k2], "dear", None) or {})
                out.append((f"{k1} FX1 + {k2} FX2 dear", "pair", all_tracks(fx1=(k1, d1), fx2=(k2, d2))))
    return out


def _spec_text(spec):
    return "-" if spec is None else spec[0] + (f" {spec[1]}" if spec[1] else "")


def cmd_plan(a):
    lay = layouts(a.remix, a.pairs)
    n = len(lay)
    print(f"{a.remix}: {n} layouts, {-(-n // PER_PROJECT)} project(s) of up to {PER_PROJECT}; "
          f"~{n * (a.play + a.tail + 4) / 60:.0f} min at --play {a.play:g} --tail {a.tail:g}")
    for i, (name, kind, lo) in enumerate(lay):
        print(f"  {i:3d}  {kind:5s} {name}")


# ---------------------------------------------------------------------------
# proj
# ---------------------------------------------------------------------------
def _program(i):
    """Layout slot i (0..31) -> (bank number 1..8, pattern 1..4, program change)."""
    bank, k = divmod(i, 4)
    return bank + 1, k + 1, bank * 16 + k


# ---------------------------------------------------------------------------
# stimuli: samples, sample slots and trigs written into the project
# ---------------------------------------------------------------------------
STIM_BPM = 120            # 64 sixteenth steps = 8 s, a whole number of every stimulus' length
STIM_LEN, STIM_SCALE = 64, 2                       # LEN 64, SCALE 1X (ot_project.SCALE_NAMES)
SLOT_REC = 784                                     # a markers.work record; FLEX slot n is record n - 1 from 0x16


def stim_assign(names, tracks):
    """[(track 0..7, slot 1..N)]: the stimuli round-robin over `tracks` (1-based)."""
    return [(t - 1, 1 + i % len(names)) for i, t in enumerate(tracks)]


def _stim_text(dest, names, frames):
    """FLEX slots 1..N in project.work / .strd name the stimuli (PATH beside the project files)."""
    import re
    blocks = b""
    for i, n in enumerate(names):
        bars = frames[n] * 100 * STIM_BPM // (FS_STIM * 60 * 4)
        blocks += (f"[SAMPLE]\r\nTYPE=FLEX\r\nSLOT={i + 1:03d}\r\nPATH={n}.wav\r\nTRIM_BARSx100={bars}"
                   f"\r\nLOOP_BARSx100={bars}\r\nBPMx24={STIM_BPM * 24}\r\nTSMODE=0\r\nLOOPMODE=1\r\nGAIN=48"
                   f"\r\nTRIGQUANTIZATION=-1\r\n[/SAMPLE]\r\n\r\n").encode()
    used = {f"{i + 1:03d}".encode() for i in range(len(names))}
    for path in (dest / "project.work", dest / "project.strd"):
        if not path.exists():
            continue
        raw = path.read_bytes()
        raw = re.sub(rb"\[SAMPLE\]\r?\nTYPE=FLEX\r?\nSLOT=(\d+)\r?\n.*?\[/SAMPLE\]\r?\n\r?\n",
                     lambda m: b"" if m.group(1) in used else m.group(0), raw, flags=re.S)
        at = raw.find(b"[SAMPLE]")
        if at < 0:
            sys.exit(f"{path}: no [SAMPLE] section to put the stimuli before")
        path.write_bytes(raw[:at] + blocks + raw[at:])


def _stim_markers(dest, names, frames):
    import struct
    for path in (dest / "markers.work", dest / "markers.strd"):
        if not path.exists():
            continue
        data = bytearray(path.read_bytes())
        for i, n in enumerate(names):
            off = 0x16 + i * SLOT_REC
            data[off:off + SLOT_REC] = struct.pack(">III", 0, frames[n], 0) + bytes(SLOT_REC - 12)
        data[-2:] = (sum(data[0x10:-2]) & 0xFFFF).to_bytes(2, "big")
        path.write_bytes(data)


FS_STIM = 44100


def write_stimuli(dest, names):
    """The WAVs beside the project files, their FLEX slots and trim records; -> {name: frames}."""
    import ot_stimuli as S
    frames = {}
    for n in names:
        if n not in S.STIMULI:
            sys.exit(f"no stimulus {n!r}; have {', '.join(S.STIMULI)}")
        q, extra = S.render(n)
        S.write_wav(dest / f"{n}.wav", q)
        frames[n] = len(q)
    _stim_text(dest, names, frames)
    _stim_markers(dest, names, frames)
    (dest / "OCTABAM_STIMULI.json").write_text(json.dumps(
        {n: S.describe(n, *S.render(n)) for n in names}, indent=1))
    return frames


def stim_part(data, off, assign):
    """One part record: the assigned tracks are FLEX machines on their slot, looping, no stretch, neutral pitch."""
    for t, slot in assign:
        data[off + 0x02b + t] = 1                       # machine type FLEX (ot_project.MTYPE_OFF)
        data[off + 0x2d3 + t * 5 + 1] = slot - 1        # the track's flex slot
        data[off + 0x01b + t * 2] = 55                  # mix headroom, as stress_project.py
        setup, vals = off + 0x1e3 + t * 30 + 6, off + 0x033 + t * 30 + 6
        data[setup] = 1                                 # LOOP
        data[setup + 4] = 0                             # TSTR off
        data[vals] = 64                                 # PTCH neutral
        data[vals + 3] = 127                            # RATE forward


def stim_pattern(data, pat, assign):
    """Pattern `pat` (0-based): no trigs or locks, then step 1 on the assigned tracks, LEN 64 at 1X."""
    import ot_project as P
    for t in range(8):
        off = P.trac_off(pat, t)
        data[off:off + 64] = bytes(64)
        data[off + 0x59:off + 0x59 + 64 * 32] = bytes([0xff]) * (64 * 32)
    for t, _slot in assign:
        data[P.trac_off(pat, t) + 7] |= 1               # mask 0, step 1
    tail = P.PTRN0 + pat * P.PTRN_FSTRIDE + P.PTRN_FSTRIDE - 11
    data[tail + 2], data[tail + 3] = STIM_LEN, STIM_SCALE


# ---------------------------------------------------------------------------
# project settings: the MIDI setup and the start state, written as text
# ---------------------------------------------------------------------------
def test_settings(pc_channel=1):
    """[SETTINGS] keys a run depends on (docs/firmware/STORAGE.md section 5). Channel keys are 0-based."""
    s = {"MIDI_CLOCK_RECEIVE": 1, "MIDI_TRANSPORT_RECEIVE": 1,
         "MIDI_CLOCK_SEND": 0, "MIDI_TRANSPORT_SEND": 0,
         "MIDI_PROGRAM_CHANGE_RECEIVE": 1, "MIDI_PROGRAM_CHANGE_RECEIVE_CH": pc_channel - 1,
         "MIDI_PROGRAM_CHANGE_SEND": 0,
         "MIDI_AUTO_CHANNEL": -1, "MIDI_SOFT_THRU": 0,
         "PATTERN_TEMPO_ENABLED": 0, "METRONOME_ENABLED": 0}
    s.update({f"MIDI_TRIG_CH{t}": t - 1 for t in range(1, 9)})
    return s


# [STATES]: the project opens on A01 with nothing muted, soloed or cued.
TEST_STATES = {"BANK": 0, "PATTERN": 0, "PART": 0, "TRACK": 0, "ARRANGEMENT": 0, "ARRANGEMENT_MODE": 0,
               "TRACK_MUTE_MASK": 0, "TRACK_SOLO_MASK": 0, "TRACK_CUE_MASK": 0}


def stamp_text(dest, settings, states):
    """Set keys inside [SETTINGS] and [STATES] of project.work and project.strd.
    -> {key: [old, new]} for the keys that changed. A key the file does not have is an error."""
    import re
    changed = {}
    for name in ("project.work", "project.strd"):
        path = dest / name
        if not path.exists():
            continue
        raw = path.read_bytes().decode("latin1")
        for block, kv in (("SETTINGS", settings), ("STATES", states)):
            m = re.search(rf"\[{block}\]\r?\n(.*?)\[/{block}\]", raw, re.S)
            if not m:
                sys.exit(f"{path}: no [{block}] block")
            body = m.group(1)
            for key, val in kv.items():
                hit = re.search(rf"^{re.escape(key)}=(-?\d+)(\r?)$", body, re.M)
                if not hit:
                    sys.exit(f"{path}: no {key}= line in [{block}]")
                if hit.group(1) != str(val):
                    changed.setdefault(key, [int(hit.group(1)), int(val)])
                body = body[:hit.start()] + f"{key}={val}{hit.group(2)}" + body[hit.end():]
            raw = raw[:m.start(1)] + body + raw[m.end(1):]
        path.write_bytes(raw.encode("latin1"))
    return changed


# ---------------------------------------------------------------------------
# audit: what in a project is not a fresh unit-created one
# ---------------------------------------------------------------------------
def audit(src):
    """-> dict of findings for the project at `src`: trigs and locks anywhere, part records that differ from
    bank A part 1, LFO depths, project-local sample paths. A project the unit created and nobody edited has none."""
    import ot_project as P
    import ot_bank as B
    import ot_ladder as L
    src = pathlib.Path(src)
    out = {"trigs": [], "locks": [], "parts": [], "lfo": [], "samples": 0, "banks": 0}
    ref = None
    for n in range(1, 17):
        f = src / f"bank{n:02d}.work"
        if not f.is_file():
            continue
        d = f.read_bytes()
        B.check_tags(d)
        out["banks"] += 1
        for pt in range(16):
            for t in range(8):
                off = P.trac_off(pt, t)
                if any(d[off:off + 64]):
                    out["trigs"].append(f"{BANKS[(n - 1) % 8] if n <= 8 else n}{pt + 1:02d} T{t + 1}")
                if any(x != 0xff for x in d[off + 0x59:off + 0x59 + 64 * 32]):
                    out["locks"].append(f"{n}:{pt + 1} T{t + 1}")
        for r in range(P.NPARTS_ALL):
            off = P.PART_BASE + r * P.PART_STRIDE
            rec = bytearray(d[off:off + P.PART_STRIDE])
            rec[L.PART_INDEX_OFF] = 0
            if ref is None:
                ref = bytes(rec)
            elif bytes(rec) != ref:
                out["parts"].append(f"bank {n} record {r + 1}")
            for t in range(8):
                if any(d[off + P.LFO_P1_OFF + t * 24 + 3:off + P.LFO_P1_OFF + t * 24 + 6]):
                    out["lfo"].append(f"bank {n} record {r + 1} T{t + 1}")
    import re
    txt = (src / "project.work").read_bytes().decode("latin1")
    out["samples"] = len([m for m in re.findall(r"^PATH=(.+?)\r?$", txt, re.M) if m.strip()])
    return out


def fresh_findings(a):
    f = []
    for key, what in (("trigs", "tracks with trigs"), ("locks", "tracks with parameter locks"),
                      ("parts", "part records differing from bank A's first"), ("lfo", "tracks with an LFO depth")):
        if a[key]:
            f.append(f"{len(a[key])} {what} (first: {a[key][0]})")
    if a["samples"]:
        f.append(f"{a['samples']} sample slots with a file path")
    return f


def cmd_audit(a):
    r = audit(a.project)
    f = fresh_findings(r)
    print(f"{a.project}: {r['banks']} banks")
    for line in f or ["nothing: every pattern empty, every part record equal, no LFO, no sample path"]:
        print("  " + line)
    return 1 if f else 0


def make_project(src, dest, remix_name, chunk, pattern="A2", stimuli=None, stim_tracks=range(1, 9),
                 pc_channel=1, extra_settings=None, clean=False, allow_dirty=False):
    """Copy SRC to DEST and write `chunk` (a list of layouts, at most 32; the rest BASE).
    With `stimuli` (names from ot_stimuli) the tracks in `stim_tracks` play them on FLEX slots 1..N, one trig
    on step 1 of a 64-step pattern, instead of SRC's own pattern content.
    `clean`: SRC is a project the unit created and nobody edited. All 16 banks are rebuilt from its first
    pattern and first part: every pattern empty but the ones stamped, every part record the template's with only
    the stamped layouts on top. Refused unless `audit` finds SRC fresh (`allow_dirty` overrides)."""
    import ot_ladder as L
    import ot_project as P
    from remix import registry
    src, dest = pathlib.Path(src), pathlib.Path(dest)
    if dest.exists():
        sys.exit(f"{dest} exists -- refusing to overwrite. Pick a new name.")
    if not (src / "project.work").is_file():
        sys.exit(f"{src} is not an Octatrack project directory")
    remix, mods = registry.remix(remix_name), registry.modules()
    if clean:
        if not stimuli:
            sys.exit("--clean needs --stimuli: a clean project has nothing else to play")
        found = fresh_findings(audit(src))
        if found and not allow_dirty:
            sys.exit(f"{src} is not a fresh project:\n  " + "\n  ".join(found)
                     + "\nCreate a new project on the unit and use that, or pass --allow-dirty-template.")
        pattern = "A1"
    sbank, spat = L._pattern_ref(pattern)
    sdata = (src / f"bank{sbank:02d}.work").read_bytes()
    p0 = P.PTRN0 + (spat - 1) * P.PTRN_FSTRIDE
    ptrn = sdata[p0:p0 + P.PTRN_FSTRIDE]
    if ptrn[:4] != b"PTRN":
        sys.exit(f"bank{sbank:02d} pattern {spat}: no PTRN chunk at {p0:#x}")
    spart = ptrn[P.PTRN_FSTRIDE - 5]
    if spart > 3:
        sys.exit(f"pattern {pattern} names part {spart}, not 0..3")
    part_cur = sdata[P.PART_BASE + spart * P.PART_STRIDE:][:P.PART_STRIDE]
    part_sav = sdata[P.PART_BASE + (spart + 4) * P.PART_STRIDE:][:P.PART_STRIDE]

    base = chunk[0] if chunk and chunk[0][0] == "BASE" else None
    slots = list(chunk) + [base or chunk[0]] * (PER_PROJECT - len(chunk))
    plans = []
    for name, kind, lo in slots:
        plans.append([(t, L._slot_bytes(f1, remix, mods), L._slot_bytes(f2, remix, mods))
                      for t, (f1, f2) in lo.items()])

    shutil.copytree(src, dest)
    settings = test_settings(pc_channel)
    if stimuli:
        settings["TEMPOx24"] = STIM_BPM * 24
    settings.update(extra_settings or {})
    changed = stamp_text(dest, settings, TEST_STATES)
    assign = []
    if stimuli:
        write_stimuli(dest, stimuli)
        assign = stim_assign(stimuli, list(stim_tracks))
    for b in range(16 if clean else 8):
        num = b + 1
        used = b < 8                                  # program change reaches banks A-H
        bank_plans = plans[b * 4:b * 4 + 4] if used else [[], [], [], []]

        def mut(data, bank_plans=bank_plans, used=used):
            for j in range(16 if clean else 4):      # pattern j+1 plays part j+1 (j < 4)
                d0 = P.PTRN0 + j * P.PTRN_FSTRIDE
                data[d0:d0 + P.PTRN_FSTRIDE] = ptrn
                data[d0 + P.PTRN_FSTRIDE - 5] = j if j < 4 else 0
                if clean:
                    stim_pattern(data, j, assign if used and j < 4 else [])
                elif assign:
                    stim_pattern(data, j, assign)
            for p in range(P.NPARTS_ALL):
                off = P.PART_BASE + p * P.PART_STRIDE
                data[off:off + P.PART_STRIDE] = part_cur if p < 4 else part_sav
                data[off + L.PART_INDEX_OFF] = p % 4      # a record's own index (FAILURE_MODES "PARSE ERROR")
                if assign and used:
                    stim_part(data, off, assign)
                for t, (id1, v1), (id2, v2) in bank_plans[p % 4]:
                    i = t - 1
                    data[off + P.FX1_OFF + i] = id1
                    data[off + P.FX2_OFF + i] = id2
                    a = off + P.P1_OFF + i * P.TRACK_STRIDE
                    bb = off + P.P2_OFF + i * P.P2_STRIDE
                    data[a:a + 6] = v1[:6]; data[a + 6:a + 12] = v2[:6]
                    data[bb:bb + 6] = v1[6:]; data[bb + 6:bb + 12] = v2[6:]
            if used:
                for p in range(4):
                    o = len(data) - 2 - 4 * 7 + p * 7
                    field = f"{b * 4 + p:03d}".encode("latin1")
                    data[o:o + 7] = field + b"\x00" * (7 - len(field))

        P._bank_write(dest, num, mut, guard=False)
        data = (dest / f"bank{num:02d}.work").read_bytes()
        if int.from_bytes(data[-2:], "big") != (sum(data[0x10:-2]) & 0xFFFF):
            sys.exit(f"bank{num:02d}: checksum did not take -- do NOT use this")
        for j in range(16 if clean else 4):
            d0 = P.PTRN0 + j * P.PTRN_FSTRIDE
            if data[d0:d0 + 4] != b"PTRN" or data[d0 + P.PTRN_FSTRIDE - 5] != (j if j < 4 else 0):
                sys.exit(f"bank{num:02d} pattern {j + 1}: read-back disagrees")
        for p in range(P.NPARTS_ALL):
            off = P.PART_BASE + p * P.PART_STRIDE
            if data[off:off + 4] != b"PART" or data[off + L.PART_INDEX_OFF] != p % 4:
                sys.exit(f"bank{num:02d} part {p + 1}: record header/index read-back disagrees")
            for t, (id1, v1), (id2, v2) in bank_plans[p % 4]:
                i = t - 1
                a = off + P.P1_OFF + i * P.TRACK_STRIDE
                bb = off + P.P2_OFF + i * P.P2_STRIDE
                got = (data[off + P.FX1_OFF + i], data[off + P.FX2_OFF + i],
                       bytes(data[a:a + 12]), bytes(data[bb:bb + 12]))
                if got != (id1, id2, v1[:6] + v2[:6], v1[6:] + v2[6:]):
                    sys.exit(f"bank{num:02d} part {p + 1} T{t}: read-back disagrees")
    P.write_stored(dest)
    entries = []
    for i, (name, kind, lo) in enumerate(chunk):
        bank, pat, prog = _program(i)
        entries.append({"slot": i, "bank": BANKS[bank - 1], "pattern": pat, "program": prog, "name": name,
                        "kind": kind, "layout": {str(t): [_spec_text(f1), _spec_text(f2)] for t, (f1, f2) in lo.items()}})
    (dest / "OCTABAM_MATRIX.json").write_text(json.dumps(
        {"remix": remix_name, "layouts": entries, "bpm": STIM_BPM if stimuli else None,
         "pc_channel": pc_channel, "settings_changed": changed, "clean": clean,
         "stimuli": {n: [t + 1 for t, sl in assign if sl == i + 1] for i, n in enumerate(stimuli)} if stimuli else None},
        indent=1))
    return len(entries)


def cmd_proj(a):
    lay = layouts(a.remix, a.pairs)
    base, rest = lay[0], lay[1:]
    stimuli = [x for x in a.stimuli.split(",") if x] if a.stimuli else None
    tracks = _span(a.stim_tracks)
    extra = {}
    for kv in a.setting:
        key, _, val = kv.partition("=")
        if not re.fullmatch(r"-?\d+", val):
            sys.exit(f"--setting {kv!r} is KEY=INTEGER")
        extra[key] = int(val)
    per = PER_PROJECT - 1                     # BASE takes slot 0 of every project
    n = 0
    for k in range(0, len(rest), per):
        dest = f"{a.dest}_{k // per + 1:02d}"
        n += make_project(a.src, dest, a.remix, [base] + rest[k:k + per], a.pattern, stimuli, tracks,
                          a.pc_channel, extra, a.clean, a.allow_dirty_template) - 1
        print(f"{dest}: {len(rest[k:k + per]) + 1} layouts (slot 0 BASE)")
    print(f"{n} layouts in {-(-len(rest) // per)} project(s); "
          + (f"clean rebuild from {a.src}" if a.clean else f"material {a.src} {a.pattern}"))


# ---------------------------------------------------------------------------
# analysis (numpy; the selftest runs it on synthetic audio)
# ---------------------------------------------------------------------------
def _db(x):
    import numpy as np
    return 20.0 * np.log10(max(float(x), 1e-12))


def window_alive(x, fs):
    """Per WIN_S window: any channel above DEAD_DBFS."""
    import numpy as np
    w = int(WIN_S * fs)
    n = len(x) // w
    rms = np.sqrt((x[:n * w].reshape(n, w, -1) ** 2).mean(axis=1))        # (windows, channels)
    return (20 * np.log10(np.maximum(rms, 1e-12)) > DEAD_DBFS).any(axis=1)


def click_events(x, fs):
    """Per channel: samples whose second difference is far above their neighbourhood's median."""
    import numpy as np
    out = []
    blk = 512
    for c in range(x.shape[1]):
        d2 = np.abs(np.diff(x[:, c], 2))
        n = len(d2) // blk
        if n < 3:
            out.append(0)
            continue
        b = d2[:n * blk].reshape(n, blk)
        med = np.median(b, axis=1)
        ref = np.maximum.reduce([np.roll(med, 1), med, np.roll(med, -1)])
        ref[0], ref[-1] = med[0], med[-1]
        thr = np.maximum(1e-3, 50 * ref)[:, None]
        out.append(int((b > thr).sum()))
    return out


def hf_power_db(x, fs):
    """8-16 kHz power of all channels summed, dB."""
    import numpy as np
    n = 8192
    win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1 / fs)
    sel = (f >= 8000) & (f < min(16000, fs / 2))
    acc, k = 0.0, 0
    for c in range(x.shape[1]):
        for i in range(0, len(x) - n, n):
            acc += (np.abs(np.fft.rfft(x[i:i + n, c] * win)) ** 2)[sel].mean()
            k += 1
    return 10 * np.log10(max(acc / max(k, 1), 1e-30))


def measure(x, fs, play_s):
    """x[:, channels], the play phase first, then the tail. -> metrics dict."""
    import numpy as np
    x = x[:, np.abs(x).max(axis=0) > 0] if (np.abs(x).max(axis=0) > 0).any() else x
    play = x[:int(play_s * fs)]
    return {"rms_db": _db(np.sqrt(np.mean(play ** 2))), "peak_db": _db(np.abs(play).max()),
            "dc": float(np.abs(play.mean(axis=0)).max()), "clip": int((np.abs(play) >= 0.9999).sum()),
            "clicks": int(sum(click_events(play[int(CLICK_SKIP_S * fs):], fs))), "hf_db": float(hf_power_db(play, fs)),
            "alive": window_alive(play, fs).tolist(), "channels": int(x.shape[1])}


def runs(mask):
    """[(start, length)] of True runs."""
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            out.append((i, j - i))
            i = j
        else:
            i += 1
    return out


def judge(m, base, load=None):
    """Flags for measurement m against the project's BASE measurement."""
    flags = []
    bal, al = base["alive"], m["alive"]
    n = min(len(bal), len(al))
    need = int(CRASH_S / WIN_S)
    if n >= need and any(bal[:need]) and not any(al[:need]):
        return ["CRASH"], None
    dead = [not al[i] and bal[i] for i in range(n)]
    fr = [(s, l) for s, l in runs(dead) if l * WIN_S >= FREEZE_S]
    if fr:
        flags.append("FREEZE")
    if m["clicks"] - base["clicks"] > CLICK_EXTRA and m["clicks"] > CLICK_RATIO * max(base["clicks"], 1):
        flags.append("CLICKS")
    if m["hf_db"] - base["hf_db"] >= STATIC_DB:
        flags.append("STATIC")
    if abs(m["rms_db"] - base["rms_db"]) >= LEVEL_DB:
        flags.append("LEVEL")
    if m["clip"]:
        flags.append("CLIP")
    if load and load.get("windows"):
        top = max(load["cf_share_max"], load["dsp_core0_max"], load["dsp_core1_max"])
        if top >= LOAD_FRAC:
            flags.append("LOAD")
    return flags, ([round(s * WIN_S, 2) for s, _ in fr] or None)


def cmd_selftest(_a):
    import numpy as np
    fs = 44100
    rng = np.random.default_rng(1)
    t = np.arange(fs * 12) / fs
    env = np.exp(-((t * 2) % 1) * 6)                      # a hit every 0.5 s
    base_sig = (0.3 * np.sin(2 * np.pi * 220 * t) * env + 1e-4 * rng.standard_normal(len(t))).astype(np.float32)
    mk = lambda s: np.stack([s, s], axis=1)               # noqa: E731
    base = measure(mk(base_sig), fs, 12)
    fails = []

    def expect(what, got, want):
        ok = got == want
        print(f"  [{'ok' if ok else 'FAIL'}] {what}: {got}")
        if not ok:
            fails.append(what)

    expect("clean copy of BASE has no flags", judge(measure(mk(base_sig.copy()), fs, 12), base)[0], [])
    s = base_sig.copy()
    for i in range(20):
        s[fs + i * 4000] += 0.4                            # a step click
    expect("20 injected clicks", "CLICKS" in judge(measure(mk(s), fs, 12), base)[0], True)
    s = base_sig + (0.02 * rng.standard_normal(len(t))).astype(np.float32)
    expect("added broadband noise", "STATIC" in judge(measure(mk(s), fs, 12), base)[0], True)
    s = base_sig.copy(); s[5 * fs:7 * fs] = 0
    f, at = judge(measure(mk(s), fs, 12), base)
    expect("a 2 s dropout is a FREEZE at 5 s", ("FREEZE" in f, at), (True, [5.0]))
    s = base_sig * 0.2
    expect("14 dB quieter", "LEVEL" in judge(measure(mk(s), fs, 12), base)[0], True)
    s = np.zeros_like(base_sig)
    expect("silence from the start is a CRASH", judge(measure(mk(s), fs, 12), base)[0], ["CRASH"])
    s = np.clip(base_sig * 4, -1, 1)
    expect("clipping", "CLIP" in judge(measure(mk(s), fs, 12), base)[0], True)
    print(f"selftest: {'OK' if not fails else str(len(fails)) + ' FAILED'}")
    return 1 if fails else 0


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def _span(text):
    """'1-4,7' -> [1, 2, 3, 4, 7]."""
    out = []
    for part in text.split(","):
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not m:
            sys.exit(f"{part!r} is not N or N-M")
        out += range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1)
    return out


def parse_only(s, n):
    if not s:
        return list(range(n))
    out = []
    for part in s.split(","):
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not m:
            sys.exit(f"--only: {part!r} is not N or N-M")
        out += range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1)
    return [i for i in out if i < n]


class LmFeed:
    """LOAD METER readings with their times: in this process when libusb loads, else from
    `load_meter.py --jsonl` under /usr/local/bin/python3 (the Intel Homebrew libusb does not load in an arm64 python)."""

    def __init__(self):
        self.rows, self.proc, self.dev, self.err = [], None, None, None
        try:
            import load_meter
            self.lm = load_meter
            self.dev = load_meter.libusb_device()
            load_meter.read(self.dev)
            return
        except (SystemExit, Exception) as e:  # noqa: BLE001
            self.err = str(e) or type(e).__name__
        import os
        import subprocess
        if os.path.exists("/usr/local/bin/python3"):
            self.proc = subprocess.Popen(["/usr/local/bin/python3", str(HERE / "load_meter.py"), "--jsonl", "--interval", "0.25"],
                                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.proc.stdout:
            try:
                self.rows.append(json.loads(line))
            except ValueError:
                pass

    def ok(self):
        return self.dev is not None or self.proc is not None

    def window(self, t0, t1):
        """Decoded readings taken between wall times t0 and t1."""
        if self.proc is not None:
            return [r for r in list(self.rows) if t0 <= r["t"] <= t1]
        return []

    def poll(self):
        """In-process mode: take a reading now (the feed does its own polling otherwise)."""
        if self.dev is None:
            return None
        try:
            r = self.lm.read(self.dev)
        except Exception:  # noqa: BLE001
            return None
        r["t"] = time.time()
        self.rows.append(r)
        return r

    def close(self):
        if self.proc is not None:
            self.proc.terminate()


def cmd_run(a):
    import numpy as np
    import ot_ladder as L
    import sounddevice as sd
    plan = json.loads((pathlib.Path(a.project) / "OCTABAM_MATRIX.json").read_text())
    entries = plan["layouts"]
    out_dir = pathlib.Path("out/hw/matrix") / a.label
    out_dir.mkdir(parents=True, exist_ok=True)
    import usb_transport_probe as U
    dev, nch = U.find_input(a.audio)
    fs = 44100

    lm = LmFeed()
    print("LOAD METER: " + ("reading" if lm.ok() else f"unavailable ({lm.err})"))

    seg, lock = {"chunks": None}, threading.Lock()   # the callback fills seg while a layout plays

    live = {"db": 0.0}

    def cb(indata, frames, t, status):
        live["db"] = float(_db(np.sqrt(np.mean(indata.astype(np.float64) ** 2))))
        with lock:
            if seg["chunks"] is not None:
                seg["chunks"].append(indata.copy())
    bpm = a.bpm or plan.get("bpm") or 121.0
    pc_ch = a.pc_channel or plan.get("pc_channel") or 1
    clock = L.Clock(bpm, a.midi)
    results, base_m = [], None
    sd_stream = sd.InputStream(device=dev, channels=nch, samplerate=fs, dtype="float32", callback=cb)
    try:
        with sd_stream:
            for i in parse_only(a.only, len(entries)):
                e = entries[i]
                clock.stop(); time.sleep(0.3)
                clock.pc(pc_ch, e["program"]); time.sleep(0.8)
                t_settle = time.time()
                while live["db"] > SETTLE_DBFS and time.time() - t_settle < SETTLE_MAX_S:
                    time.sleep(0.25)
                settled = round(time.time() - t_settle, 1)
                with lock:
                    seg["chunks"] = []
                clock.start()
                t_play = time.time()
                while time.time() - t_play < a.play:
                    lm.poll()
                    time.sleep(0.25)
                clock.stop()
                time.sleep(a.tail)
                with lock:
                    chunks, seg["chunks"] = seg["chunks"], None
                x = np.concatenate(chunks).astype(np.float64) if chunks else np.zeros((0, nch))
                m = measure(x, fs, a.play) if len(x) >= int((a.play + 0.5) * fs) else None
                readings = [r for r in lm.window(t_play, t_play + a.play)] if lm.ok() else []
                if lm.dev is not None:
                    readings = [r for r in lm.rows if t_play <= r['t'] <= t_play + a.play]
                import load_meter as _lmod
                load = _lmod.summarise(readings) if len(readings) > 1 else None
                if m is None:
                    flags, at = ["NO AUDIO CAPTURED"], None
                elif e["name"] == "BASE":
                    base_m, flags, at = m, [], None
                else:
                    flags, at = judge(m, base_m or m, load)
                row = {"slot": e["slot"], "program": e["program"], "name": e["name"], "flags": flags, "settle_s": settled,
                       "freeze_at_s": at, "metrics": {k: v for k, v in (m or {}).items() if k != "alive"}, "load": load}
                results.append(row)
                print(f"{i:3d} PC{e['program']:3d} {e['name']:34s} "
                      + (f"rms {m['rms_db']:6.1f} hf {m['hf_db']:6.1f} clicks {m['clicks']:4d} " if m else "")
                      + (f"settle {settled:4.1f}s cf {100 * load['cf_share_max']:4.1f}% dsp {100 * load['dsp_core0_max']:4.1f}/{100 * load['dsp_core1_max']:4.1f}% " if load and load.get("windows") else "")
                      + (" ".join(flags) or "ok"), flush=True)
                if flags and x is not None and len(x):
                    wav = out_dir / f"{i:03d}_{re.sub(r'[^A-Za-z0-9]+', '_', e['name'])}.wav"
                    import wave
                    w = wave.open(str(wav), "wb")
                    w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(fs)
                    w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
                    w.close()
                if "CRASH" in flags:
                    print("CRASH: the sequencer is stuck; power-cycle the unit. Stopping.")
                    break
                if "FREEZE" in flags:
                    clock.stop(); time.sleep(0.5)
    finally:
        clock.stop()
        clock.close()
        lm.close()
        (out_dir / "report.json").write_text(json.dumps({"remix": plan["remix"], "project": a.project, "args": vars(a),
                                                        "results": results}, indent=1))
    bad = [r for r in results if r["flags"]]
    print(f"{len(results)} layouts run, {len(bad)} flagged; report {out_dir / 'report.json'}")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("remix"); p.add_argument("--pairs", action="store_true")
    p.add_argument("--play", type=float, default=12.0); p.add_argument("--tail", type=float, default=3.0)
    p = sub.add_parser("proj"); p.add_argument("src"); p.add_argument("dest"); p.add_argument("remix")
    p.add_argument("--pairs", action="store_true"); p.add_argument("--pattern", default="A2")
    p.add_argument("--stimuli", default="", help="ot_stimuli names, comma-separated: played on FLEX slots 1..N instead of SRC's pattern")
    p.add_argument("--stim-tracks", default="1-8", help="tracks that play them, round-robin (default 1-8)")
    p.add_argument("--clean", action="store_true", help="SRC is a fresh unit-created project: rebuild all 16 banks from its first "
                   "pattern and part (needs --stimuli); refused if `audit` finds SRC edited")
    p.add_argument("--allow-dirty-template", action="store_true", help="with --clean: use SRC although audit finds it edited")
    p.add_argument("--pc-channel", type=int, default=1, help="MIDI channel (1-16) the project receives program change on")
    p.add_argument("--setting", action="append", default=[], metavar="KEY=INT",
                   help="another [SETTINGS] key to stamp, e.g. MAIN_LEVEL=64 (repeatable); the keys are in project.work")
    p = sub.add_parser("run"); p.add_argument("project"); p.add_argument("label")
    p.add_argument("--midi", default="Elektron Octatrack DPS-1"); p.add_argument("--audio", default="Octatrack")
    p.add_argument("--pc-channel", type=int, default=None, help="default: the project's (see proj), else 1")
    p.add_argument("--bpm", type=float, default=None, help="default: the project's (120 for a stimuli project), else 121")
    p.add_argument("--play", type=float, default=12.0); p.add_argument("--tail", type=float, default=3.0)
    p.add_argument("--only", default="")
    p = sub.add_parser("audit"); p.add_argument("project")
    sub.add_parser("selftest")
    a = ap.parse_args()
    return {"plan": cmd_plan, "proj": cmd_proj, "run": cmd_run, "selftest": cmd_selftest, "audit": cmd_audit}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
