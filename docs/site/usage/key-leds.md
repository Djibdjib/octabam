KEY LEDS makes the CHROMATIC keyboard of a MIDI track show its KEY. Stock
always lights C major on the trig keys, whatever KEY says. With KEY LEDS,
the tonic is yellow, the scale's other notes red, and the notes outside
the scale dark, the same colours stock uses for C major.

## How to use it

Select a MIDI track and open MIDI ARP SETUP with **FUNC + AMP**. Press
encoder **F** to turn KEY on and turn F to choose the key. Then hold the
track key and choose **CHROMATIC** in the trig-mode list: the trig keys
light that key's scale.

Key 1 is always C, as on stock's keyboard; only the colours follow the
KEY. For example, **D MIN** lights D yellow (keys 3 and 15) and E, F, G,
A, Bb and C red. With [MIDI Scales](midi-scales.md) in the remix, its
modes light too: **C DOR** shows C, D, Eb, F, G, A and Bb.

KEY OFF keeps stock's C major. Audio tracks are not changed.

## What it does not do

It only changes the LEDs. It does not move notes onto the scale: KEY (and
MIDI Scales) does that for the sequencer and the arpeggiator, as before.
Nothing is saved; there is no setting.

## Verification limits

Checked under the emulator on both models, for every KEY value: the trig
LEDs read from the panel stream. Not yet tested on a unit.
