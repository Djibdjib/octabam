# SIDECHAIN_COMPRESSOR beside the demand loader

28 Oct 2026. DRAFT, for review before any code. ✅ measured / read from the tree, 🟡 inferred, ⬜ not looked at.
Nothing here has been built or run: the session that wrote it had no m68k toolchain, no `vendor/` and no 1.40C image.
Follows octabam#934 (Zac Kyoti agreed to test a port).

## Why the resident placement does not fit

| need | words | where it could go | status |
|---|---|---|---|
| SC code, `patch_sc_dsp3.asm` | 612, plus the 16- and 49-word tables = 677 per payload | resident, window words below `0x37f00` that no stock effect writes | ✅ upstream README |
| the same, if the two payloads' copies cannot be one | up to 1,354 | | 🟡 the `subst` tokens differ per core; a core-independent form is not written |
| the cross-core key window, 4 tracks x 4 generations x 32 words, plus GSEED/GCNT | `$202` = 514 on each core's half, 1,028 | offset `0x3da3` or higher of a slot, or a block nothing else holds | ✅ upstream manifest |
| the resident gap | `0x33da3..0x33fff` (605) and `0x37da3..0x37eff` (349) = 954; the loader, its guards and LOAD METER use about 877-899 | | ✅ `DEMAND_LOAD.md`; Zac measured about 77 left |

Everything above `0x37f00` is zeroed by payload B's boot loop, so resident code cannot go in B's half; data can (GSEED is a
sentinel and nothing needs the window cleared). The slot tops in B's half (`0x3bda3..`, `0x3fda3..`) are 605 words each and
already hold TRANSIENT's homes at `0x3be00` and `0x3fe00` once loaded.

Zac's trial address `0x3effe` for core A's window is offset `0x2ffe` into the fourth slot: PLATE REV (`0x37ff`) and DARK REV
(`0x3da2`) write there when one is on that FX2. 🟡 inferred from `stock.SLOT_EXTENT`, not tested.

`Remix.window` also refuses a module with hooks, a second table or a tail (`schema.py`, the comment on `window`), and SC has
four hooks and two tables.

## Proposal: SC is a demand block, reached through resident stubs

The loader already does the hard part for effects: a block of the window is copied in while a track uses the effect, a stub
passes the audio through until then, the stock reverbs are guarded off the code, and a chooser refuses what cannot load. SC is
different in one way: it is not reached by its own id. Its four entry points are hooks:

| hook | site | runs | if SC is not resident |
|---|---|---|---|
| `sctap` | dispatcher, `A 0x4a7`, `B 0x29c` | every track, every block | do nothing: nobody reads the keybus |
| `moncommit` | dispatcher per-track commit, `A 0x50e`, `B 0x303` | every track, every block | do nothing |
| `scdet` | COMPRESSOR proc+0, `A 0x1ab1`, `B 0x1871` | each COMPRESSOR | skip it: the detector reads its own track, as stock |
| `scinit` | COMPRESSOR init, `A 0x1aa4`, `B 0x1864` | each COMPRESSOR init | skip it |

1. **Four resident stubs**, each: test the entry's BOUND word (as `dlstub.asm` does), if bound `jmp` into the loaded body,
   else replay the displaced instruction and return. 🟡 about 8-12 words each, 32-48 in all, which fits the 77 left. The
   keybus and MON words stay claimed in core-private Y (`$7f0..$9ff`) as now.
2. **SC as a fifth demand block.** Trigger: any live FX slot holds COMPRESSOR's id (the pump already compares live ids, so
   `dl_tab` gets a row whose id is COMPRESSOR's, not SC's own). Withdrawn when none does, after the same 10 s grace.
3. **One block holds the code and both key windows.** The block is exclusively SC's while loaded, so the windows need no
   separate safe address. 🟡 677 words of code plus 1,028 of window is 1,705, which fits the 2,016 words above offset
   `0x3820` of the third or fourth block if the two payloads can share one copy of the code. If they cannot (1,354 + 1,028 =
   2,382) it does not, and the code has to be made core-independent first (open question 1).
4. **Reverb collision.** Same as any demand effect: a block where a stock reverb reaches the code is not used, the guard makes
   that reverb run dry, a chooser pick that would collide is refused with the existing toast. SC would use the block homes
   not taken by MODULATION, SPECTRUM, CHARACTER and TRANSIENT, so four blocks now serve five effects. 🟡 Possible demand
   pressure: whether five effects ever collide in a realistic project is not measured.
5. **What the user sees while SC is not resident:** COMPRESSOR with KEY set works as stock COMPRESSOR (self-keyed) for the
   load time (about 25 ms for MODULATION) and whenever the block is taken. A toast would name why, as for the others.

## Open questions, in the order they decide the work

1. **Can the two payloads share one copy of the code?** `@COREBASE@`, `@FCOREBASE@`, `@SBASE@`, `@FSBASE@`, `@GCNT@`,
   `@GSEED@` and `@FOREIGN_BR@` differ per core. Turning them into a read of a core-id cell is a change to Zac's DSP source and
   costs cycles on every block (his measure: 2,475-2,652 cycles a sample on core 1). Needs his view.
2. **Load cost.** SC is called from the dispatcher every block, so code run from the window pays the window's wait state
   (Zac measured one extra cycle per instruction word fetched from P in the window, about +47 cycles per sample per core, on
   an MKI; `KYOTI_BP303_SCOPE.md` section 3a) against a copy-frame peak already at 99.8 %. Not measured on octabam.
3. **Stub cost and the `P:0x50e` site.** `docs/contributing/COSTS.md` says SC's `moncommit` and LOAD METER's `otop_e2` patch
   the same dispatcher site. ⬜ I have not read both patches; one of them must chain to the other, and the ledger refuses two
   hooks on one site.
4. **Cross-core timing** is a hardware question; the emulator runs one core (Zac).
5. **A load in flight:** `sctap` and `scdet` must never see a half-copied body. The copier's order (BOUND cleared first, set
   last) covers a code block; whether it covers the data windows (written by the running code, not the copier) needs the
   window to be zeroed or generation-stamped at publish. 🟡

## Work breakdown

1. Read `tools/build/dsp_modmap.py` and `tools/remix/dsp_ranges.py`: how a `DspSection` with hooks is placed today, and what
   a hook into a demand block needs. Decide where the four stubs are generated.
2. Extend the build: a demand block that is not an FX id's effect (stubs at hook sites, trigger id from another module's menu).
3. `dlpump`: a trigger id separate from the module's own id; the toast text.
4. Zac: question 1, then `--manifest`/`--org` runs of his three emulator tools on the block's addresses.
5. Gates: extend `verify_dlstub`, `verify_dlwrap`, `verify_dlload` for the fifth block; refhash for the build change
   (`scripts/refhash.sh check`, in CI only).
6. Docs: `docs/site/` pages, the module README, `DEMAND_LOAD.md`, `CHANGELOG.md` and, only after a flash, the proof note.
