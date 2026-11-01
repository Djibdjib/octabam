MIDI CC numbers that stock ignores now reach page 2 of FX1 and FX2. Stock
incoming CC writes page 1 only (CC 16–45).

## The CC numbers

| CC | Writes |
|---|---|
| 102–107 | FX2 page 2, slots 6–11 |
| 108–111, 14, 15 | FX1 page 2, slots 6–11 |

Until 1 Nov 2026 the blocks were 62–67 and 68–73. A controller preset
made for those numbers needs the new ones. The old range held the pedal
CCs (64 sustain to 69 hold 2), so a keyboard's sustain pedal moved an FX
knob, and CC FEEDBACK sent a held sustain to external synths. Every
number now is undefined in the MIDI standard.

## Operation

Send the CC on a track's channel, with AUDIO CC IN on. The value is
clamped to the slot's range. With MODE DEFAULTS in the image, a MODE
sent over CC re-defaults the knobs around it.

## Notes

- FX2 page 2 is reached only when the track's FX2 is the Delay Server or
  the Reverb Server; any other FX2 effect is skipped. In an image without
  the bus, only the FX1 block does anything. FX1 page 2 works on any FX1
  effect except NONE.
- The value is written where the panel's own page-2 editor writes it, so
  the effect follows it on the next audio frame.
