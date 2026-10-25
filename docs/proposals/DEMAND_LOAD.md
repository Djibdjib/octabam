# Demand loading of window effects: plan and state

25-26 Oct 2026. ✅ measured (port or unit, as stated), 🟡 inferred, ⬜ not looked at. Nothing here has run on a unit.
Addresses are `P:` / `X:` / `Y:` DSP words, or ColdFire virtual addresses where they start `0x4`.

## Goal

Every stock effect stays and works as stock; our new effects are in the effect list and are loaded into the
DSP's shared window only while a track uses them. No stock effect is removed, replaced or shrunk. The window
is stock's buffer memory, so the code goes only where no running stock effect writes.

## Constraints that fix the design

| fact | status |
|---|---|
| P is 8K per core and full with the 13 stock DSP effects; P above `0x1fff` is absent | ✅ unit (`modules/pextprobe`) |
| Code written into the window at 7 addresses ran from both cores | ✅ unit |
| The window `0x30000..0x3ffff` is one memory; P, X and Y alias there | ✅ unit |
| FX2 buffer slots per core: `Y:0x4000`, `Y:0x8000`, then two in the window (core A `0x30000`, `0x34000`; core B `0x38000`, `0x3c000`) | ✅ (`CHIP.md`, `stock.SLOT_BASES`) |
| Highest word each stock effect writes above its slot base: FLANGER `0x7ff`, SPRING REV `0xfff`, CHORUS `0xbfd`, COMB `0xbff`, SPATIALIZER `0xa5f`, PLATE REV `0x37ff`, DARK REV `0x3da2` | ✅ port, default knobs (`stock.SLOT_EXTENT`); 🟡 other settings, the unit |
| So code at offset `0x1000` or higher in a block is clear of every stock effect except PLATE REV and DARK REV (SPRING REV stops on the line); the top 605 words of each block (`0x33da3`, `0x37da3`, `0x3bda3`, `0x3fda3`) are clear of all | derived |
| The dispatcher calls `INIT_TABLE[id]` when an id changes and `PROCESS_TABLE[id]` every frame, through `jsr (r2)`; both tables are in X | ✅ (`DSP.md` section 5) |
| `proc` is entered with `a` = 0 or 1; `init` must keep `r1`; the instance state is the `r7` block | ✅ stock listings, `verify_init_regs` |
| `x:$213` at `init` holds the address of the slot's entry in the allocator table; the buffer base is the word there. PLATE REV reads it at `P:0x1018`, DARK REV at `P:0x1692` | ✅ stock listing, port |
| The ColdFire writes DSP X by host command `$08`, reaching `X:0x0000..0x3fff` only; 16 data bits per word | ✅ port (`docs/proposals/HOT_RELOAD.md` on `feat/hotreload-poc`) |
| `X:0x2840..0x3fff` was written by nothing in one project at two fill seeds | 🟡 one project, one setting |
| Core A's destination mapping for X words of `0x2000` and above | ⬜ |
| The frame interrupt's entry (`0x4000aad0`) is the one point a ColdFire transfer can start without upsetting the stock chain; LOAD METER detours the same site | ✅ port |
| The FX1 and FX2 choosers' select handlers are `0x400526e4` and `0x40052474` | ✅ (`modules/fx2-lock/README.md`) |

## Decisions, 26 Oct 2026

1. **Demand set:** SPECTRUM, CHARACTER, MODULATION, TRANSIENT, loaded when a track uses them. GATE VERB is out of this plan.
   LOAD METER is the only resident effect; the stubs and guards are resident with it.
2. **Guards** keep PLATE REV, DARK REV and SPRING REV off loaded code (the other four buffered effects stay clear by placement
   at offset `0x1000` or higher).
3. **Unload:** an effect is unloaded when no track uses it. The ColdFire watches the live effect assignments.
4. **No free block:** the selection is refused. **Scope: the FX1 and FX2 choosers only.** Every other route that puts one of
   our effects on a track (Part, pattern, project load, paste) takes the load-on-use path with no hook, and passes the audio
   through if nothing is free.
5. **Placement:** each effect picks its own block. The ColdFire reads the live assignments and avoids any block whose track
   runs PLATE REV, DARK REV or SPRING REV. The guards check a table of loaded spans, one per effect.
6. **Staging area:** `X:0x2840..0x3fff` is claimed in the ledger, and measured on the unit by a probe before any image relies on it.
7. **Core A:** its X mapping is measured in the port first. The loader sends to whichever core is waiting; the "wanted" word says which.
8. **Unit checks, as probes first:** (a) the host write reaches the staging area, (b) the DSP's P stores into the window and the
   execution of copied code, (c) the stock extents at non-default knob settings. No image depends on them until they are read.
9. **Frame entry:** LOAD METER's entry code calls a named pump hook when the pump unit is present. The pump is its own module.

## Design

