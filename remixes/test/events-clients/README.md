# EVENTS clients

A focused fixture for the shared EVENTS migration: EUCLID consumes transport
notifications and PLOCKS P2 consumes held edits and copy notifications. Both
clients are selected together, installing 25 event hooks. FILTER and COMPRESSOR
provide stock controls; PLATE REV supplies the page-2 fallback used by the
editor gates.

USB presents MAIN and CUE only (four channels), so the hardware stress runner's
first stereo pair observes MAIN. LOAD METER supplies frame-interrupt and DSP
readings. This is a test selection, not the standard Inserts remix.

Run `make check REMIX=events-clients` with `OT_PROJECT` pointing to a disposable
project. For a unit, follow [HARDWARE_TESTING](../../../docs/contributing/HARDWARE_TESTING.md):
generate a fresh project and the stimulus layouts, qualify the exact image,
then run the focused EUCLID layouts and transport sequence. BASE has no effects;
it still carries both event subscribers. Zero-subscriber omission is verified
separately by `events-empty`.

The standard stress generator covers START/STOP but not CONTINUE. Resume needs
an explicit sequence or the panel. Held edits, copy/paste/undo and the physical
save/power-cycle check also need the operator. USB capture does not validate the
analog outputs.

## Hardware results

EVT871E1 (`f09654ca`), 25 October 2026: six layouts and four explicit
START/STOP/CONTINUE/tempo cases ran with zero USB fault deltas or DSP bad-record
increases. The first both-slot ENV capture had one brief transient; its repeat
did not. Elevated level remained. The ten-minute transport stress stopped on
silence at 431.5 seconds with a healthy frame engine; attribution is unresolved.
Short BASE/RAND and transport-suffix checks passed after power cycling but did
not reproduce the preceding seven minutes. These are partial results, not a
hardware acceptance pass.

During physical editing, continuous-hold trig-paste undo retained the copied
page-two lock. The pre-EVENTS private-hook image reproduces this under the port;
stock page one restores the previous locks while leaving the trig present.
The PLOCKS fix and regression are described in its
[development notes](../../../modules/plocks-p2/DEVELOPMENT.md#trig-paste-undo-snapshot).
EVT871E2 (`9a752f97`) failed the physical retest on EVT871E2_ED/C03 during
playback: `UNDO PASTE` appeared, but the copied MIX 40 remained when trig 5
was released and held again; the unheld Part value was 127. The 454.3-second
panel monitor recorded zero USB fault deltas and no monitor errors. The
stopped software fixture passes; the difference remains under investigation.
Further edit operations, save/power-cycle and sustained combined transport
acceptance remain pending.
