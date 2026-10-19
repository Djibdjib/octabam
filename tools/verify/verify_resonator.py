#!/usr/bin/env python3
"""RESONATOR — must RING after a hit, not just EQ the dry."""
import pathlib, struct, subprocess, sys, math

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import toolpath  # noqa: E402,F401
import send_probe
from remix import registry

MOD = registry.by_name("resonator")
SEND = registry.by_name("send")
K = MOD.knob_map()
MEM = f"out/dsp/_audition_{MOD.name}_A.mem"
HOST = "vendor/dsp56300/build/source/dsp_host/dsp_host"
FXID = MOD.menu.fx2_id
FRAMES = 16
FS = 44100.0
TMP = pathlib.Path("out/_rsgate")
TMP.mkdir(parents=True, exist_ok=True)

pathlib.Path(MEM).unlink(missing_ok=True)
subprocess.run([sys.executable, "tools/remix/audition.py", MOD.name,
                "out/dry/drums_110.wav"], capture_output=True)
if not pathlib.Path(MEM).exists():
    sys.exit(f"no {MEM}")
init, proc = send_probe.entry_points(MEM, FXID)
if (init, proc) == send_probe.entry_points(MEM, SEND.menu.fx2_id):
    sys.exit("SEND alias")
print(f"entries: init=P:0x{init:04x} proc=P:0x{proc:04x}")

DEFAULTS = [(p.default or 0) for p in MOD.params]


def params(**kw):
    v = list(DEFAULTS)
    for name, val in kw.items():
        v[K[name]] = val
    return v


def render(samples, fx2=False, **kw):
    n = len(samples) - len(samples) % FRAMES
    src, out = TMP / "in.raw", TMP / "out.raw"
    src.write_bytes(b"".join(struct.pack("<i", m) for m in samples[:n]))
    cmd = [HOST, "-mem", MEM, "-init", f"{init:x}", "-proc", f"{proc:x}",
           "-inst", "1", "-r7", "1", "-alloc", "4000" if fx2 else "0",
           "-inmask", "1", "-frames", str(FRAMES), "-blocks", str(n // FRAMES),
           "-in", str(src), "-out", str(out),
           "-params", ",".join(str(x) for x in params(**kw))]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"dsp_host failed:\n{r.stdout}\n{r.stderr}")
    w = struct.unpack(f"<{len(out.read_bytes()) // 4}i", out.read_bytes())
    return list(w[0::2])[:n], list(w[1::2])[:n]


FAILS = []


def check(label, ok):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        FAILS.append(label)


def tone(hz, n, amp=0.35):
    return [int(amp * (1 << 23) * math.sin(2 * math.pi * hz * i / FS))
            for i in range(n)]


N = 8192
ramp = [int((i * 2 * (1 << 23) // 4096) - (1 << 23)) for i in range(4096)]

L, R = render(ramp, MIX=0, PIT1=40, PIT2=60, PIT3=80, PIT4=100, DECY=40)
check("MIX 0 bit-exact", L == ramp[:len(L)] and R == ramp[:len(R)])

hit = [0] * 64 + [int(0.5 * (1 << 23))] + [0] * (N - 65)
Lh, _ = render(hit, MIX=127, PIT1=50, PIT2=64, PIT3=80, PIT4=96, DECY=127)
early = sum(abs(x) for x in Lh[65:65 + 512])
late = sum(abs(x) for x in Lh[65 + 2000:65 + 4000])
check(f"post-hit EARLY energy ({early})", early > 100_000)
ratio = (late / early) if early else 0.0
check(f"RING not EQ: late/early={ratio:.3f} (need >0.15)", ratio > 0.15)
check(f"late tail still loud ({late})", late > 50_000)

Lh_lo, _ = render(hit, MIX=127, PIT1=50, PIT2=64, PIT3=80, PIT4=96, DECY=10)
late_lo = sum(abs(x) for x in Lh_lo[65 + 2000:65 + 4000])
check(f"DECY127 rings longer than DECY10 ({late} > {late_lo})", late > late_lo * 2)

off = tone(3000, N)
Lmix, _ = render(off, MIX=127, PIT1=40, PIT2=50, PIT3=60, PIT4=70, DECY=127)


def _corr(a, b):
    n = len(a)
    ma = sum(a) / n
    mb = sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return abs(num / (da * db)) if da * db else 0.0


r_dry = _corr(Lmix[2048:4096], off[2048:4096])
check(f"no dry track DECY127 corr={r_dry:.3f} (need <0.40)", r_dry < 0.40)

ton = tone(500, N)
Lon, _ = render(ton, MIX=127, PIT1=70, PIT2=70, PIT3=70, PIT4=70,
                GN1=64, GN2=64, GN3=64, GN4=64, DECY=64)
Loff, _ = render(tone(3000, N), MIX=127, PIT1=70, PIT2=70, PIT3=70, PIT4=70,
                 GN1=64, GN2=64, GN3=64, GN4=64, DECY=64)
e_on = sum(abs(x) for x in Lon[512:])
e_off = sum(abs(x) for x in Loff[512:])
dry_e = sum(abs(x) for x in ton[512:])
check(f"BP selects ({e_on} > {e_off})", e_on > e_off * 1.25)
check(f"wet loud vs dry on pitch ({e_on} vs {dry_e})", e_on > dry_e * 0.25)

Lz, _ = render(hit, MIX=127, GN1=0, GN2=0, GN3=0, GN4=0, DECY=127)
ez = sum(abs(x) for x in Lz[65:65 + 4000])
check(f"GN all 0 silent ({ez})", ez < 1000)

Lhi, _ = render(hit, MIX=127, GN1=127, GN2=127, GN3=127, GN4=127,
                SCAL=8, DECY=127)
Lmid, _ = render(hit, MIX=127, GN1=64, GN2=64, GN3=64, GN4=64,
                 SCAL=8, DECY=127)
e_hi = sum(abs(x) for x in Lhi[65:65 + 512])
e_mid = sum(abs(x) for x in Lmid[65:65 + 512])
check(f"GN127 hotter than GN64 ({e_hi} > {e_mid})", e_hi > e_mid * 1.2)

Ltn, _ = render(hit, MIX=127, GN1=64, GN2=64, GN3=64, GN4=64,
                SCAL=127, DECY=127)
Ltame, _ = render(hit, MIX=127, GN1=64, GN2=64, GN3=64, GN4=64,
                  SCAL=8, DECY=127)
e_tn = sum(abs(x) for x in Ltn[65:65 + 512])
e_tame = sum(abs(x) for x in Ltame[65:65 + 512])
check(f"SCAL127 hotter than SCAL8 ({e_tn} > {e_tame})", e_tn > e_tame * 4)

L, R = render(ramp, fx2=True, MIX=127)
check("FX2 dry", L == ramp[:len(L)] and R == ramp[:len(R)])

if FAILS:
    sys.exit(f"{len(FAILS)} FAIL: {FAILS}")
print("verify_resonator: all PASS — ring gate green")
