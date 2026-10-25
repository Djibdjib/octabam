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
The stopped physical retest also retained MIX 40 after undo and release/rehold.
Later controlled stopped checks passed on E2: a previous MIX 64 returned after
paste/undo, and an explicitly removed destination lock returned to unhighlighted
127. Diagnostic-only D1 had separately traced both restores; its instrumentation
is outside this PR. E2's clear-locks/undo messages and final MIX 40 were confirmed,
but the intermediate cleared state was not checked. Track undo's final value
was not confirmed. These scoped passes do not explain the original failures.
Manual testing now focuses on hardware-specific behavior. The operator saved
`EVT871D1_ED` with C03/T1/trig 1 showing highlighted MIX 40, power-cycled the
unit, confirmed the same project loaded, and confirmed highlighted MIX 40
again without turning the knob. This passes persistence for that lock, not
every save path. E2 was the selected image before restart; the running image
was not independently identified again after the power cycle.

The later E2 fixed-C03 transport run on fresh `EVT871E2_RN` stopped at 18.0
seconds: initial START produced audio, but the first STOP/CONTINUE remained
silent until the monitor stopped. USB fault deltas and DSP bad-record increases were
zero and frame health remained good; one sampled ColdFire longest run was
413 microseconds. Fixture inspection found that the three-second silence grace
ends before the next step-1 sample trigger; an earlier passing capture also
waits 4.3 seconds after CONTINUE. This run is inconclusive, not an EVENTS
failure, and does not supersede the earlier seven-minute failure. See the
[failure register](../../../docs/contributing/FAILURE_MODES.md#e2-continue-monitor-stops-before-the-fixtures-next-trigger).

The corrected E2 CONTINUE capture waited a full pattern: audio returned after
4.1 seconds, followed by audible 90 BPM playback, with zero USB faults or DSP
bad-record increments. A separate 600-second uninterrupted C03 run at 120 BPM
also completed with no sustained silence, clipping or USB faults. ColdFire's
longest observed frame interrupt was 424 microseconds, above the approximately
363-microsecond frame budget; frame-budget acceptance remains open. Neither
run reproduces the E1 mixed-transport sequence or proves total CPU headroom.
