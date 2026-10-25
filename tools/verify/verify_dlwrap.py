#!/usr/bin/env python3
"""DLWRAP under dsp_host: a stock reverb runs unchanged where its buffer is clear of loaded code, and stays off it where not.

    python3 tools/verify/verify_dlwrap.py

PLATE REV is rendered directly and through the wrapper, on the allocator slots that put its buffer at Y:0x4000,
0x8000, 0x30000 and 0x34000, with and without code published at P:0x35000..0x35618 (BOUND and the span words are
written into a copy of the dump). Clear of the code the wrapper's output and its Y writes equal the direct render's.
On the 0x34000 slot with code loaded the instance passes the audio through and writes nothing to Y. dsp_host keeps P
and Y apart, so what this proves is the wrapper's decision, not an overwrite on the chip.
"""
import math
import pathlib
import struct
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1])); import toolpath  # noqa: E402,F401
import send_probe  # noqa: E402

MAGIC, CODE_LO, CODE_HI = 0xB0A5ED, 0x35000, 0x35619
HOST = "vendor/dsp56300/build/source/dsp_host/dsp_host"
FRAMES, BLOCKS = 16, 120
TMP = pathlib.Path("out/_dlwrap")
TMP.mkdir(parents=True, exist_ok=True)
fails = 0


def check(label, ok, detail=""):
    global fails
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{'  ' + detail if detail else ''}")
    fails += 0 if ok else 1


mem = send_probe.dump_mem("out/mainos_bus.bin", TMP / "a.mem", "A")
init_p, proc_p = send_probe.entry_points(mem, 0x14)           # stock PLATE REV
init_w, proc_w = send_probe.entry_points(mem, 0x1E)           # DLWRAP
init_n, proc_n = send_probe.entry_points(mem, 0x08)           # the null stub
samples = []
for i in range(FRAMES * BLOCKS):
    v = int(0.4 * 8388607 * math.sin(2 * math.pi * 220 * i / 44100))
    samples += [v, -v // 2]
(TMP / "in.raw").write_bytes(b"".join(struct.pack("<i", v) for v in samples))


def published(name):
    """A copy of the dump with the shared words DLSTUB's copier would have written: BOUND, the span."""
    blob = mem.read_bytes()
    end = blob.rindex(b"\xff")
    words = {0x33DA6: CODE_LO, 0x33DA7: CODE_HI, 0x33DA3: MAGIC}      # effect 0's entry (modules/dlcopy/dlcopy.asm)
    rec = b"".join(struct.pack("<BII", 1, a, 1) + struct.pack("<I", w) for a, w in words.items())
    (TMP / f"{name}.mem").write_bytes(blob[:end] + rec + blob[end:])
    return TMP / f"{name}.mem"


def run(memfile, init, proc, alloc, tag):
    out, ydump = TMP / f"{tag}.raw", TMP / f"{tag}.y"
    cmd = [HOST, "-mem", str(memfile), "-init", f"{init:x}", "-proc", f"{proc:x}", "-inst", "1", "-alloc", str(alloc),
           "-r7", "1", "-inmask", "1", "-frames", str(FRAMES), "-blocks", str(BLOCKS), "-in", str(TMP / "in.raw"),
           "-out", str(out), "-params", "64,64,64,64,64,64", "-dumpy", f"4000,40000,{ydump}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"dsp_host failed ({tag}):\n{r.stdout[-600:]}\n{r.stderr[-600:]}")
    d, y = out.read_bytes(), ydump.read_bytes()
    return list(struct.unpack(f"<{len(d) // 4}i", d)), struct.unpack(f"<{len(y) // 4}I", y)


def wrote(y, lo, hi):
    """Non-zero Y words in [lo, hi): what the instance wrote there."""
    return sum(1 for a in range(lo, hi) if y[a - 0x4000])


loaded = published("loaded")
dry_out, _ = run(mem, init_n, proc_n, 1, "null")
for alloc, base in ((1, 0x4000), (3, 0x8000), (5, 0x30000), (7, 0x34000)):
    d_out, d_y = run(mem, init_p, proc_p, alloc, f"direct{alloc}")
    w_out, w_y = run(mem, init_w, proc_w, alloc, f"clear{alloc}")
    check(f"no code loaded, buffer at Y:0x{base:05x}: the wrapper equals the stock render", w_out == d_out and w_y == d_y)
    check(f"no code loaded, buffer at Y:0x{base:05x}: the reverb really wrote its buffer", wrote(d_y, base, base + 0x400) > 0)
    w_out, w_y = run(loaded, init_w, proc_w, alloc, f"loaded{alloc}")
    covers = base < CODE_HI and base + 0x3800 > CODE_LO
    if covers:
        check(f"code loaded, buffer at Y:0x{base:05x} covers it: the instance passes the audio through", w_out == dry_out)
        check(f"code loaded, buffer at Y:0x{base:05x} covers it: nothing is written to the buffer", wrote(w_y, base, base + 0x3800) == 0)
    else:
        check(f"code loaded, buffer at Y:0x{base:05x} clear of it: the wrapper equals the stock render", w_out == d_out and w_y == d_y)

print("PASS" if not fails else f"{fails} FAIL")
sys.exit(1 if fails else 0)
