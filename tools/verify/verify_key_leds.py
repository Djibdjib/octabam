#!/usr/bin/env python3
"""KEY LEDS: the CHROMATIC trig keys light the MIDI track's KEY.

Under the port, MKI and MKII: MIDI mode, track 1, TRACK + the trig-mode
list twice (CHROMATIC), with MIDI track 1's KEY byte (0x46c76df1) set
before. The trig LEDs are decoded from the panel stream (both colours'
levels, ids 0..31) and compared with a model built here from the modes
as rotations of the major scale -- not from the module's tables: the
tonic yellow, the scale's other notes red, the rest dark, key 1 = C.
KEY 0 (OFF) and an audio track must be stock's C major. With MIDI SCALES
in the remix every KEY 0..84 is run; without it, stock's 0..24.
"""
import os
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "panel"))
import toolpath  # noqa: E402,F401
from remix import registry  # noqa: E402
from panel_link import PanelLink  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY_LANE = 0x46c76df1                     # MIDI track 1's KEY byte
MAJOR = (0, 2, 4, 5, 7, 9, 11)
MODES = {"MAJ": 0, "DOR": 1, "PHR": 2, "LYD": 3, "MIX": 4, "MIN": 5, "LOC": 6}   # degree the mode starts on
ADDED = ("DOR", "PHR", "LYD", "MIX", "LOC")


def scale(mode):
    """The mode's pitch classes above its tonic: the major scale from that degree."""
    first = MAJOR[MODES[mode]]
    return {(p - first) % 12 for p in MAJOR}


def decode(key):
    """KEY byte -> (tonic, mode); None for OFF. Stock's 1..24, MIDI SCALES' 25..84."""
    if key == 0:
        return None
    if key <= 24:
        return (key - 1) // 2, ("MAJ", "MIN")[(key - 1) % 2]
    return (key - 25) // 5, ADDED[(key - 25) % 5]


def expected(key):
    tonic, mode = decode(key) or (0, "MAJ")     # OFF and audio: stock's C major
    notes = scale(mode)
    out = ""
    for k in range(16):
        degree = (k % 12 - tonic) % 12
        out += "Y" if degree == 0 else "R" if degree in notes else "."
    return out


def shown(stream):
    link = PanelLink()
    link.feed(stream.read_bytes())
    colours = {(15, 15): "Y", (15, 0): "R", (0, 0): ".", (0, 15): "G"}
    return "".join(colours.get((link.leds.get(2 * k, 0), link.leds.get(2 * k + 1, 0)), "?")
                   for k in range(16))


def script(path, midi):
    lines, t = [], 1500

    def send(text, gap=150):
        nonlocal t
        lines.append(f"{t} {text}")
        t += gap

    def tap(key):
        send(f"key {key:#x} down", 40)
        send(f"key {key:#x} up", 300)

    tap(0x32)
    if midi:
        tap(0x35)                         # MIDI mode
    send("key 0x2d down")
    tap(0x20)                             # the trig-mode list
    tap(0x20)                             # CHROMATIC
    send("key 0x2d up", 1500)
    send("quit")
    path.write_text("\n".join(lines) + "\n")


def main():
    remix = sys.argv[1]
    mods = registry.remix(remix).modules
    if "KEY LEDS" not in mods:
        return 0
    keys = range(85) if "MIDI SCALES" in mods else range(25)
    out = ROOT / "out/key-leds"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    env = dict(os.environ, REMIX=remix, XBUS="1", SPEC="1")
    subprocess.run([sys.executable, "tools/build/build_bus.py"], cwd=ROOT, env=env,
                   stdout=subprocess.DEVNULL, check=True)
    image = out / "mainos.bin"
    shutil.copy2(ROOT / "out/mainos_bus.bin", image)
    empty = out / "empty-project"
    empty.mkdir()
    card = out / "card.img"
    subprocess.run([str(ROOT / ".venv/bin/python3"), "tools/emu/ot_emu/stage_card.py",
                    str(empty), "KLSET", "KLPRJ", "--out", str(card)], cwd=ROOT,
                   stdout=subprocess.DEVNULL, check=True)
    script(out / "midi.script", True)
    script(out / "audio.script", False)
    modes = "0x80000012=00;0x80000013=00;0x80000014=00;0x80000015=00"
    runs = [(f"midi-{k}", "midi", k) for k in keys] + [("audio-6", "audio", 6)]
    fails = 0
    for model in ("mki", "mkii"):
        cmd = [str(ROOT / "out/emu/ot_emu"), "--image", str(image), "--card", str(card),
               "--set", "KLSET", "--project", "KLPRJ", "--load-ms", "90000",
               "--scenario-jobs", str(os.cpu_count() or 4)]
        if model == "mkii":
            cmd.append("--mkii")
        for tag, kind, key in runs:
            base = out / f"{model}-{tag}"
            cmd += ["--scenario", f"{base}.log --live-script {out / kind}.script --serial-out {base} "
                    f"--poke {modes};{KEY_LANE:#x}={key}"]
        with (out / f"{model}.log").open("w") as f:
            subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
        bad = []
        for tag, kind, key in runs:
            base = out / f"{model}-{tag}"
            want = expected(key) if kind == "midi" else expected(0)
            got = shown(base.with_suffix(".a")) if base.with_suffix(".a").exists() else "(no stream)"
            ended = "ended on quit" in base.with_suffix(".log").read_text()
            if got != want or not ended:
                bad.append(f"{tag}: want {want} got {got}{'' if ended else ' (the script did not end)'}")
        print(f"  [{'FAIL' if bad else 'PASS'}] verify_key_leds: {model}, {len(runs)} runs "
              f"(MIDI KEY {keys.start}..{keys.stop - 1}, an audio track)")
        for line in bad[:8]:
            print(f"      {line}")
        fails += bool(bad)
    return int(bool(fails))


if __name__ == "__main__":
    sys.exit(main())
