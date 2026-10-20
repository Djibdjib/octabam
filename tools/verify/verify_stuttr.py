#!/usr/bin/env python3
"""STUTTR render gates (chance-engage redesign).

  MIX=0       -> bit-exact passthrough
  CHNC=0      -> stays dry (wet residual ~0) with MIX 127
  CHNC=127    -> engages: wet residual while HOLD
  SIZE        -> spike repeats at ~(kn+1)^2/2 sample gaps
  HALF        -> loop gaps ~2x FWD
  REV=127     -> non-silent (and differs from REV=0 on a spike)
  HOLD short  -> returns toward dry after reload
  every knob  -> renders without dsp_host dying
"""
import math
import pathlib, struct, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import toolpath  # noqa: E402,F401
import send_probe
from remix import registry

MOD = registry.by_name("stuttr")
SEND = registry.by_name("send")
K = MOD.knob_map()
MEM = f"out/dsp/_audition_{MOD.name}_A.mem"
HOST = "vendor/dsp56300/build/source/dsp_host/dsp_host"
FXID = MOD.menu.fx2_id
FRAMES = 15
TMP = pathlib.Path("out/_stgate")
TMP.mkdir(parents=True, exist_ok=True)
CLEAR = 0x80 * FRAMES

pathlib.Path(MEM).unlink(missing_ok=True)
subprocess.run([sys.executable, "tools/remix/audition.py", MOD.name, "out/dry/drums_110.wav"],
               capture_output=True)
if not pathlib.Path(MEM).exists():
    sys.exit(f"no {MEM} -- audition failed for {MOD.name}")
init, proc = send_probe.entry_points(MEM, FXID)
if (init, proc) == send_probe.entry_points(MEM, SEND.menu.fx2_id):
    sys.exit(f"fx id 0x{FXID:02x} is SEND -- STUTTR not in dump")
print(f"entries: init=P:0x{init:04x} proc=P:0x{proc:04x}")

DEFAULTS = [(p.default or 0) for p in MOD.params]


def params(**kw):
    v = list(DEFAULTS)
    for name, val in kw.items():
        v[K[name]] = val
    return v


def render(samples, **kw):
    n = len(samples) - len(samples) % FRAMES
    src, out = TMP / "in.raw", TMP / "out.raw"
    src.write_bytes(b"".join(struct.pack("<i", m) for m in samples[:n]))
    cmd = [HOST, "-mem", MEM, "-init", f"{init:x}", "-proc", f"{proc:x}",
           "-inst", "1", "-r7", "1", "-alloc", "1", "-inmask", "1",
           "-frames", str(FRAMES), "-blocks", str(n // FRAMES),
           "-in", str(src), "-out", str(out),
           "-params", ",".join(str(x) for x in params(**kw))]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"dsp_host failed for {kw}:\n{r.stdout}\n{r.stderr}")
    w = struct.unpack(f"<{len(out.read_bytes()) // 4}i", out.read_bytes())
    return list(w[0::2])[:n], list(w[1::2])[:n]


def peak_gaps(xs, thr=(1 << 17)):
    peaks = [i for i, x in enumerate(xs) if abs(x) > thr]
    sep = []
    for p in peaks:
        if not sep or p - sep[-1] >= 2:
            sep.append(p)
    gaps = [sep[i + 1] - sep[i] for i in range(len(sep) - 1)]
    return sep, gaps


FAILS = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


def size_words(kn):
    w = (kn + 1) ** 2
    if w < 8:
        w = 8
    return w & ~1


def size_frames(kn):
    return size_words(kn) // 2


def hold_samples(kn, size_kn):
    h = (kn + 1) ** 2 * 16
    g = size_frames(size_kn)
    return max(h, g)


N = 4800
ramp = [((i % 200) - 100) * (1 << 16) for i in range(N)]
tone = [int(0.3 * (1 << 23) * math.sin(2 * math.pi * 440 * i / 44100))
        for i in range(N)]

print("STUTTR gates")
L, R = render(ramp, MIX=0, SIZE=80, RATE=100, CHNC=127, HOLD=40, MODE=0)
check("MIX=0 bit-exact", L == ramp and R == ramp,
      f"max|d|={max(abs(a - b) for a, b in zip(L, ramp))}")

E_dry = sum(x * x for x in render(tone, MIX=0)[0])
Lmiss, _ = render(tone, MIX=127, SIZE=40, RATE=120, CHNC=0, HOLD=80, MODE=0, REV=0)
res_miss = sum((a - b) * (a - b) for a, b in zip(Lmiss, tone[:len(Lmiss)]))
check("CHNC=0 stays dry", res_miss < E_dry // 1000 + 1,
      f"res={res_miss} Edry={E_dry}")

