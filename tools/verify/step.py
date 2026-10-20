#!/usr/bin/env python3
"""Run a command and print one stamped line with its wall time.

    python3 tools/verify/step.py [--cards] <command> [args ...]

    step: 14:03:22 +  7.4 s  rc=0  python3 tools/remix/selftest.py

The line goes to stdout after the command's own output, so a gate's log
keeps a per-step time (`make verify-shared` runs each of its steps through
this). ``--cards`` removes cards newly made by a passing step. The exit
code is the command's.
"""
import subprocess
import sys
import time

import card_retention


def main(argv):
    cards = argv[:1] == ["--cards"]
    if cards:
        argv = argv[1:]
    if not argv:
        sys.exit("usage: step.py <command> [args ...]")
    before = card_retention.begin(card_retention.ROOT, " ".join(argv)) if cards else None
    t0 = time.monotonic()
    rc = subprocess.run(argv).returncode
    if cards:
        card_retention.finish(card_retention.ROOT, before, " ".join(argv), rc == 0)
    print(f"step: {time.strftime('%H:%M:%S')} + {time.monotonic() - t0:5.1f} s  rc={rc}  {' '.join(argv)}", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
