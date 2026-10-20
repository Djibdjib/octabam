A buffer freeze / slice repeater. Input writes into the stock FX instance
ring; RATE re-grabs a slice; SIZE loops it; JITR nudges the grab start;
DECY fades each grain back to dry. MIX 0 is exact dry.

## Access

An effect on a track: select the track, press FX2 (or FX1 in remixes that
list it there), and pick Stuttr from the chooser.

## Operation

SIZE and DECY are quadratic so the useful range is not crammed into the
low end of the dial. Keep RATE slower than SIZE so each grab finishes at
least one loop. JITR 0 grabs exactly; higher values start further behind
the write head. DECY 0 holds the grain; higher fades faster into dry
(the track never mutes between grabs).

## Parameters

| Knob | Default | What it does |
|---|---|---|
| SIZE | 40 | slice length ((kn+1)² words; ~0.1–186 ms on FX2) |
| RATE | 40 | re-grab speed (slow left, fast right) |
| JITR | 0 | 0 = exact grab; higher = random start further behind write |
| FDBK | 0 | recirculate the slice into the write head |
| DECY | 0 | fade into dry; 0 = hold, higher = faster (step = kn²) |
| MIX | 127 | dry/wet; after DECY the dry path returns |
| MODE | LOOP | LOOP / REV / DROP / SCRAM |
| SYNC | FREE | FREE / 16 / 8 / 4 divisions of the grab clock |
