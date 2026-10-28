# SIDECHAIN_COMPRESSOR beside the demand loader

28 Oct 2026. DRAFT, for review before any code. ✅ read from the tree (file and line given), 🟡 inferred, ⬜ not looked at.
Nothing here has been built or run: the session that wrote it had no m68k toolchain, no `vendor/` and no 1.40C image, so
every word count below is an estimate until a build report prints it.
Follows octabam#934 (Zac Kyoti agreed to test a port).

## Why the resident placement does not fit

| need | words | status |
|---|---|---|
| SC's DSP section, `patch_sc_dsp3.asm` | 612 code + 16 (`ptable`) + 49 (`ptable2`) = 677 a copy | ✅ upstream README |
| as written, one copy per payload: the `@COREBASE@`, `@FCOREBASE@`, `@SBASE@`, `@FSBASE@`, `@GCNT@`, `@GSEED@` and `@FOREIGN_BR@` tokens differ per core | 1,354 | ✅ upstream manifest `subst` |
| the cross-core key window, 4 tracks x 4 generations x 32 words, and GSEED/GCNT, on each core's half | 2 x `$202` = 1,028 | ✅ upstream manifest |
| the resident gap left in `octabam` | 605 - 559 = 46 at `0x33fd3..`, 349 - 340 = 9 at `0x37ef7..`; the issue's "about 77" needs a build report to settle | ✅ `DEMAND_LOAD.md` |

