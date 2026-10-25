# EVENTS clients

A focused fixture for the shared EVENTS migration: EUCLID consumes transport
notifications and PLOCKS P2 consumes held edits and copy notifications. Both
clients are selected together, installing 25 event hooks. FILTER and COMPRESSOR
provide stock controls; PLATE REV supplies the page-2 fallback used by the
editor gates.

USB presents MAIN and CUE only (four channels), so the hardware stress runner's
first stereo pair observes MAIN. LOAD METER supplies frame-interrupt and DSP
readings. This is a dedicated integration-test selection.

Run `make check REMIX=events-clients` with `OT_PROJECT` pointing to a disposable
project. For a unit, follow [HARDWARE_TESTING](../../../docs/contributing/HARDWARE_TESTING.md):
generate a fresh project and the stimulus layouts, qualify the exact image,
then run the focused EUCLID layouts and transport sequence. BASE has no effects;
it still carries both event subscribers. Zero-subscriber omission is verified
separately by `events-empty`.

The standard stress generator covers START/STOP but not CONTINUE. Resume needs
an explicit sequence or the panel. Panel operations have emulator coverage; physical panel timing and a real
save/power-cycle check need the operator. USB capture does not validate the
analog outputs.

## Hardware results

Octatrack MKII, 25 October 2026. `EVT871E2.RMX` was built from `9a752f97`;
MAIN/RMX SHA-256:
`18f5fced905a9dcdcb05bde239afb94ed5c99e9e22276d11d148e3b9e6a236c9`.
BRAIN labels this remix `EVENTS-CLIENTS`; that label alone does not identify
an image version. These results apply to E2, not automatically to later builds.

| Check | Recorded result |
| --- | --- |
| Stopped trig-paste undo, continuous hold | Existing MIX 64 restored; explicitly empty destination restored to unhighlighted Part value 127, both checked after release/rehold |
| START / STOP / CONTINUE, C03 | Audio resumed at the next sample trigger, 4.1 seconds after CONTINUE; subsequent 90 BPM playback produced audio |
| 600 seconds uninterrupted C03, 120 BPM | No sustained silence or clipping; zero USB overrun, underrun, duplicate-bank or DSP bad-record deltas |
| Physical save and power cycle | C03/T1/trig 1 retained highlighted MIX 40; E2 selected before restart, image identity not independently checked afterward |

The sustained run's longest observed ColdFire frame interrupt was 424 us
against a nominal 363-us frame period. An earlier E1 mixed-transport run
stopped on silence at 431.5 seconds. A later edited-C03 workload comparison
contained one detected stereo transient. Their cause is not established;
these observations do not establish timing or mixed-transport acceptance.
The [failure register](../../../docs/contributing/FAILURE_MODES.md#events-clients-transport-stress-reaches-silence-with-healthy-frames)
contains the measured scope. Early E2 undo observations also differed from
the later controlled passes; see the
[undo record](../../../docs/contributing/FAILURE_MODES.md#plocks-trig-paste-undo-keeps-copied-page-two-locks).