Lhit, _ = render(tone + tone, MIX=127, SIZE=40, RATE=120, CHNC=127, HOLD=100,
                 MODE=0, REV=0)
res_hit = sum((a - b) * (a - b) for a, b in zip(Lhit[CLEAR:], (tone + tone)[CLEAR:len(Lhit)]))
check("CHNC=127 engages", res_hit > E_dry // 4,
      f"res={res_hit}")

Nspike = CLEAR + 12000


def spike_in(kn):
    s = [0] * Nspike
    s[CLEAR + size_frames(kn) - 2] = 1 << 22
    return s


engage = dict(CHNC=127, HOLD=127, RATE=0, REV=0, MIX=127, MODE=0)

for kn in (0, 8, 16):
    expect = size_frames(kn)
    Lw, _ = render(spike_in(kn), SIZE=kn, **engage)
    peaks, gaps = peak_gaps(Lw)
    good = [g for g in gaps if abs(g - expect) <= 2]
    check(f"SIZE={kn} loop gap~{expect}",
          len(peaks) >= 3 and len(good) >= 2,
          f"peaks={len(peaks)} gaps={gaps[:6]} matched={len(good)}")

g8 = peak_gaps(render(spike_in(8), SIZE=8, **engage)[0])[1]
g32 = peak_gaps(render(spike_in(32), SIZE=32, **engage)[0])[1]
med = lambda gs: sorted(gs)[len(gs) // 2] if gs else 0
check("SIZE mid dial still lengthens", med(g8) < med(g32) and med(g8) > 0,
      f"med8={med(g8)} med32={med(g32)}")

# HALF: same spike, gaps ~2x FWD
Lf, _ = render(spike_in(8), SIZE=8, CHNC=127, HOLD=127, RATE=0, REV=0, MIX=127, MODE=0)
Lh, _ = render(spike_in(8), SIZE=8, CHNC=127, HOLD=127, RATE=0, REV=0, MIX=127, MODE=1)
gf, gh = peak_gaps(Lf)[1], peak_gaps(Lh)[1]
check("HALF gaps ~2x FWD",
      med(gf) > 0 and med(gh) >= med(gf) * 2 - 2,
      f"medFWD={med(gf)} medHALF={med(gh)}")

Lrev0, _ = render(spike_in(16), SIZE=16, CHNC=127, HOLD=127, RATE=0, REV=0, MIX=127, MODE=0)
Lrev1, _ = render(spike_in(16), SIZE=16, CHNC=127, HOLD=127, RATE=0, REV=127, MIX=127, MODE=0)
check("REV=127 changes vs 0", Lrev0 != Lrev1,
      f"identical={Lrev0 == Lrev1}")
check("REV=127 non-silent", max(abs(x) for x in Lrev1) > (1 << 16),
      f"peak={max(abs(x) for x in Lrev1)}")

# Short HOLD: first-fill grab, brief hold, then dry again
Nhold = CLEAR + 4000
tone_h = [int(0.25 * (1 << 23) * math.sin(2 * math.pi * 220 * i / 44100))
          for i in range(Nhold)]
# SIZE=0 -> 8 words / 4 frames; HOLD=0 -> reload max(16, 4) = 16 samples
Lshort, _ = render(tone_h, SIZE=0, RATE=0, CHNC=127, HOLD=0, MIX=127, MODE=0, REV=0)
grab0 = CLEAR + size_frames(0)
mid_lo = grab0 + 2
mid_hi = grab0 + 12
tail_lo = grab0 + 200
mid_res = sum((a - b) * (a - b)
              for a, b in zip(Lshort[mid_lo:mid_hi], tone_h[mid_lo:mid_hi]))
tail_res = sum((a - b) * (a - b)
               for a, b in zip(Lshort[tail_lo:tail_lo + 200],
                               tone_h[tail_lo:tail_lo + 200]))
check("HOLD short returns toward dry",
      mid_res > 1000 and tail_res < mid_res // 4,
      f"mid_res={mid_res} tail_res={tail_res}")

for name in K:
    render(ramp[:FRAMES * 8], **{name: 64 if name not in ("MODE", "SYNC") else 1})
check("every named knob renders", True)
assert "CHNC" in K and "HOLD" in K and "REV" in K, f"knobs={sorted(K)}"
assert "JITR" not in K and "DECY" not in K and "FDBK" not in K, f"knobs={sorted(K)}"

if FAILS:
    sys.exit(f"verify_stuttr: {len(FAILS)} FAILED: {', '.join(FAILS)}")
print("verify_stuttr: OK")
