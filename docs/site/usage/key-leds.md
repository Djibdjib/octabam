KEY LEDS makes the CHROMATIC keyboard of a MIDI track show its KEY. Stock
always lights C major on the trig keys, whatever KEY says. With KEY LEDS,
the tonic is yellow, the scale's other notes red, and the notes outside
the scale dark, the same colours stock uses for C major.

## How to use it

Select a MIDI track and open MIDI ARP SETUP with **FUNC + AMP**. Press
encoder **F** to turn KEY on and turn F to choose the key. Then hold the
track key and choose **CHROMATIC** in the trig-mode list: the trig keys
light that key's scale.

On a MIDI track key 1 is always C, as on stock's keyboard; only the
colours follow the KEY. For example, **D MIN** lights D yellow (keys 3 and 15) and E, F, G,
A, Bb and C red. With [MIDI Scales](midi-scales.md) in the remix, its
modes light too: **C DOR** shows C, D, Eb, F, G, A and Bb.

On an audio track, with [Scale Quantizer](quantizer.md) in the remix, the
keys light its **SCALE** on its **ROOT** (PROJECT > CONTROL > SEQUENCER).
Scale Quantizer's keyboard plays ROOT on key 1, so keys 1 and 13 stay
yellow and the rest of the pattern follows the scale.

KEY OFF and SCALE OFF keep stock's C major, and so does an audio track
without Scale Quantizer.

## What it does not do

It only changes the LEDs. It does not move notes onto the scale: KEY (and
MIDI Scales) does that for the sequencer and the arpeggiator, and Scale
Quantizer for the audio tracks, as before.
Nothing is saved; there is no setting.

## Verification limits

Checked under the emulator on both models, for every KEY value and for
Scale Quantizer's scales and roots: the trig LEDs read from the panel
stream. Not yet tested on a unit.
