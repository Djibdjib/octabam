#!/usr/bin/env python3
"""The demand loader under the port: DLPUMP loads and withdraws an effect as the tracks use it, DLCOPY publishes it.

    python3 tools/verify/verify_dlload.py [--remix test/dlspike] [--project DIR]

Builds the remix (default test/dlspike: MODULATION on demand; octabam: four effects) and runs scenarios on the
staged project, each on its own boot, setting track effect ids by poking the live arrays
(0x80000ec4 FX1, 0x80000ecc FX2) and the Part bytes behind them. Effects are numbered as in
Remix.window_demand (k):

  used       T1.. use effects 0.. on FX1 from the start -> each bound, its entry and code in the window
                                                          word for word, seen from both cores
  withdrawn  the same, T1's FX1 back to FILTER at 2 s  -> effect 0 unbound, its span empty, the rest bound
  unused     no track uses any                          -> none bound
  runs-b / runs-a  T1 (core B) / T5 (core A) uses effect 0 -> its loaded proc is reached on that core (--dsp-pcwatch)
  blocked    effect 0 in use, and the FX2 of the track whose slot shares its block is PLATE REV -> effect 0 not loaded
  pick / pick-blocked  T2's FX1 chooser (NONE, then DOWN, YES) picks effect 0; with the block's track on PLATE REV
             the chooser leaves T2's FX1 as it was

Cannot see: the hardware's host-write timing, other projects' use of X:0x2840..0x3fff.
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1])); import toolpath  # noqa: E402,F401

ROOT = pathlib.Path(__file__).resolve().parents[2]
EMU = ROOT / "out/emu/ot_emu"
PY = ROOT / ".venv/bin/python3"
OUT = ROOT / "out/dlload"
STAGE = 0x2900
FX1_LIVE, FX2_LIVE = 0x80000EC4, 0x80000ECC
FX1_PART, FX2_PART = 0x402A75E0, 0x402A75E8      # Part 1's FX ids of track 1 (bank + 0x8ed80 / 0x8ed88)
FILTER, PLATE = 0x01, 0x14
KEYS = dict(no=0x32, fx1=0x25, down=0x20, yes=0x31, t2=0x11)
FAILS = []


def check(what, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {what}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(what)


def poke(live, part, track, value):
    return f"{live + track:#x}={value:#x};{part + track:#x}={value:#x}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--remix", default="test/dlspike")
    ap.add_argument("--project", default=os.environ.get("OT_PROJECT", ""))
    ap.add_argument("--set-name", default="BRAINSET")
    ap.add_argument("--name", default="BRAINPRJ")
    ap.add_argument("--ms", type=int, default=4000)
    a = ap.parse_args()
    project = a.project
    if not project and pathlib.Path("~/.octabam_project").expanduser().is_file():
        project = pathlib.Path("~/.octabam_project").expanduser().read_text().strip()
    if not project:
        print("  [SKIP] verify_dlload: no project (OT_PROJECT=<dir>, --project or ~/.octabam_project)"); return 0
    if not EMU.is_file():
        print("  [SKIP] verify_dlload: no port binary (make emu-cf)"); return 0
    OUT.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ, REMIX=a.remix, XBUS="1", SPEC="1")
    env.setdefault("BUILD", "0")
    r = subprocess.run([sys.executable, str(ROOT / "tools/build/build_bus.py")], env=env, capture_output=True,
                       text=True, cwd=ROOT)
    if r.returncode:
        sys.exit(f"verify_dlload: building {a.remix} failed:\n{(r.stdout + r.stderr)[-1500:]}")
    image = OUT / "mainos.bin"
    shutil.copy2(ROOT / "out/mainos_bus.bin", image)
    recs = list(json.loads((ROOT / "out/dsp/demand_records.json").read_text()).items())
    from remix import registry
    order = list(registry.remix(a.remix).window_demand)
    recs = [dict(next(r for key, r in recs if key == k), key=k) for k in order]
    rec = recs[0]
    mod_id = rec["id"]

    copy = OUT / "project"
    shutil.rmtree(copy, ignore_errors=True)
    copy.mkdir(parents=True)
    for f in pathlib.Path(project).expanduser().iterdir():
        if f.is_file() and f.suffix.lower() == ".work":
            shutil.copy2(f, copy / f.name)

    every = ";".join(poke(FX1_LIVE, FX1_PART, t, r["id"]) for t, r in enumerate(recs))
    block_track = {0: 6, 1: 7, 2: 2, 3: 3}[(rec["addr"] - 0x30000) >> 14 & 3]       # modules/dlpump/manifest.py
    scenarios = {
        "used": (every, []),
        "withdrawn": (every, [(2000, poke(FX1_LIVE, FX1_PART, 0, FILTER))]),
        "unused": ("", []),
        "blocked": (poke(FX1_LIVE, FX1_PART, 0, mod_id) + ";" + poke(FX2_LIVE, FX2_PART, block_track, PLATE), []),
        "pick": (poke(FX1_LIVE, FX1_PART, 1, 0), []),
        "pick-blocked": (poke(FX1_LIVE, FX1_PART, 1, 0) + ";" + poke(FX2_LIVE, FX2_PART, block_track, PLATE), []),
        "runs-b": (poke(FX1_LIVE, FX1_PART, 0, mod_id), []),      # T1 is on core B
        "runs-a": (poke(FX1_LIVE, FX1_PART, 4, mod_id), []),      # T5 is on core A
    }
    watch = {"runs-b": f"1:{rec['proc']:x}", "runs-a": f"0:{rec['proc']:x}"}
    procs = {}
    for tag, (first, later) in scenarios.items():
        card = OUT / f"{tag}.img"
        r = subprocess.run([str(PY), str(ROOT / "tools/emu/ot_emu/stage_card.py"), str(copy), a.set_name, a.name,
                            "--tree", str(OUT / f"tree_{tag}"), "--out", str(card)], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"verify_dlload: stage_card failed:\n{r.stdout[-800:]}{r.stderr[-800:]}")
        lines = [f"{ms} poke {p}" for ms, p in later]
        if tag.startswith("pick"):
            t = 1500
            for k, gap in (("no", 400), ("t2", 400), ("fx1", 160), ("fx1", 800), ("down", 600), ("yes", 1500)):
                lines += [f"{t} key {KEYS[k]:#x} down", f"{t + 40} key {KEYS[k]:#x} up"]
                t += 40 + gap
        lines.append(f"{a.ms} quit")
        (OUT / f"{tag}.script").write_text("\n".join(lines) + "\n")
        dump = OUT / f"{tag}_ids.bin"
        peeks = ";".join(f"{c}:X:{STAGE:x},1;{c}:X:{0x33DA3 + 8 * k:x},5;{c}:P:{r['addr']:x},{len(r['words'])}"
                         for c in (0, 1) for k, r in enumerate(recs))
        cmd = [EMU, "--image", image, "--card", card, "--set", a.set_name, "--project", a.name, "--load-ms", "90000",
               "--mkii", "--dsp", "--frame", "--live-script", OUT / f"{tag}.script", "--dsp-peek", peeks,
               "--mem-dump", f"{FX1_LIVE:#x},16={dump}"]
        if first:
            cmd += ["--step", "-:poke:" + first]
        if tag in watch:
            cmd += ["--dsp-pcwatch", watch[tag]]
        fh = open(OUT / f"{tag}.txt", "w")
        procs[tag] = (subprocess.Popen(list(map(str, cmd)), cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT), fh)
    texts = {}
    for tag, (p, fh) in procs.items():
        rc = p.wait()
        fh.close()
        texts[tag] = (OUT / f"{tag}.txt").read_text(errors="replace")
        if rc or "ended on quit" not in texts[tag]:
            sys.exit(f"verify_dlload: the {tag} run did not finish -- {OUT / (tag + '.txt')}")

    def peek(tag, core, space, addr):
        m = re.search(rf"core {core} {space}:0x0*{addr:x}:([^\n]*)", texts[tag])
        return [int(t, 16) for t in m.group(1).split()] if m else []

    print("used:")
    for k, r in enumerate(recs):
        n = len(r["words"])
        for c in (1, 0):
            entry = peek("used", c, "X", 0x33DA3 + 8 * k)
            check(f"core {c}: {r['key']} is bound with its entries and span",
                  entry == [0xB0A5ED, r["init"], r["proc"], r["addr"], r["addr"] + n], f"{[hex(w) for w in entry]}")
            code = peek("used", c, "P", r["addr"])
            check(f"core {c}: {r['key']}'s code is in the window, every word", code == r["words"],
                  f"{len(code)} of {n} words read")
    check("the doorbell was consumed", peek("used", 1, "X", STAGE) == [0])
    print("withdrawn:")
    entry = peek("withdrawn", 1, "X", 0x33DA3)
    check(f"{recs[0]['key']} is unbound and its span empty", entry[:1] == [0] and entry[3:5] == [0, 0], f"{[hex(w) for w in entry]}")
    for k, r in enumerate(recs[1:], 1):
        check(f"{r['key']} stays bound", peek("withdrawn", 1, "X", 0x33DA3 + 8 * k)[:1] == [0xB0A5ED])
    print("unused:")
    for k, r in enumerate(recs):
        check(f"{r['key']} was never bound", peek("unused", 1, "X", 0x33DA3 + 8 * k)[:1] == [0])
    print("blocked:")
    check(f"{recs[0]['key']} is not loaded over a stock reverb's block", peek("blocked", 1, "X", 0x33DA3)[:1] == [0])
    print("pick:")
    ids = {t: (OUT / f"{t}_ids.bin").read_bytes() for t in ("pick", "pick-blocked")}
    check(f"T2's FX1 chooser picks {recs[0]['key']} when it can be loaded", ids["pick"][1] == mod_id, f"FX1 of T2 = 0x{ids['pick'][1]:02x}")
    check("and leaves T2's FX1 as it was when the block is under a stock reverb", ids["pick-blocked"][1] == 0,
          f"FX1 of T2 = 0x{ids['pick-blocked'][1]:02x}")
    print("runs:")
    for tag, core in (("runs-b", 1), ("runs-a", 0)):
        m = re.search(r"dsp pcwatch:[^\n]*\n((?: +\d+ [^\n]*\n)*)", texts[tag])
        arrivals = len(m.group(1).splitlines()) if m else None
        check(f"core {core}: the loaded code runs on a track of that core", bool(arrivals),
              f"arrivals at P:0x{rec['proc']:x}: {arrivals}")
    print("PASS" if not FAILS else "FAIL")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
