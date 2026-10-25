# `pextprobe` -- PEXT PROBE

A measurement instrument: how far does P memory reach above `P:0x2000` on each
DSP core? Hot reload (the proof of concept on the hot-reload branch) puts swapped effects above the stock code; `DSP.md` section 3 records
`P:0x2000` as executable (a relocated CHORUS ran on the unit) and the upper
bound as unmeasured. This probe measures it. It ships in no remix but
`remixes/test/pext-probe`.

It is an insert on EQUALIZER's id (every id 4..31 is taken). Its output replaces
its track's audio with a status word, 32 bits a frame, one per sample slot, and
a capture of the track's audio reads it with `decode.py`.

## The ladder

Seven rungs, one every 64 frames (23 ms) after GO is turned on: `P:0x3fe0`,
`0x5fe0`, `0x7fe0`, `0x9fe0`, `0xbfe0`, `0xdfe0`, `0xffe0`, the top 32 words of
each 8 K block above the first. Each is congruent to the base `P:0x1fe0` modulo
`0x2000`, and `P:0x1fe0..0x1fff` is unused on both payloads (A's top is
`0x1fdf`, B's `0x1d9f`), so a rung that wraps onto a power-of-two memory lands
on spare words. A rung writes SENTINEL (`0x5a5a5a`) to the base and PATTERN
(`0x123456`) to the rung, then reads:

| result | meaning |
|---|---|
| REAL | the rung holds PATTERN and the base still holds SENTINEL: its own memory |
| ALIAS | the base holds PATTERN: the address wrapped onto the base; the memory is `(rung + 1) * 0x2000` words |
| ABSENT | neither: reads do not return what was written |
| frames stop | the core froze on the rung: the last frames name it |

The first rung that is not REAL gives the extent: ALIAS at rung k means P is
`(k + 1) * 0x2000` words (8 K granularity); ABSENT at rung k means it ends
before `(k + 1) * 0x2000 + 0x1fe0`. The frame's layout is at the head of
`pextprobe.asm`.

Under `dsp_host` every rung reads REAL (the emulator maps P at all of them), so
`tools/verify/verify_pextprobe.py` proves the instrument and the decoder
(`tools/verify/tests/test_pextprobe.py` the three outcomes and a frozen core on
synthetic frames). Nothing here says what the chip does. A form the chip has
not run: a P store through `(r1)`; the stock listing has absolute stores
(`move x0,p:>$58c`), `dsp_asm` takes the register-indirect one.

## Running it on a unit

1. `make image REMIX=pext-probe BUILD=<n>`, flash it (`docs/guide/BUILDING.md`).
   The remix carries USB audio out, TRACKS PRE (16 channels, the tracks).
2. On the unit: set FX1 of track 1 (core 1) and of track 5 (core 0) to PEXT
   PROBE; GO stays OFF. Each instance tests its own core.
3. Start a capture of the USB audio, all channels, 44.1 kHz, 24-bit or float.
4. Decode the pairs of tracks 1 and 5 (channels 0, 1 and 8, 9):
   `python3 modules/pextprobe/decode.py capture.wav --channels 0 1`.
   Expected: `frames ... with the marker`, GO 0, next rung 0, all rungs
   `untested`, frames arriving. No marker: the probe is not on that channel
   pair, or not on the track.
5. With the capture running, set GO to RUN on track 5, wait 10 s, decode again;
   then the same on track 1. The ladder takes 7 * 64 + 64 frames, about 0.2 s.
6. If frames stop arriving, the core froze on the rung the decoder names:
   power-cycle the unit (no reflash). Decode the capture as it stands.

Expected numbers are in the table above, not a prediction. The probe does not
write anywhere a running payload reads (the base is spare words, a rung is
above all stock code) except where a rung wraps onto something other than the
base, which only a non-power-of-two memory size could do.

## Files

`pextprobe.asm` (generated from seven rungs; the rung block is the same with
each address), `manifest.py`, `decode.py`, and
[`remixes/test/pext-probe`](../../remixes/test/pext-probe/README.md).
