#!/usr/bin/env python3
"""Generate the private EUCLID transport-regression project; never writes a card."""
import argparse
from hardware_project import prepare

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    amp = dict(FREQ=16, RES=0, DEPTH=127, DECAY=64, STEPS=7, PULSE=3,
               ROT=0, RATE=1, TYPE=3, ATK=4, OUT=1, MIX=127)
    filt = dict(FREQ=48, RES=16, DEPTH=112, DECAY=32, STEPS=15, PULSE=5,
                ROT=0, RATE=1, TYPE=0, ATK=4, OUT=0, MIX=127)
    print(prepare(a.source, a.out, 'octabam-inserts',
                  [('fx1', 1, 'EUCLID', amp), ('fx2', 5, 'EUCLID', filt),
                   ('fx1', 2, 'EUCLID', amp), ('fx2', 2, 'EUCLID', filt)],
                  {1: {1: [1]}, 2: {5: [1]}, 3: {1: [1], 5: [1]}, 4: {2: [1]}}))

if __name__ == '__main__': main()
