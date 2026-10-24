#!/usr/bin/env python3
"""Seeded stress sequences for the unit, driven over USB MIDI, with the health checks of the one-cable rig.

    python3 tools/hw/ot_fuzz.py gen SEED OUT.json [--profile mix] [--minutes 5] [--layouts 28]
    python3 tools/hw/ot_fuzz.py run SEQ.json LABEL [--until N] [--audio Octatrack] [--midi NAME]
    python3 tools/hw/ot_fuzz.py show SEQ.json [--from N --to M]

A sequence is a list of timed operations a person could make over MIDI: program changes to the
project's layouts (single, in bursts a few tenths of a second apart, and back again), START and
STOP at any moment, a MIDI clock whose tempo moves, the crossfader (CC 48) swept and jumped, scene
A / B select (CC 55, 56), track mutes and levels, FX page-1 knobs. The same SEED gives the same
sequence; `run` sends it with the recorded timing and, every 0.5 s, checks that the DSP's frame
count advances, the frame interrupt keeps its rate and LOAD METER's bad records stay near zero,
that the MIDI and audio endpoints are still there and the audio level has not gone dead for 3 s
while the transport plays. It stops on the first failure and writes out/hw/fuzz/LABEL/failure.json
with the operation index, the last 40 operations and the unit's state, so `run SEQ.json LABEL
--until INDEX` replays up to it. The unit has to be power-cycled after a failure.

Profiles: pc (program changes only, bursts included), transport (START / STOP / tempo), xf (crossfader
and scene select), mix (all of them, program changes weighted most).

What it does not do: the panel (LOAD KIT, SAVE KIT, setting a scene lock, the direct-jump toggle) has
to be set up by hand before a run, and it cannot see inside the unit beyond LOAD METER, the audio
stream and the endpoints; a halt that leaves them looking normal is missed. The projects it drives are
the ones `ot_matrix.py proj` writes: layouts are programs 16 * bank + pattern - 1.
"""
import argparse
import json
import pathlib
import random
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PROFILES = {
    "pc": {"pc": 10, "pc_burst": 4, "pc_back": 3},
    "transport": {"start": 5, "stop": 5, "tempo": 4, "pc": 2},
    "xf": {"xf_sweep": 5, "xf_jump": 4, "scene": 4, "pc": 1},
    "mix": {"pc": 10, "pc_burst": 4, "pc_back": 3, "start": 3, "stop": 3, "tempo": 2, "xf_sweep": 3, "xf_jump": 3,
            "scene": 2, "mute": 3, "level": 2, "knob": 4},
}
HEALTH_EVERY_S, DEAD_AUDIO_S = 0.5, 3.0


