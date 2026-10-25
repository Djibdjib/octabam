#!/usr/bin/env python3
"""DLPUMP and DLCOPY under the port: a block staged in DRAM arrives in a DSP core's X memory, doorbell last, and is copied into the window.

    python3 tools/verify/verify_dlpump.py [--core 0|1] [--project DIR]

Builds REMIX=test/dlspike (MODULATION is its Remix.window_demand effect), arms the pump by poking
its state (core, destination, source, count, state last) and a staged block (effect index, window
offsets of the code and its entries, then the halfwords the copier takes: 2 per code word) into
DRAM, runs to a fixed time with no DSP effect assigned, and reads back, from the core the block
went to and from the other core: the doorbell, effect 0's entry and the code in the window.

Cannot see: the hardware's host-write timing, other projects' use of X:0x2840..0x3fff.
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1])); import toolpath  # noqa: E402,F401

ROOT = pathlib.Path(__file__).resolve().parents[2]
EMU = ROOT / "out/emu/ot_emu"
PY = ROOT / ".venv/bin/python3"
ELF = ROOT / "out/platform/runtime/runtime.elf"
OUT = ROOT / "out/dlpump"
SRC = 0x49301000                  # a DRAM run the firmware leaves alone (tools/poc/hotreload used it)
STAGE = 0x2900
RING = 0xA55A
FAILS = []


def check(what, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {what}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(what)


def symbols():
    nm = shutil.which("m68k-elf-nm") or shutil.which("m68k-linux-gnu-nm")
    out = {}
    for line in subprocess.run([nm, str(ELF)], capture_output=True, text=True).stdout.splitlines():
        parts = line.split()
        if len(parts) == 3:
            out[parts[2]] = int(parts[0], 16)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--core", type=int, default=1, choices=(0, 1))
    ap.add_argument("--project", default=os.environ.get("OT_PROJECT", ""))
    ap.add_argument("--set-name", default="BRAINSET")
    ap.add_argument("--name", default="BRAINPRJ")
    ap.add_argument("--ms", type=int, default=3000)
    a = ap.parse_args()
    project = a.project
    if not project and pathlib.Path("~/.octabam_project").expanduser().is_file():
        project = pathlib.Path("~/.octabam_project").expanduser().read_text().strip()
    if not project:
        print("  [SKIP] verify_dlpump: no project (OT_PROJECT=<dir>, --project or ~/.octabam_project)"); return 0
    if not EMU.is_file():
        print("  [SKIP] verify_dlpump: no port binary (make emu-cf)"); return 0
    OUT.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ, REMIX="test/dlspike", XBUS="1", SPEC="1")
    env.setdefault("BUILD", "0")
    r = subprocess.run([sys.executable, str(ROOT / "tools/build/build_bus.py")], env=env, capture_output=True,
                       text=True, cwd=ROOT)
    if r.returncode:
        sys.exit(f"verify_dlpump: building test/dlspike failed:\n{(r.stdout + r.stderr)[-1500:]}")
    image = OUT / "mainos.bin"
    shutil.copy2(ROOT / "out/mainos_bus.bin", image)
    sym = symbols()

    rec = json.loads((ROOT / "out/dsp/demand_records.json").read_text())["MODULATION"]
    halves = []
    for w in rec["words"]:
        halves += [w >> 8, w & 0xFF]
    win = 0x30000
    block = [0, rec["addr"] - win, len(rec["words"]), rec["init"] - win, rec["proc"] - win] + halves      # effect 0

    pokes = []
    for i, h in enumerate(block):
        pokes += [f"{SRC + 2 * i:#x}={h >> 8:#x}", f"{SRC + 2 * i + 1:#x}={h & 0xFF:#x}"]
    for name, val in (("dl_core", a.core), ("dl_dest", STAGE + 1), ("dl_src", SRC), ("dl_left", len(block)),
                      ("dl_state", 1)):
        pokes += [f"{sym[name] + k:#x}={(val >> (8 * (3 - k))) & 0xFF:#x}" for k in range(4)]

    copy = OUT / "project"
    shutil.rmtree(copy, ignore_errors=True)
    copy.mkdir(parents=True)
    for f in pathlib.Path(project).expanduser().iterdir():
        if f.is_file() and f.suffix.lower() == ".work":
            shutil.copy2(f, copy / f.name)
    card = OUT / "card.img"
    r = subprocess.run([str(PY), str(ROOT / "tools/emu/ot_emu/stage_card.py"), str(copy), a.set_name, a.name,
                        "--tree", str(OUT / "tree"), "--out", str(card)], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"verify_dlpump: stage_card failed:\n{r.stdout[-800:]}{r.stderr[-800:]}")
    (OUT / "run.script").write_text(f"{a.ms} quit\n")
    state_dump = OUT / "state.bin"
    cmd = [EMU, "--image", image, "--card", card, "--set", a.set_name, "--project", a.name, "--load-ms", "90000",
           "--mkii", "--dsp", "--frame", "--live-script", OUT / "run.script",
           "--step", "-:poke:" + ";".join(pokes),
           "--dsp-peek", ";".join(f"{c}:X:{STAGE:x},1;{c}:X:33d80,5;{c}:P:{rec['addr']:x},{len(rec['words'])}" for c in (a.core, 1 - a.core)),
           "--mem-dump", f"{sym['dl_state']:#x},20={state_dump}"]
    log = OUT / "run.txt"
    with open(log, "w") as fh:
        r = subprocess.run(list(map(str, cmd)), cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
    text = log.read_text(errors="replace")
    if r.returncode or "ended on quit" not in text:
        sys.exit(f"verify_dlpump: the run did not finish -- {log}")

    def peek(space, addr, core=a.core):
        m = re.search(rf"core {core} {space}:0x0*{addr:x}:([^\n]*)", text)
        return [int(t, 16) for t in m.group(1).split()] if m else []

    bell = peek("X", STAGE)
    entry = peek("X", 0x33D80)
    code = peek("P", rec["addr"])
    check("the doorbell was consumed by the copier", bell == [0], f"{bell}")
    check("effect 0 is bound", entry[:1] == [0xB0A5ED], f"{[hex(w) for w in entry]}")
    check("its init and proc and span are published",
          entry[1:5] == [rec["init"], rec["proc"], rec["addr"], rec["addr"] + len(rec["words"])],
          f"{[hex(w) for w in entry[1:5]]}")
    bad = [i for i, (g, w) in enumerate(zip(code, rec["words"])) if g != w]
    check("the code is in the window, every word", len(code) == len(rec["words"]) and not bad,
          f"{len(code)} of {len(rec['words'])} words read, {len(bad)} differ")
    other = 1 - a.core
    check("the other core sees effect 0 bound", peek("X", 0x33D80, other)[:1] == [0xB0A5ED])
    check("the other core sees the code", peek("P", rec["addr"], other) == rec["words"])
    left = int.from_bytes(state_dump.read_bytes()[0:4], "big")
    check("the pump is idle again", left == 0, f"dl_state={left}")
    print("PASS" if not FAILS else "FAIL")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
