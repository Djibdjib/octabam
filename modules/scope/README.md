# `scope` — SCOPE

Full-screen **OSC**, **XY**, or **ALL** (4×2 mini OSC: T1–T4 left column,
T5–T8 right, centre divider).

**DOWN + TEMPO** opens; **UP + TEMPO** = [TUNER](../tuner/README.md).
**UP** / **DOWN** cycle. **RIGHT** help; **LEFT** back.
**Push A** = GAIN default + clear peak. **CUE** release = G/P HUD.

| | A | B | C–F |
|---|---|---|---|
| **OSC** / **XY** / **ALL** | GAIN | TIME | — |

XY is a hotter scale than OSC. ALL cells follow the panel track pad layout.

**Measured:** `make check REMIX=test/scope` (port). **Inferred:** live
waveform needs track audio; quiet under the emulator live path (like
TUNER `--`). Not `Proof.HARDWARE` until a named tip is confirmed on unit.