def program_of(layout):
    """Layout slot (0..31) -> the program change that selects it (ot_matrix: bank = slot // 4, pattern = slot % 4)."""
    return (layout // 4) * 16 + layout % 4


def gen(seed, minutes, layouts, profile):
    """-> {"seed", "profile", "layouts", "ops": [{"t": seconds, "op": name, "bytes": [..], "note": text}]}.
    Bytes are on MIDI channel 1 for program changes and on the track's channel (track t = channel t) for CCs."""
    rng = random.Random(seed)
    weights = PROFILES[profile]
    names, w = list(weights), [weights[k] for k in weights]
    ops, t, bpm, playing, layout, nb = [], 0.0, 120.0, False, 0, 0

    def add(at, op, bytes_, note=""):
        ops.append({"t": round(at, 3), "op": op, "bytes": list(bytes_), "note": note})

    add(0.0, "start", [0xFA], "START at the first layout")
    playing = True
    while t < minutes * 60.0:
        t += rng.choice([0.25, 0.5, 1.0, 2.0, 3.0, 5.0]) * rng.uniform(0.6, 1.4)
        kind = rng.choices(names, w)[0]
        if kind == "pc":
            layout = rng.randrange(layouts)
            add(t, "pc", [0xC0, program_of(layout)], f"layout {layout}")
        elif kind == "pc_burst":
            nb += 1
            for j in range(rng.randint(3, 8)):
                layout = rng.randrange(layouts)
                add(t, "pc", [0xC0, program_of(layout)], f"burst {nb}.{j}, layout {layout}")
                t += rng.uniform(0.02, 0.4)
        elif kind == "pc_back":
            a, b = layout, rng.randrange(layouts)
            add(t, "pc", [0xC0, program_of(b)], f"layout {b}")
            add(t + rng.uniform(0.05, 0.8), "pc", [0xC0, program_of(a)], f"back to layout {a}")
            t += 1.0
        elif kind == "start" and not playing:
            add(t, "start", [0xFA]); playing = True
        elif kind == "stop" and playing:
            add(t, "stop", [0xFC]); playing = False
        elif kind == "tempo":
            bpm = max(60.0, min(180.0, bpm + rng.choice([-30, -10, -1, 1, 10, 30])))
            add(t, "tempo", [], f"{bpm:g}")
        elif kind == "xf_sweep":
            a, b = rng.randrange(128), rng.randrange(128)
            n = rng.randint(8, 40)
            for i in range(n + 1):
                add(t + i * 0.05, "cc", [0xB0, 48, round(a + (b - a) * i / n)], "crossfader sweep")
            t += n * 0.05
        elif kind == "xf_jump":
            add(t, "cc", [0xB0, 48, rng.choice([0, 127, rng.randrange(128)])], "crossfader jump")
        elif kind == "scene":
            add(t, "cc", [0xB0, rng.choice([55, 56]), rng.randrange(128)], "scene select")
        elif kind == "mute":
            tr = rng.randrange(8)
            add(t, "cc", [0xB0 | tr, 49, rng.choice([0, 127])], f"mute T{tr + 1}")
        elif kind == "level":
            tr = rng.randrange(8)
            add(t, "cc", [0xB0 | tr, 7, rng.randrange(40, 128)], f"level T{tr + 1}")
        elif kind == "knob":
            tr = rng.randrange(8)
            cc = rng.choice(list(range(34, 40)) + list(range(40, 46)))
            add(t, "cc", [0xB0 | tr, cc, rng.randrange(128)], f"T{tr + 1} knob CC{cc}")
    add(t + 2.0, "stop", [0xFC], "end")
    ops.sort(key=lambda o: o["t"])
    return {"seed": seed, "profile": profile, "layouts": layouts, "minutes": minutes, "ops": ops}


class ClockGen(threading.Thread):
    """24 ppqn MIDI clock whose tempo can change, sent while `running`."""

    def __init__(self, out, bpm=120.0):
        super().__init__(daemon=True)
        self.out, self.bpm, self.stop_evt = out, bpm, threading.Event()

    def run(self):
        nxt = time.monotonic()
        while not self.stop_evt.is_set():
            self.out.send([0xF8])
            nxt += 60.0 / (self.bpm * 24.0)
            d = nxt - time.monotonic()
            if d > 0:
                time.sleep(d)
            else:
                nxt = time.monotonic()


def cmd_gen(a):
    seq = gen(a.seed, a.minutes, a.layouts, a.profile)
    pathlib.Path(a.out).write_text(json.dumps(seq, indent=1))
    kinds = {}
    for o in seq["ops"]:
        kinds[o["op"]] = kinds.get(o["op"], 0) + 1
    print(f"seed {a.seed}, profile {a.profile}: {len(seq['ops'])} operations over {seq['ops'][-1]['t']:.0f} s: {kinds}")
    return 0


def cmd_show(a):
    seq = json.loads(pathlib.Path(a.seq).read_text())
    for i, o in enumerate(seq["ops"]):
        if (a.start is None or i >= a.start) and (a.to is None or i <= a.to):
            print(f"{i:5d} {o['t']:8.3f}s  {o['op']:6s} {bytes(o['bytes']).hex(' '):12s} {o['note']}")
    return 0


def cmd_run(a):
    import numpy as np
    import ot_midi
    import load_meter
    import sounddevice as sd
    import usb_transport_probe as U
    seq = json.loads(pathlib.Path(a.seq).read_text())
    ops = seq["ops"] if a.until is None else seq["ops"][:a.until + 1]
    out_dir = pathlib.Path("out/hw/fuzz") / a.label
    out_dir.mkdir(parents=True, exist_ok=True)
    usb = load_meter.libusb_device()
    dev, nch = U.find_input(a.audio)
    out = ot_midi.Out(a.midi)
    clock = ClockGen(out)
    state = {"idx": -1, "db": -240.0, "played_at": None, "bad0": None, "fail": None, "samples": []}

    def cb(indata, frames, t, status):
        state["db"] = float(20 * np.log10(max(np.sqrt(np.mean(indata[:, :2].astype(np.float64) ** 2)), 1e-12)))
    last_audio = {"t": time.monotonic()}

    def check():
        """-> a reason string, or None."""
        ok, why = load_meter.healthy(usb)
        if not ok:
            return why
        r = load_meter.read_fast(usb)
        if state["bad0"] is None:
            state["bad0"] = r["dsp"]["bad"]
        state["samples"].append((round(time.monotonic() - t_start, 2), round(r["cf"]["longest_us"]), r["dsp"]["bad"] - state["bad0"]))
        if r["dsp"]["bad"] - state["bad0"] > 200:
            return f"{r['dsp']['bad'] - state['bad0']} bad records since the start (frames are being skipped)"
        if not any(n == "Elektron Octatrack DPS-1" for n, _ in ot_midi.endpoints("dst")):
            return "the MIDI destination is gone"
        if state["db"] > -80.0:
            last_audio["t"] = time.monotonic()
        elif state["played_at"] is not None and time.monotonic() - max(last_audio["t"], state["played_at"]) > DEAD_AUDIO_S:
            return f"the audio has been silent for {DEAD_AUDIO_S:.0f} s while the transport plays"
        return None

    t_start = time.monotonic()
    code = 0
    try:
        with sd.InputStream(device=dev, channels=nch, samplerate=44100, dtype="float32", callback=cb):
            clock.start()
            nxt_check = t_start
            for i, o in enumerate(ops):
                while time.monotonic() - t_start < o["t"]:
                    if time.monotonic() >= nxt_check:
                        why = check()
                        nxt_check += HEALTH_EVERY_S
                        if why:
                            state["fail"] = why
                            break
                    time.sleep(0.01)
                if state["fail"]:
                    break
                state["idx"] = i
                if o["op"] == "tempo":
                    clock.bpm = float(o["note"])
                elif o["bytes"]:
                    out.send(o["bytes"])
                if o["op"] == "start":
                    state["played_at"] = time.monotonic(); last_audio["t"] = time.monotonic()
                elif o["op"] == "stop":
                    state["played_at"] = None
            if not state["fail"]:
                # a final look after the last operation
                time.sleep(1.0)
                state["fail"] = check()
    finally:
        clock.stop_evt.set()
        try:
            out.send([0xFC])
        except Exception:  # noqa: BLE001
            pass
    idx = state["idx"]
    if state["fail"]:
        code = 1
        rep = {"seed": seq["seed"], "profile": seq["profile"], "failed_after_operation": idx, "reason": state["fail"],
               "elapsed_s": round(time.monotonic() - t_start, 1), "last_operations": ops[max(idx - 39, 0):idx + 1],
               "samples_tail": state["samples"][-20:],
               "replay": f"python3 tools/hw/ot_fuzz.py run {a.seq} {a.label}_replay --until {idx}"}
        (out_dir / "failure.json").write_text(json.dumps(rep, indent=1))
        print(f"FAILED after operation {idx} at {rep['elapsed_s']} s: {state['fail']}")
        print(f"  last: {ops[idx]['op']} {ops[idx]['note']}; failure.json has the last 40 operations. Power-cycle the unit.")
    else:
        longest = max((s[1] for s in state["samples"]), default=0)
        print(f"{len(ops)} operations over {ops[-1]['t']:.0f} s, no failure; ColdFire longest run {longest} us, "
              f"bad records {state['samples'][-1][2] if state['samples'] else 0}")
    (out_dir / "run.json").write_text(json.dumps({"seed": seq["seed"], "operations": len(ops), "failed": state["fail"],
                                                  "samples": state["samples"][::4]}))
    return code


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("gen"); p.add_argument("seed", type=int); p.add_argument("out")
    p.add_argument("--profile", choices=sorted(PROFILES), default="mix"); p.add_argument("--minutes", type=float, default=5.0)
    p.add_argument("--layouts", type=int, default=28, help="layouts in the project (slot 0 is BASE)")
    p = sub.add_parser("run"); p.add_argument("seq"); p.add_argument("label")
    p.add_argument("--until", type=int, default=None, help="stop after this operation index (a replay)")
    p.add_argument("--audio", default="Octatrack"); p.add_argument("--midi", default="Elektron Octatrack DPS-1")
    p = sub.add_parser("show"); p.add_argument("seq")
    p.add_argument("--from", dest="start", type=int, default=None); p.add_argument("--to", type=int, default=None)
    a = ap.parse_args()
    return {"gen": cmd_gen, "run": cmd_run, "show": cmd_show}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
