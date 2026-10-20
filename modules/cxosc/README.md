# `cxosc` — CX OSC

Buchla-flavoured **complex oscillator** as a machine-list machine (sibling to
SYNTH MACHINE). Local fork of Tim Hastie's FM SYNTH ColdFire engine
(`modules/synth/upstream`); not an edit of that submodule.

## Select

**FUNC + SRC** or **SELECT MACHINE TYPE** → **CX OSC** (sixth row). No marker
file. Stored as FLEX with Part signature `"CX", 1` (same pattern as FM SYNTH
2.15). At most one CX OSC track per Part (selection guard).

## Provenance

Most of the voice / machine / page plumbing comes from FM SYNTH. CX-specific
work: marker-less list row, FOLD + SYMM waveshape, free/snap RATO, harder
FDBK, mono + stock LFOs (no VOIC/CHRD).

## PLAYBACK

| Slot | Name | Role |
|------|------|------|
| A | PTCH | Semitones (−64..+63) |
| B | RATO | Mod:carrier ratio (free 0.25..4; FUNC snaps classic table ≤4.01) |
| C | INDX | FM index (holds; LFO/plock for motion) |
| D | FOLD | Sine waveshape fold (dry/wet; moderate drive) |
| E | SYMM | Fold symmetry (DC bias into the fold; 0 = centered) |
| F | FDBK | Modulator feedback (up to ~1 cycle at 127) |

Mono only. Stock LFO page (all three LFOs). No VOIC/CHRD.

## Conflicts

**SYNTH MACHINE**, **ANALOG BD** — machine-list / page cave / kind table.

## Proof

**Hardware** (author's MKII): CXOSC C10–C22 remix handoffs — machine select
(after the `lea` name-table fix), PLAYBACK knobs including FOLD / SYMM / FDBK /
free+snap RATO. Port: `make check REMIX=cxosc` and reach with `TESTS=1`.

Measured: select no longer illegal-instructions at `fm_src_names`; fold bass
moves with fold order. Inferred: non-monotonic lows under FOLD are sine-fold
Chebyshev behaviour.

## Build

```bash
make check REMIX=cxosc
```
