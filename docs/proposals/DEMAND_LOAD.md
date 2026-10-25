# Demand loading of window effects

25-26 Oct 2026. ✅ measured (port, or unit where stated), 🟡 inferred, ⬜ not looked at. Nothing here has run on a unit.
Addresses are `P:` / `X:` / `Y:` DSP words, or ColdFire virtual addresses where they start `0x4`.

## What it does

Every stock effect stays and works as stock. SPECTRUM, CHARACTER, MODULATION and TRANSIENT are in the effect list and are
copied into the DSP's shared window while a track uses them, and withdrawn when no track does. Nothing of stock is removed,
replaced or shrunk. The window is stock's buffer memory, so the code goes only where no running stock effect writes.

`remixes/octabam` is built this way. `remixes/test/dlspike` is the same with one effect, for the gates.

## Constraints

| fact | status |
|---|---|
| P is 8K per core and full with the 13 stock DSP effects; P above `0x1fff` is absent | ✅ unit (`modules/pextprobe`) |
| Code written into the window ran from both cores; the window `0x30000..0x3ffff` is one memory, P, X and Y alias | ✅ unit |
| FX2 instance *k* of a core has its buffer at `Y:0x4000`, `Y:0x8000`, then two window slots: core A (tracks 7, 8) `0x30000`, `0x34000`; core B (tracks 3, 4) `0x38000`, `0x3c000` | ✅ (`DSP.md` section 7) |
| Highest word each stock effect writes above its slot base: FLANGER `0x7ff`, SPRING REV `0xfff`, CHORUS `0xbfd`, COMB `0xbff`, SPATIALIZER `0xa5f`, PLATE REV `0x37ff`, DARK REV `0x3da2` | ✅ port, default knobs (`stock.SLOT_EXTENT`); other settings ⬜ |
| So offset `0x1000` or higher in a slot is clear of every stock effect except PLATE REV and DARK REV (SPRING REV stops on the line); offset `0x3da3` or higher is clear of all | derived |
| Payload B's boot zero loop clears `Y:0x37f00..0x3ffff` after the pre-boot upload, so an uploaded record there is gone at boot | ✅ port (both cores faulted at boot with resident code at `0x3bda3`) |
| The dispatcher calls `INIT[id]` when an id changes and `PROCESS[id]` every frame through `jsr (r2)`; `proc` is entered with `a` = 0 or 1; `init` keeps `r1`; `x:$213` at `init` is the address of the slot's allocator entry | ✅ |
| The ColdFire writes DSP X by host command `$08` (`HOST+4` = `0x88`), reaching `X:0..0x3fff` only, 16 data bits a word | ✅ port |
| Payload B's frame loop stores `0x3fff` or `0x5fff` into the host handlers' address masks every frame (`P:0x70`, `0x72`, from the bank word); a chunk sent on a frame whose ping word (`0x800000e0`) is 1 is lost, one sent at ping 0 arrives whole | ✅ port: 0 of 3,126 halfwords differ at ping 0, 1,178 differ sending every frame. Why the lost chunks do not appear at `X:0x4901` is ⬜ |
| Sending to core A at the frame interrupt's entry stops the stock ping words alternating: core A's chain stalls. HC polling and a settle loop did not change it | ✅ port; cause ⬜ |
| `X:0x2840..0x3fff` was written by nothing in one project at two fill seeds | 🟡 |
| The live FX ids are `0x80000ec4[8]` (FX1) and `0x80000ecc[8]` (FX2), tracks 1-8 | ✅ |
| The FX1 and FX2 choosers' select handlers are `0x400526e4` and `0x40052474`; the "same effect" test is `0x4005272a` / `0x400524ba` | ✅ |

## Design

Core B loads for both cores. The window is one memory, so code copied by B's hook is resident for A's tracks, and the pump
never writes to core A.

- **DLPUMP** (ColdFire, `modules/dlpump`), called from LOAD METER's entry code (`lm_in`, weak symbol) every frame interrupt.
  Idle: on ping-0 frames it compares the ids on the 16 live FX slots with the effects loaded and arms one message. A load is
  armed when an effect is used, not loaded, and the FX2 slot that shares its block is not PLATE REV, SPRING REV or DARK REV; a
  withdrawal when it is loaded and no slot uses it. Sending: 100 halfwords per ping-0 frame to core B's `X:0x2901..`, then the
  doorbell `0xa55a` to `X:0x2900` two frames later. The table of effects and their blocks are generated per remix
  (`remix.inc`, `Linked.include`) from `out/dsp/demand_records.json`; the unit reserves 2,600 code words a block on every link.
  The FX1 and FX2 choosers' "same effect" test is detoured: choosing an effect that is not loaded and whose block is under a
  stock reverb leaves the track as it was. Part, pattern, project load and paste are not hooked.
