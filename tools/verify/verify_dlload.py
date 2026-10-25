#!/usr/bin/env python3
"""The demand loader under the port: DLPUMP loads and withdraws an effect as the tracks use it, DLCOPY publishes it.

    python3 tools/verify/verify_dlload.py [--project DIR]

Builds REMIX=test/dlspike (MODULATION is its Remix.window_demand effect) and runs four scenarios on the
staged project, each on its own boot, setting track effect ids by poking the live arrays
(0x80000ec4 FX1, 0x80000ecc FX2) and the Part bytes behind them:

  used       T1's FX1 is MODULATION from the start      -> effect 0 bound, the code in the window word for
                                                           word, seen from both cores
  withdrawn  the same, T1's FX1 back to FILTER at 2 s  -> effect 0 unbound, its span empty
  unused     no track uses it                           -> effect 0 never bound
  runs-b / runs-a  T1 (core B) / T5 (core A) uses it -> the loaded proc is reached on that core (--dsp-pcwatch)
  blocked    as used, and T8's FX2 (the track whose slot   -> effect 0 not loaded
             shares MODULATION's block) is PLATE REV

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
FAILS = []


def check(what, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {what}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(what)


def poke(live, part, track, value):
    return f"{live + track:#x}={value:#x};{part + track:#x}={value:#x}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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

    env = dict(os.environ, REMIX="test/dlspike", XBUS="1", SPEC="1")
    env.setdefault("BUILD", "0")
    r = subprocess.run([sys.executable, str(ROOT / "tools/build/build_bus.py")], env=env, capture_output=True,
                       text=True, cwd=ROOT)
    if r.returncode:
        sys.exit(f"verify_dlload: building test/dlspike failed:\n{(r.stdout + r.stderr)[-1500:]}")
    image = OUT / "mainos.bin"
    shutil.copy2(ROOT / "out/mainos_bus.bin", image)
    rec = json.loads((ROOT / "out/dsp/demand_records.json").read_text())["MODULATION"]
    mod_id = rec["id"]

    copy = OUT / "project"
    shutil.rmtree(copy, ignore_errors=True)
    copy.mkdir(parents=True)
    for f in pathlib.Path(project).expanduser().iterdir():
        if f.is_file() and f.suffix.lower() == ".work":
            shutil.copy2(f, copy / f.name)

    scenarios = {
        "used": (poke(FX1_LIVE, FX1_PART, 0, mod_id), []),
        "withdrawn": (poke(FX1_LIVE, FX1_PART, 0, mod_id), [(2000, poke(FX1_LIVE, FX1_PART, 0, FILTER))]),
        "unused": ("", []),
        "blocked": (poke(FX1_LIVE, FX1_PART, 0, mod_id) + ";" + poke(FX2_LIVE, FX2_PART, 7, PLATE), []),
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
        lines = [f"{ms} poke {p}" for ms, p in later] + [f"{a.ms} quit"]
        (OUT / f"{tag}.script").write_text("\n".join(lines) + "\n")
        peeks = ";".join(f"{c}:X:{STAGE:x},1;{c}:X:33d80,5;{c}:P:{rec['addr']:x},{len(rec['words'])}" for c in (0, 1))
        cmd = [EMU, "--image", image, "--card", card, "--set", a.set_name, "--project", a.name, "--load-ms", "90000",
               "--mkii", "--dsp", "--frame", "--live-script", OUT / f"{tag}.script", "--dsp-peek", peeks]
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

    n = len(rec["words"])
    print("used:")
    for c in (1, 0):
        entry = peek("used", c, "X", 0x33D80)
        check(f"core {c}: effect 0 is bound with its entries and span",
              entry == [0xB0A5ED, rec["init"], rec["proc"], rec["addr"], rec["addr"] + n], f"{[hex(w) for w in entry]}")
        code = peek("used", c, "P", rec["addr"])
        check(f"core {c}: the code is in the window, every word", code == rec["words"],
              f"{len(code)} of {n} words read")
    check("the doorbell was consumed", peek("used", 1, "X", STAGE) == [0])
    print("withdrawn:")
    entry = peek("withdrawn", 1, "X", 0x33D80)
    check("effect 0 is unbound and its span empty", entry[:1] == [0] and entry[3:5] == [0, 0], f"{[hex(w) for w in entry]}")
    print("unused:")
    check("effect 0 was never bound", peek("unused", 1, "X", 0x33D80)[:1] == [0])
    print("blocked:")
    check("effect 0 is not loaded over a stock reverb's block", peek("blocked", 1, "X", 0x33D80)[:1] == [0])
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
