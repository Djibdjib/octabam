#!/usr/bin/env python3
"""STUTTR render gates.

  MIX=0       -> bit-exact passthrough
  LOOP        -> energy on a tone
  REV/SCRAM   -> non-silent when engaged
  DROP        -> renders
  SIZE        -> spike after clear repeats at ~(kn+1)^2/2 sample gaps
  RATE slow   -> several SIZE loops land before the next grab
  JITR        -> high knobs change grab start vs JITR=0
  JITR dist   -> many grabs at 127: peak offsets not constant
  DECY        -> 0 = hold, higher = faster fade into dry (quadratic step)
  FDBK        -> recirculate changes the ring vs FDBK=0
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


N = 4800
ramp = [((i % 200) - 100) * (1 << 16) for i in range(N)]
tone = [int(0.3 * (1 << 23) * __import__("math").sin(2 * 3.14159265 * 440 * i / 44100))
        for i in range(N)]

print("STUTTR gates")
L, R = render(ramp, MIX=0, SIZE=80, RATE=100, JITR=0, MODE=0)
check("MIX=0 bit-exact", L == ramp and R == ramp,
      f"max|d|={max(abs(a - b) for a, b in zip(L, ramp))}")

# DECY=0 holds each grain for SIZE/RATE gap checks.
E_dry = sum(x * x for x in render(tone, MIX=0)[0])
E_loop = sum(x * x for x in render(tone, JITR=0, MIX=127, SIZE=40, RATE=110,
                                   MODE=0, DECY=0)[0])
check("LOOP energy", E_loop > E_dry * 0.2,
      f"Edry={E_dry} Eloop={E_loop}")

Lr, _ = render(tone, JITR=0, MIX=127, SIZE=40, RATE=110, MODE=1, DECY=0)
check("REV non-silent", max(abs(x) for x in Lr) > (1 << 16),
      f"peak={max(abs(x) for x in Lr)}")

Ls, _ = render(tone, JITR=0, MIX=127, SIZE=60, RATE=100, MODE=3, DECY=0)
check("SCRAM non-zero", max(abs(x) for x in Ls) > (1 << 14),
      f"peak={max(abs(x) for x in Ls)}")

Ld, _ = render(tone, JITR=0, MIX=127, SIZE=40, RATE=110, MODE=2, DECY=0)
check("DROP renders", len(Ld) == len(tone) - len(tone) % FRAMES)

Nspike = CLEAR + 12000


def size_words(kn):
    w = (kn + 1) ** 2
    if w < 8:
        w = 8
    return w & ~1


def size_frames(kn):
    return size_words(kn) // 2


def spike_in(kn):
    s = [0] * Nspike
    s[CLEAR + size_frames(kn) - 2] = 1 << 22
    return s


for kn in (0, 8, 16):
    expect = size_frames(kn)
    Lw, _ = render(spike_in(kn), SIZE=kn, RATE=0, JITR=0, MIX=127, MODE=0,
                   DECY=0, FDBK=0)
    peaks, gaps = peak_gaps(Lw)
    good = [g for g in gaps if abs(g - expect) <= 2]
    check(f"SIZE={kn} loop gap~{expect}",
          len(peaks) >= 3 and len(good) >= 2,
          f"peaks={len(peaks)} gaps={gaps[:6]} matched={len(good)}")

g8 = peak_gaps(render(spike_in(8), SIZE=8, RATE=0, JITR=0, MIX=127, MODE=0,
                      DECY=0, FDBK=0)[0])[1]
g32 = peak_gaps(render(spike_in(32), SIZE=32, RATE=0, JITR=0, MIX=127, MODE=0,
                       DECY=0, FDBK=0)[0])[1]
med = lambda gs: sorted(gs)[len(gs) // 2] if gs else 0
check("SIZE mid dial still lengthens", med(g8) < med(g32) and med(g8) > 0,
      f"med8={med(g8)} med32={med(g32)}")

Lt, _ = render(tone + tone, SIZE=40, RATE=40, JITR=0, MIX=127, MODE=0, DECY=0)
check("tone stays loud", max(abs(x) for x in Lt[CLEAR:]) > (1 << 20),
      f"peak={max(abs(x) for x in Lt[CLEAR:])}")

Lbig, _ = render(spike_in(16), SIZE=16, RATE=20, JITR=0, MIX=127, MODE=0,
                 DECY=0, FDBK=0)
gaps_r = peak_gaps(Lbig)[1]
good_r = [g for g in gaps_r if abs(g - size_frames(16)) <= 2]
check("RATE=20 keeps SIZE loop",
      len(good_r) >= 2,
      f"gaps={gaps_r[:6]} expect~{size_frames(16)}")

Lj0, _ = render(spike_in(16), SIZE=16, RATE=0, JITR=0, MIX=127, MODE=0,
                DECY=0, FDBK=0)
Lj1, _ = render(spike_in(16), SIZE=16, RATE=0, JITR=127, MIX=127, MODE=0,
                DECY=0, FDBK=0)
check("JITR changes output vs 0", Lj0 != Lj1,
      f"identical={Lj0 == Lj1}")
g_j0 = peak_gaps(Lj0)[1]
good_j0 = [g for g in g_j0 if abs(g - size_frames(16)) <= 2]
check("JITR=0 locks SIZE gap", len(good_j0) >= 2,
      f"gaps={g_j0[:6]} matched={len(good_j0)}")

# Grab-start distribution at JITR=127: many re-grabs of a long tone. A stuck
# LFSR makes every SIZE-length grain identical once the ring is full; a live
# one yields several distinct grain fingerprints.
Nlong = 9600
tone_long = [int(0.35 * (1 << 23) * __import__("math").sin(
    2 * 3.14159265 * 220 * i / 44100)) for i in range(Nlong)]
# kn SIZE=24 -> (25)^2=625 words; RATE=110 for frequent re-grabs
Ldist, _ = render(tone_long, SIZE=16, RATE=120, JITR=127, MIX=127, MODE=0,
                  DECY=0, FDBK=0)
grain = (16 + 1) ** 2  # words; L-only list is one sample per word roughly
# skip the clear + first fill; then fingerprint successive grains
fps = []
for g0 in range(CLEAR + grain, Nlong - grain, grain):
    seg = tuple(Ldist[g0:g0 + min(64, grain)])  # first 64 samples of each grain
    if any(abs(x) > 1000 for x in seg):
        fps.append(seg)
uniq_fp = len(set(fps))
check("JITR grab-start distribution not constant",
      len(fps) >= 3 and uniq_fp >= 3,
      f"grains={len(fps)} unique_fps={uniq_fp}")



Ndec = CLEAR + 20000
g = size_frames(32)
grab = CLEAR + g

tone_d = [int(0.25 * (1 << 23) * math.sin(2 * 3.14159265 * 220 * i / 44100))
          for i in range(Ndec)]


def _wet_res(out, dry, lo, hi):
    return sum((a - b) * (a - b) for a, b in zip(out[lo:hi], dry[lo:hi]))


def _energy(xs, lo, hi):
    return sum(x * x for x in xs[lo:hi])


Lhold = render(tone_d, SIZE=32, RATE=0, JITR=0, MIX=127, DECY=0, FDBK=0)[0]
L64 = render(tone_d, SIZE=32, RATE=0, JITR=0, MIX=127, DECY=64, FDBK=0)[0]
L127 = render(tone_d, SIZE=32, RATE=0, JITR=0, MIX=127, DECY=127, FDBK=0)[0]
mid_lo, mid_hi = grab + g // 4, grab + (3 * g) // 4
check("active kills dry (MIX127)",
      _wet_res(Lhold, tone_d, mid_lo, mid_hi) > _energy(tone_d, mid_lo, mid_hi) // 4,
      f"res={_wet_res(Lhold, tone_d, mid_lo, mid_hi)}")

early127 = _energy(L127, grab, grab + g // 4)
late127 = _energy(L127, grab + (3 * g) // 4, grab + g - 2)
check("DECY fades within first grain",
      late127 < early127 // 2,
      f"early={early127} late={late127}")
hold0 = _energy(Lhold, grab + g // 2, grab + g - 2)
fade127 = _energy(L127, grab + g // 2, grab + g - 2)
check("DECY 0 holds vs 127",
      fade127 < hold0 // 4,
      f"hold0={hold0} fade127={fade127}")

nz64 = sum(1 for x in L64[grab:grab + g] if abs(x) > 1000)
check("DECY=64 spans most of grain", nz64 > (3 * g) // 4,
      f"nz={nz64} grain={g}")

Lf0, _ = render(spike_in(16), SIZE=16, RATE=0, JITR=0, MIX=127, MODE=0,
                DECY=0, FDBK=0)
Lf1, _ = render(spike_in(16), SIZE=16, RATE=0, JITR=0, MIX=127, MODE=0,
                DECY=0, FDBK=127)
check("FDBK changes output vs 0", Lf0 != Lf1,
      f"identical={Lf0 == Lf1}")

for name in K:
    render(ramp[:FRAMES * 8], **{name: 64})
check("every named knob renders", True)
assert "JITR" in K and "CHNC" not in K, f"knobs={sorted(K)}"

if FAILS:
    sys.exit(f"verify_stuttr: {len(FAILS)} FAILED: {', '.join(FAILS)}")
print("verify_stuttr: OK")
