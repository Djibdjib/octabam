#!/usr/bin/env python3
"""DLSTUB and DLCOPY under dsp_host: dry until the demand-loaded code is bound, then the real code, bit for bit.

    python3 tools/verify/verify_dlstub.py

Renders the same input through MODULATION on its own id, through the stock null stub (the dry reference: dsp_host
shapes its input, so a pass-through does not return it bit for bit), through DLSTUB unbound (it must equal the null
stub) and through DLSTUB bound to MODULATION's code (it must equal the direct render, from the first block). The shared words are written into a copy of the dump. dsp_host maps P and X separately outside the
window's alias, so this proves the stub's logic and register handling, not the hardware.
"""
import json
import math
import pathlib
import struct
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1])); import toolpath  # noqa: E402,F401
import send_probe  # noqa: E402
from remix import registry  # noqa: E402

MAGIC = 0xB0A5ED
SHARED = 0x33DA3                         # effect 0's entry: BOUND, real init, real proc (modules/dlcopy/dlcopy.asm)
DLC = 0x33DC3                            # DLCOPY's hook entry, called as an init
HOST = "vendor/dsp56300/build/source/dsp_host/dsp_host"
FRAMES, BLOCKS = 16, 200
TMP = pathlib.Path("out/_dlstub")
TMP.mkdir(parents=True, exist_ok=True)
fails = 0


def check(label, ok, detail=""):
    global fails
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{'  ' + detail if detail else ''}")
    fails += 0 if ok else 1


MOD = registry.by_name("modulation")
mem = send_probe.dump_mem("out/mainos_bus.bin", TMP / "dlspike_A.mem", "A")
rec = json.loads(pathlib.Path("out/dsp/demand_records.json").read_text())["MODULATION"]
init_m, proc_m = rec["init"], rec["proc"]                       # the real code, loaded on demand
init_s, proc_s = send_probe.entry_points(mem, MOD.menu.fx2_id)  # its id dispatches to the stub
init_n, proc_n = send_probe.entry_points(mem, 0x08)          # an unassigned id: the stock null stub
print(f"MODULATION init/proc P:0x{init_m:05x}/0x{proc_m:05x}; DLSTUB P:0x{init_s:05x}/0x{proc_s:05x}")


def with_words(src, dst, words):
    """A copy of the dump with X words at SHARED (the window is one memory; dsp_host reads X records)."""
    blob = pathlib.Path(src).read_bytes()
    end = blob.rindex(b"\xff")                      # the terminating record starts with 0xff
    rec = struct.pack("<BII", 1, SHARED, len(words)) + b"".join(struct.pack("<I", w) for w in words)
    pathlib.Path(dst).write_bytes(blob[:end] + rec + blob[end:])


