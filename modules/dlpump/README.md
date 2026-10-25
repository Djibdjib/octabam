# `dlpump` -- DLPUMP

The ColdFire half of the demand loader (design, measurements and open items:
[`docs/proposals/DEMAND_LOAD.md`](../../docs/proposals/DEMAND_LOAD.md)).

`pump.s` is called from LOAD METER's entry code (`lm_in`, a weak symbol) on every frame
interrupt. Idle, on frames whose ping word (`0x800000e0`) is 0, it compares the ids on the 16
live FX slots (`0x80000ec4`) with the effects loaded and arms one message: a load when an effect
is used, not loaded, and the FX2 slot that shares its block is not PLATE REV, SPRING REV or DARK
REV; a withdrawal when it is loaded and unused, or when that FX2 slot has become one of those reverbs. Sending, it writes 100 halfwords a ping-0 frame
to core B's `X:0x2901..` by the stock host write, then the doorbell two frames later. It never
writes to core A.

Detours at the FX1 and FX2 choosers' "same effect" test (`0x4005272a`, `0x400524ba`) leave a track
as it was when the chosen demand effect is not loaded and its block is under a stock reverb.

`remix.inc` (the effect table and the blocks) is generated per remix from
`out/dsp/demand_records.json`; the unit reserves 2,600 code words an effect on every link.

Gate: `verify_dlload` (the port). Not run on a unit.
