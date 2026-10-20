# `cxosc`

Gate remix for **CX OSC** (complex oscillator machine).

## What is in it

- **CX OSC** — machine-list row (no marker file); PLAYBACK PTCH RATO INDX FOLD
  SYMM FDBK

Not combined with SYNTH MACHINE (declared conflict).

## Status

`Proof.CHECK`: builds and boots under the port. Hardware smoke on the
author's MKII (CXOSC C10–C22 handoffs): select, PLAYBACK knobs, fold /
symmetry / feedback.

## Build

```bash
make check REMIX=cxosc
```