samples = []
for i in range(FRAMES * BLOCKS):
    v = int(0.4 * 8388607 * math.sin(2 * math.pi * 220 * i / 44100) + 0.1 * 8388607 * math.sin(2 * math.pi * 3100 * i / 44100))
    samples += [v, -v // 2]
(TMP / "in.raw").write_bytes(b"".join(struct.pack("<i", v) for v in samples))
knobs = {p.name.decode(): (p.default or 0) for p in MOD.params}
knobs["MIX"], knobs["DPTH"] = 100, 90
vals = [knobs.get(p.name.decode(), 0) if p.name else 0 for p in MOD.params]


def run(memfile, init, proc, tag):
    out = TMP / f"{tag}.raw"
    cmd = [HOST, "-mem", str(memfile), "-init", f"{init:x}", "-proc", f"{proc:x}", "-inst", "1", "-r7", "1", "-alloc", "0",
           "-inmask", "1", "-frames", str(FRAMES), "-blocks", str(BLOCKS), "-in", str(TMP / "in.raw"),
           "-out", str(out), "-params", ",".join(str(v) for v in vals)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"dsp_host failed ({tag}):\n{r.stdout[-600:]}\n{r.stderr[-600:]}")
    d = out.read_bytes()
    return list(struct.unpack(f"<{len(d) // 4}i", d))


src = list(struct.unpack(f"<{len(samples)}i", (TMP / "in.raw").read_bytes()))
direct = run(mem, init_m, proc_m, "direct")
check("direct: MODULATION changes the audio (the reference is not a passthrough)", direct != src)

dry = run(mem, init_n, proc_n, "null")
check("null stub: the dry reference differs from the direct render", dry != direct)
unbound = run(mem, init_s, proc_s, "unbound")
check("unbound: the stub's output equals the null stub's", unbound == dry)

with_words(mem, TMP / "bound.mem", [MAGIC, init_m, proc_m])
bound = run(TMP / "bound.mem", init_s, proc_s, "bound")
check("bound: the output equals MODULATION's direct render, sample for sample", bound == direct,
      f"{sum(a != b for a, b in zip(bound, direct))} of {len(direct)} samples differ")

with_words(mem, TMP / "wrongmagic.mem", [MAGIC ^ 1, init_m, proc_m])
check("wrong magic: still dry", run(TMP / "wrongmagic.mem", init_s, proc_s, "wrongmagic") == dry)

# ---- the copier: a staged block moves the code into the window and binds it ----
CODE_AT, STAGE = 0x35000, 0x2900


def records(path):
    """[(space, address, [words])] of a dump, without the terminator."""
    blob, pos, out = pathlib.Path(path).read_bytes(), 0, []
    while pos + 9 <= len(blob):
        sp, addr, cnt = struct.unpack_from("<BII", blob, pos)
        pos += 9
        if sp == 0xFF:
            break
        out.append((sp, addr, list(struct.unpack_from(f"<{cnt}I", blob, pos))))
        pos += 4 * cnt
    return out


def write_records(path, recs):
    path.write_bytes(b"".join(struct.pack("<BII", sp, a, len(w)) + struct.pack(f"<{len(w)}I", *w) for sp, a, w in recs)
                     + struct.pack("<BII", 0xFF, 0, 0))


recs = records(mem)
code = next(w for sp, a, w in recs if sp == 0 and a == CODE_AT)
N = len(code)
check("the dump holds MODULATION's code at P:0x35000", init_m == CODE_AT and N > 1000, f"{N} words")
gone = [(sp, a, [0] * len(w) if (sp == 0 and a == CODE_AT) else w) for sp, a, w in recs]      # the code is not resident at boot
halves = []
for w in code:
    halves += [w >> 8, w & 0xFF]
WIN = 0x30000                      # staged addresses are window offsets: the host write delivers 16 bits
staged = [0xA55A, 0, CODE_AT - WIN, N, init_m - WIN, proc_m - WIN] + halves


def variant(name, doorbell=True, stage=True):
    words = list(staged)
    if not doorbell:
        words[0] = 0
    write_records(TMP / f"{name}.mem", gone + ([(1, STAGE, words)] if stage else []))
    return TMP / f"{name}.mem"


cold = run(variant("cold", stage=False), init_s, proc_s, "cold")
check("not staged, code absent: the stub stays dry", cold == dry)
half = run(variant("nobell", doorbell=False), init_s, proc_s, "nobell")
check("staged without the doorbell: still dry", half == dry)
half_c = run(variant("nobell", doorbell=False), DLC, proc_s, "nobell_copy")
loaded = run(variant("loaded"), DLC, proc_s, "loaded")
check("staged with the doorbell: the copier binds it and the stub runs the real code from block 0, as a bound render does",
      loaded == direct, f"{sum(x != y for x, y in zip(loaded, direct))} of {len(direct)} samples differ")
check("staged without the doorbell: the copier leaves the stub dry", half_c == dry)

# ---- withdrawn: N = 0 clears BOUND and the span ----
off_words = [0xA55A, 0, 0, 0, 0, 0]
bound_recs = records(TMP / "bound.mem")
write_records(TMP / "withdraw.mem", bound_recs + [(1, STAGE, off_words)])
check("withdrawn after a bind: the stub is dry again",
      run(TMP / "withdraw.mem", DLC, proc_s, "withdraw") == dry)

print("PASS" if not fails else f"{fails} FAIL")
sys.exit(1 if fails else 0)