Resident code must sit below `0x37f00` (payload B's boot loop zeroes `Y:0x37f00..0x3ffff`) and at a slot offset of `0x3da3`
or higher (DARK REV writes up to `0x3da2`). Zac's trial address `0x3effe` is offset `0x2ffe` of the fourth slot, which PLATE
REV and DARK REV write (🟡 from `stock.SLOT_EXTENT`).

## The design: a hooked demand block, reached through resident stubs

The loader is keyed on an effect id; SC has no dispatch entry of its own (`MenuEntry.stock_dsp`: the row is COMPRESSOR's and
COMPRESSOR's stock init/proc stay, `schema.py:552-557`). It is reached from four `DspHook`s instead. So the block is loaded
like any demand effect, but the hooks, not the dispatch table, need something resident in front of it.

### Hooks: one shared set of resident stubs

| hook | stock words (both payloads) | runs | stub when SC is not loaded |
|---|---|---|---|
| `sctap` | `66f000 000208` `move x:>$208,r6` | dispatcher, every track, every block | replay, `rts`: nobody reads the keybus |
| `moncommit` | `60f000 000206` `move x:>$206,r0` | dispatcher per-track commit | replay, `rts` (see the LOAD METER clash below) |
| `scdet` | `221e00 346100` | COMPRESSOR proc+0 | replay both, `rts`: the detector reads its own track, as stock |
| `scinit` | `44f400 0020c5` | COMPRESSOR init | replay, `rts` |

✅ The stock words are one tuple per hook in the manifest, so the displaced instructions are the same on both payloads and one
set of stubs in the shared window serves both cores (the sites differ; the build writes each payload's `jsr`).

Each stub: load the entry's BOUND word, compare with `$b0a5ed`, `jmp >` the hook's body in the block if bound, else replay and
`rts`. 🟡 About 9-10 words each with long addressing, 36-40 for four. Using only `a` keeps every stub inside its site's audited
clobber set (`sctap`'s is a, b, r0, r1, n1, x0, r6, per the source).

**The build generates them; no new module, no store.** A `DspHook` is a build-time patch (two stock words become `jsr >target`),
so nothing is managed at run time. The stubs follow from SC's own `DspHook` declarations (each site's displaced instruction and
the entry's BOUND word), the way the build already generates `dlstub.asm`'s per-effect trampolines: for a `window_demand` module
with hooks, the build emits one stub per hook into the resident gap, records them as a claim the ledger checks, and points the
`jsr`s at the stubs instead of the bodies. SC's hooks stay declared where they are. (`Store("octabam.sidechain-compressor")` is
only the id SC's settings and page defaults are filed under; it has nothing to do with the hooks.)

**One home for SC** (first version). With one home the bodies' addresses are fixed at build time, so a stub jumps to an absolute
address. More homes would need the stub to read the home's base from the entry and add an offset: more words, which the gap does
not have.

### The LOAD METER clash at `P:0x50e` / `P:0x303`

✅ `moncommit` and LOAD METER's `otop_e2` hook the same site with the same stock words (`modules/load-meter/manifest.py:87`,
`COSTS.md`). ✅ `schema.Override` composes ColdFire `Detour`s only (`site: int`, `schema.py:1466`); nothing composes two
`DspHook`s, and the ledger refuses the pair. octabam carries LOAD METER (the pump is called from its entry code), so this has to
be solved. Two options:

- **A DSP hook bridge** (the `Override` idea for `DspHook`s): the SC stub at that site does `jsr` moncommit's body when bound, then
  `jmp >otop_e2`, which replays the displaced instruction. Costs two words in the stub and a schema field. MON's fade then lands
  before LOAD METER's end stamp, so the meter counts SC. **Recommended**, on SCOPE's precedent: SCOPE shares three ColdFire
  sites with TUNER through `requires=("TUNER",)` and `overrides=(Override(site, "TUNER"), ...)`, its own stub doing both jobs
  (`modules/scope/manifest.py:27-32`). The DSP form is a new schema type, e.g.
  `DspOverride(site={"A": 0x50e, "B": 0x303}, module="LOAD METER")` (`Override.site` is a single ColdFire int and DSP sites
  differ per payload): the ledger accepts the shared site and the build skips LOAD METER's `otop_e2` hook there. It is declared
  in octabam's wrapper, `modules/sidechain-compressor/manifest.py`, which already extends Zac's MODULE with
  `dataclasses.replace`, so nothing in `upstream/` changes; `requires=("LOAD METER",)` goes with it, or the override only
  applies when LOAD METER is selected.
- **Move `otop_e2`** to another dispatcher site. This changes LOAD METER's figures, which `COSTS.md` is built on. Not recommended.

### The block: one copy of the code and one key window

**Make the code core-independent** (Zac's source, the one change on his side). 🟡 Every per-core token can be computed from
`x:$420` (the track, 0..7; core A is tracks 4-7):
- `@COREBASE@` is `track & 4`; `sctap`'s "local track 0" test becomes `track & 3 == 0`.
- `@SBASE@`/`@FSBASE@`: index the window by **absolute** track, `slot(t, gen) = WBASE + t*$80 + gen*$20` (8 x 4 x 32 = `$400`
  words, the same as two `$200`), so "own" and "foreign" are one formula.
- `@FOREIGN_BR@`: `(my track xor KEY track) & 4` is non-zero for a foreign key: one `bne` on both cores.
- `@GCNT@`/`@GSEED@` are read only by their own core (Zac, #934), so they move to core-private Y next to the MON words.
Then one copy is 677 words + `$400` = 1,701.

**Where.** The blocks' free space above offset `0x3820` (only DARK REV reaches it) is 1,411 words in blocks 0 and 1 (the loader
and LOAD METER above) and 2,016 in blocks 2 and 3. 🟡 SC's 1,701 fits blocks 2 and 3 only (`0x3b820` or `0x3f820`), the same
ones MODULATION (1,561) needs. With SC's single home there, TRANSIENT's home at offset `0x3e00` of that block is shared with SC's
span, so the pump must treat them as one block holder (it already allows one demand effect a block).

### The loader changes

| piece | change | where |
|---|---|---|
| the entry table | ✅ `x:$33da3 + 8 k` holds exactly 4 (DLCOPY starts at `0x33dc3`; the build exits above 4, `build_bus.py:151`). A fifth entry moves DLCOPY and everything after it up 8 words | `remixes/octabam/remix.py` `window`, `build_bus.py:151`, DLPROBE readers |
| the build: a hooked demand module | the window path already plants hooks into window code (`build_bus.py:3346`; the comment on `Remix.window` saying "no hooks" is stale). For a `window_demand` module it must instead emit the resident stubs and point the hooks at them, and record the bodies for the pump | `build_bus.py` around 3346; `schema.py` comment |
| the schema: `DspOverride` | a DSP form of `Override` (per-payload site, the overridden module's key); the ledger takes the site as the bridge's, the build skips the overridden hook | `schema.py`, `tools/remix/ledger.py`, `build_bus.py`; SC's wrapper manifest |
| the build: `ptable2` | ✅ the window path refuses a second table (`build_bus.py:3287`); place it behind `ptable` as the harvested path does (`build_bus.py:3583`) | `build_bus.py` |
| the trigger | ✅ `dl_tab` uses `modules[key].menu.fx2_id` (`dlpump/manifest.py`); for a `stock_dsp` module use the replaced effect's stock id (COMPRESSOR's), which is what the Part saves | `modules/dlpump/manifest.py` `table_inc` |
| the choosers | a `stock_dsp` demand module must never be refused: COMPRESSOR still works as stock when SC is not loaded. Toast only (`EVICT ... 1ST` text to settle) | `modules/dlpump/pump.s` `dl_sel_fx1/2` |
| no init/proc | SC has none; the message's init/proc offsets can point at its `sctap` body (unused: the stubs read nothing but BOUND) | `build_bus.py`, `dlcopy.asm` unchanged |

Total resident cost: 8 (entry) + 36-40 (stubs) + 2 (the bridge) = 46-50 words against 55 free (46 + 9, in two gaps). 🟡 It
fits only if the build report confirms the 55 and the stubs come in at the low end. It is the deciding number.

## Open, in the order they decide the work

1. **The resident words.** Assemble the four stubs and read the octabam build report's gap figures. If they do not fit, nothing
   below matters.
2. **Zac: the core-independent source.** Small and testable with his `emu_sc_dsp3.py`, `emu_sc_sctap.py` and
   `emu_sc_dsp3_xcore.py` under `--manifest`/`--org`. Its cycle cost on every block is the price.
3. **Cold key window.** The block is a reverb's buffer before SC loads, so for two generations after a load the foreign read can
   return stale words: a few blocks of wrong key, a duck glitch. GSEED in private Y survives a withdraw and does not reseed. Either
   the copier zeroes the `$400` words (one more frame of core B work, at a copy-frame peak already measured at 99.8 %) or the code
   keeps a per-core "warm" count reset when it first runs after a load. 🟡
4. **Load cost.** The bodies run from the window, about +47 cycles a sample a core on an MKI (Zac, `KYOTI_BP303_SCOPE.md` 3a), plus
   the stubs on every track every block. Not measured on octabam.
5. **Demand pressure.** Five demand effects over four blocks; SC and MODULATION want the same two. Which loses in a full project
   is the pump's existing first-home rule; not measured.
6. **Cross-core timing** is a hardware question (the emulator runs one core).

## Rejected

- **Load-time hook patching** (the copier writes the `jsr` into stock P when SC loads, restores it on withdraw: no resident
  stubs). Core B cannot write core A's P, so core A would need its own patcher hook, and the instruction cache would have to be
  shown not to hold the old words. More risk than the stubs save.
- **SC on COMPRESSOR's dispatch** (route COMPRESSOR's id through the loader's stub). The stub's unbound path is a dry pass-through;
  it would have to run stock COMPRESSOR instead, and the dispatcher hooks would still need resident stubs.