- **DLCOPY** (DSP, `modules/dlcopy/dlcopy.asm`), a hook on payload B at `P:0x76` (the frame head, after the masks are set), in
  the window. When the doorbell is set it clears the effect's BOUND word, copies the block to the window, writes the effect's
  init, proc and span, writes BOUND last, and clears the doorbell. A message with N = 0 only clears BOUND and the span.
- **The stub** (`modules/dlcopy/dlstub.asm`), assembled once by the build with a trampoline per effect. The effect's id
  dispatches to it. BOUND clear: the audio passes through (the stock null stub's loop). BOUND set: each instance runs the real
  init once, with `r0 n0 r6 r7 n7 m0 m1` kept, then jumps to the real proc.
- **The reverb guard** (`modules/dlcopy/dlwrap.asm`), assembled once per payload with a trampoline pair per guarded reverb;
  the reverbs' ids dispatch to it. At init it reads the buffer base through `x:$213`, and runs the stock init and proc only
  while `[base, base + extent)` misses the span of every loaded effect; otherwise the instance passes the audio through. The
  check is repeated every frame and an instance that went dry stays dry until it is selected again.

Layout (words are `X:` or `P:` as in the window, which aliases):

| where | what |
|---|---|
| `x:$33da3 + 8 k` (k = 0..3, in the clear gap) | effect k's entry: +0 BOUND (`$b0a5ed`), +1 real init, +2 real proc, +3 first window word, +4 the word after |
| `x:$2900` | staging: doorbell, k, destination offset, N, init offset, proc offset, then 2 N halfwords (code word as high 16 bits, then low 8). Addresses are offsets into the window |
| `x:$3f00..$3f4c` | the stub's per-instance flags and saved registers; `x:$3f50..$3fd2` the guard's |
| `P:0x33dc3..0x33e17` | DLCOPY; the stub follows at `window_loader`, then the guard for payload A, then for B (`0x33e20..0x33fd8` in octabam) |
| `P:0x37da3..0x37eff` | LOAD METER's DSP half (A and B) |
| slot offset `0x1000` | the effects: SPECTRUM `0x31000`, MODULATION `0x35000`, CHARACTER `0x39000`, TRANSIENT `0x3d000`, not uploaded |

The clear gaps are `0x33da3..0x33fff` (605 words) and `0x37da3..0x37eff` (349 words); resident code above `0x37f00` is wiped at
boot. octabam uses 565 and 340.

Builder: `Remix.window_demand` (keys), `Remix.window_guard` (stock keys), `Remix.window_loader` (address). The demand effects'
records are left out of payload A's upload and written to `out/dsp/demand_records.json`; the guards' addresses to
`out/dsp/guard_records.json`. The boot zero loop count ignores demand addresses.

## Checked

| gate | what | where |
|---|---|---|
| `verify_dlstub` | for each effect: the stub unbound equals the null stub, bound equals the effect's own render (0 of 6,400 samples differ), a wrong magic or a missing doorbell stays dry; DLCOPY binds a staged block and the stub runs it; a withdraw message makes it dry again | `dsp_host`, test/dlspike and octabam |
| `verify_dlwrap` | for each reverb, payload and published span: the guard equals the stock render and Y writes where the buffer is clear, passes the audio through and writes nothing where it covers the code | `dsp_host`, same |
| `verify_dlload` | with live ids poked: the four effects load (entry and every code word, read from both cores), one is withdrawn while the others stay, none loads unused, none loads over a reverb's block, the FX1 chooser picks an effect that can load and refuses one that cannot, the loaded proc is reached on core B and on core A (`--dsp-pcwatch`) | port, test/dlspike and octabam |

`dsp_host` keeps P and Y apart, so the guard is shown to decide correctly, not to prevent an overwrite on the chip.

## Open

- The unit: host write reaching `X:0x2900..0x3d55`, which frames of the unit deliver (the port's ping-0 rule), P stores into the
  window and execution of copied code, and the stock extents at other knob settings.
- Core A's stall when sent to, and the mask at the frames that lose their chunk.
- A track using an effect when its block's FX2 slot is then set to a stock reverb by a route the choosers do not hook: the effect
  stays loaded and the reverb runs dry (the guard).
- Audio at a load: the stub is dry until the code arrives, about 70 frames (25 ms) for MODULATION.
- Load cost on the ColdFire frame interrupt: LOAD METER figures.
