A chance grain repeater. Input writes into the stock FX instance ring;
RATE ticks roll CHNC to grab a SIZE grain and HOLD-loop it. Miss stays
dry. MODE picks 1× / ½× / ¼× / random rate; REV is reverse chance per
repeat. MIX 0 is exact dry.

## Access

An effect on a track: select the track, press FX2 (or FX1 in remixes that
list it there), and pick Stuttr from the chooser.

## Operation

Raise CHNC so grabs can fire; RATE sets how often attempts happen. HOLD
keeps the grain repeating after a hit; engage and release each crossfade
~2 ms so the edges do not click. Try MODE HALF or QUART for pitched-down
repeats; RND varies rate per wrap. REV at 0 is always forward; higher
rolls reverse more often.

## Parameters

| Knob | Default | What it does |
|---|---|---|
| SIZE | 40 | grain length ((kn+1)² words; ~0.1–186 ms on FX2) |
| RATE | 40 | how often CHNC may attempt a grab |
| CHNC | 64 | 0 = never; 127 = always grab on tick |
| HOLD | 40 | how long to keep repeating after a hit |
| REV | 0 | per-repeat reverse probability |
| MIX | 127 | dry/wet of the stutter vs live |
| MODE | FWD | FWD / HALF / QUART / RND |
| SYNC | FREE | FREE / 16 / 8 / 4 divisions of the attempt clock |