Three DSP pieces and one ColdFire piece.

1. **DLSTUB, one per demand effect.** The effect's id points at the stub in both dispatch tables.
   - Not bound: the audio passes through (the stock null stub's loop) and the effect's "wanted" word is set.
   - A complete staged block and the code absent: the stub copies it into the window, writes the real init and proc and the
     occupied span, writes BOUND last, clears the doorbell, and runs the real code in that same call.
   - Bound: each instance runs the real `init` once (keeping `r0 n0 r6 r7 n7 m0 m1` and the entry `a`), then jumps to the
     real `proc`.
2. **DLWRAP, one each for PLATE REV, DARK REV and SPRING REV, per payload** (the stock entries differ between payloads). It
   answers the dispatcher for the stock id. At `init` it reads the buffer base through `x:$213`, and runs the stock init and proc
   only while `[base, base + extent]` misses every loaded span; otherwise the instance passes the audio through. The check is
   repeated every frame; an instance that went dry stays dry until it is selected again.
3. **Unload.** The ColdFire clears the effect's BOUND word (the stub then passes through again), then clears its span; the
   window words are free. A guard that went dry stays dry until the reverb is selected again.
4. **The ColdFire loader.**
   - Pump: when armed, sends a chunk of the staged block to the waiting core's X at each frame interrupt's entry (called from
     LOAD METER's entry code), then the doorbell word last, one frame later.
   - Policy: reads the "wanted" words, picks a block (decision 5), sets the destination, arms the pump; unloads (decision 3).
   - Chooser refusal: a hook at `0x400526e4` and `0x40052474` that refuses the selection of one of our effects when it is not
     loaded and no block is free.

Shared window words (below the lowest window code, so payload A's boot zero loop clears them), a table of four effects at
`x:$33d80 + 8 * k`: BOUND (`$b0a5ed`), real init, real proc, first occupied word, the word after, and three reserved.
Staging, private to the core the ColdFire writes, one effect at a time: `x:$2900` doorbell (`$a55a`), `x:$2901` destination,
`x:$2902` N, `x:$2903` init, `x:$2904` proc, `x:$2905..` 2 N words (each 24-bit code word as its high 16 bits, then its low 8);
`x:$2910 + k` wanted by effect k. Per-core private tables: `x:$3f00..$3f4b` (DLSTUB), `x:$3e00..$3ee0` (DLWRAP).
The spike in `feat/dlspike` uses one effect at `x:$33d9e..$33da2` and `x:$2910`; the table above is the shape it grows to.

## Built and checked

Branch `feat/dlspike` (worktree `.claude/worktrees/dlspike`), `dsp_host` only.

| commit | what | gate |
|---|---|---|
| `1f057947` | DLSTUB: dry until bound, lazy init, real proc | `verify_dlstub`: unbound equals the null stub; bound equals MODULATION's direct render, 0 of 6,400 samples differ; a wrong magic stays dry |
| `1bfc93cc` | the copier and publish step | code absent at boot, a staged block gives the direct render over 200 blocks (1,561 words copied); no doorbell stays dry |
| `2b9272cf` | DLWRAP for PLATE REV on payload A | `verify_dlwrap`: on the four slots the wrapper equals the stock render and its Y writes where clear; dry and no Y writes where it covers the code |

`dsp_host` keeps P and Y apart, so the wrapper is shown to decide correctly, not to prevent an overwrite on the chip.

## Not built, in order

1. `Remix.window_demand`: assemble and place, leave out of the upload, write `out/dsp/demand_records.json` (address, words, entries).
2. The ColdFire pump as a linked unit, called from LOAD METER's entry code, and the blob it sends (built from the sidecar).
3. A port test: stub on a track, code absent at boot, pump armed, `pcwatch` arrivals at the real proc, `P:` and `X:` peeks.
4. Core A's destination mapping in the port, and a copier test on core A.
5. The per-effect shared table, then the "wanted" path DSP to ColdFire, the block policy and the unload.
6. DLWRAP for DARK REV and SPRING REV, and all three on payload B; DLSTUB for SPECTRUM, CHARACTER and TRANSIENT; the stubs taking each
   effect's own id in `octabam`.
7. The chooser refusal.
8. Ledger declarations: the X staging region, the private tables, the shared table, the resident words in the clear gaps.
9. Gates in `make check`; `verify_dirty_state` over the stubs; the PEXT PROBE additions for the unit checks (decision 8).
10. The unit probes, then the unit run.

## Acceptance

- Every stock effect renders bit-identically to stock in `octabam` with the loader present and nothing loaded.
- An effect loaded on demand renders bit-identically to the same effect built into the window.
- A guard never lets a stock reverb write a loaded word; a load never lands on a running reverb's buffer.
- After an unload the window words are free and the effect, selected again, loads again.
- Nothing in the loader changes a stock effect's code, tables or descriptors.
