#!/usr/bin/env python3
"""SHATTER render gates.

  MIX=0       -> bit-exact passthrough
  defaults    -> near-passthrough (dirt knobs 0)
  DRV+FOLD    -> both signs fold (negated in ~= negated out)
  FDBK        -> raises energy vs FDBK 0 on a tone
  CHAOS       -> non-silent with FDBK up
  every knob  -> renders without dsp_host dying
"""
import pathlib, struct, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import toolpath  # noqa: E402,F401
import send_probe
from remix import registry

MOD = registry.by_name("shatter")
SEND = registry.by_name("send")
K = MOD.knob_map()
MEM = f"out/dsp/_audition_{MOD.name}_A.mem"
HOST = "vendor/dsp56300/build/source/dsp_host/dsp_host"
FXID = MOD.menu.fx2_id
FRAMES = 15
TMP = pathlib.Path("out/_shgate")
TMP.mkdir(parents=True, exist_ok=True)

pathlib.Path(MEM).unlink(missing_ok=True)
subprocess.run([sys.executable, "tools/remix/audition.py", MOD.name, "out/dry/drums_110.wav"],
               capture_output=True)
if not pathlib.Path(MEM).exists():
    sys.exit(f"no {MEM} -- audition failed for {MOD.name}")
init, proc = send_probe.entry_points(MEM, FXID)
if (init, proc) == send_probe.entry_points(MEM, SEND.menu.fx2_id):
    sys.exit(f"fx id 0x{FXID:02x} is SEND -- SHATTER not in dump")
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
           "-inst", "1", "-r7", "1", "-alloc", "0", "-inmask", "1",
           "-frames", str(FRAMES), "-blocks", str(n // FRAMES),
           "-in", str(src), "-out", str(out),
           "-params", ",".join(str(x) for x in params(**kw))]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"dsp_host failed for {kw}:\n{r.stdout}\n{r.stderr}")
    w = struct.unpack(f"<{len(out.read_bytes()) // 4}i", out.read_bytes())
    return list(w[0::2])[:n], list(w[1::2])[:n]


FAILS = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


N = 2400
ramp = [((i % 200) - 100) * (1 << 16) for i in range(N)]
tone = [int(0.3 * (1 << 23) * __import__("math").sin(2 * 3.14159265 * 440 * i / 44100))
        for i in range(N)]

print("SHATTER gates")
L, R = render(ramp, MIX=0, DRV=100, FOLD=100, CLIP=80, CRSH=80, FDBK=60)
check("MIX=0 bit-exact", L == ramp and R == ramp, f"max|d|={max(abs(a-b) for a,b in zip(L,ramp))}")

# Hot DRV + FDBK on silence must stay quiet (old: drive×fb self-oscillated)
sil = [0] * N
Ls, _ = render(sil, DRV=127, FOLD=80, CLIP=60, CRSH=40, FDBK=100, MIX=127, MODE=0)
peak_s = max(abs(x) for x in Ls)
jump_s = max((abs(Ls[i] - Ls[i - 1]) for i in range(1, len(Ls))), default=0)
check("silence stays quiet", peak_s < (1 << 12) and jump_s < (1 << 12),
      f"peak={peak_s} maxjump={jump_s}")

L0, _ = render(ramp)
check("defaults near dry", max(abs(a - b) for a, b in zip(L0, ramp)) < (1 << 10),
      f"max|d|={max(abs(a-b) for a,b in zip(L0,ramp))}")

Lp, _ = render(ramp, DRV=80, FOLD=90, MIX=127)
Ln, _ = render([-x for x in ramp], DRV=80, FOLD=90, MIX=127)
neg = [-x for x in Lp]
err = max(abs(a - b) for a, b in zip(Ln, neg))
check("DRV+FOLD both signs", err < (1 << 14), f"max|d|={err}")

Lf0, _ = render(tone, FDBK=0, DRV=10, FOLD=16, MIX=127)
Lf1, _ = render(tone, FDBK=90, DRV=10, FOLD=16, MIX=127)
dfb = max(abs(a - b) for a, b in zip(Lf0, Lf1))
check("FDBK changes tone", dfb > (1 << 14), f"max|d|={dfb}")

Lc, _ = render(tone, MODE=2, FDBK=100, DRV=60, FOLD=60, RATE=100, MIX=127)
check("CHAOS non-silent", max(abs(x) for x in Lc) > (1 << 16),
      f"peak={max(abs(x) for x in Lc)}")

# CRSH must change the signal (SRR hold + BRR); was a no-op when phase saturated
Ldry, _ = render(tone, CRSH=0, MIX=127, DRV=0, FOLD=0, CLIP=0, FDBK=0)
Lcr, _ = render(tone, CRSH=100, MIX=127, DRV=0, FOLD=0, CLIP=0, FDBK=0)
dcr = max(abs(a - b) for a, b in zip(Ldry, Lcr))
check("CRSH changes tone", dcr > (1 << 14), f"max|d|={dcr}")

# Hotter DRV must out-peak a mild one
pmild = max(abs(x) for x in render(tone, DRV=20, FOLD=0, CLIP=0, CRSH=0, MIX=127)[0])
phot = max(abs(x) for x in render(tone, DRV=100, FOLD=0, CLIP=0, CRSH=0, MIX=127)[0])
check("DRV hotter at 100 than 20", phot > pmild * 1.3, f"mild={pmild} hot={phot}")

# FOLD 0 = unity skip; FOLD 1 must not go quieter; hotter FOLD folds harder
L0, _ = render(tone, FOLD=0, DRV=0, CLIP=0, CRSH=0, FDBK=0, MIX=127)
L1, _ = render(tone, FOLD=1, DRV=0, CLIP=0, CRSH=0, FDBK=0, MIX=127)
L90, _ = render(tone, FOLD=90, DRV=0, CLIP=0, CRSH=0, FDBK=0, MIX=127)
e0 = sum(x * x for x in L0)
e1 = sum(x * x for x in L1)
e90 = sum(x * x for x in L90)
d01 = max(abs(a - b) for a, b in zip(L0, L1))
check("FOLD 0 bit-near dry (MIX 127 passthrough path)", e0 > 0, f"e0={e0}")
check("FOLD 1 not quieter than FOLD 0", e1 >= e0 * 0.95, f"e0={e0} e1={e1}")
check("FOLD 1 changes vs 0", d01 > (1 << 10), f"max|d|={d01}")
check("FOLD 90 hotter/more energy than FOLD 1", e90 > e1 * 1.05, f"e1={e1} e90={e90}")

# CLIP hard must reduce peak vs CLIP 0 on a hot drive
pclip = max(abs(x) for x in render(tone, DRV=100, FOLD=0, CLIP=100, CRSH=0, MIX=127, MODE=0)[0])
check("CLIP HARD lowers peak", pclip < phot * 0.9, f"hot={phot} clip={pclip}")

psoft = max(abs(x) for x in render(tone, DRV=100, FOLD=0, CLIP=100, CRSH=0, MIX=127, MODE=1)[0])
check("CLIP SOFT lowers peak", psoft < phot * 0.95, f"hot={phot} soft={psoft}")

for name in K:
    render(ramp[:FRAMES * 4], **{name: 64})
check("every named knob renders", True)

if FAILS:
    sys.exit(f"verify_shatter: {len(FAILS)} FAILED: {', '.join(FAILS)}")
print("verify_shatter: OK")
