#!/usr/bin/env python3
"""Compare two refhash manifests: artifacts must match; reports may differ.

    python3 tools/verify/refhash_compare.py BASELINE CURRENT

Exit 0 when every non-<report> artifact line matches (and every <report>
line of a case with rc!=0). Exit 1 on any other mismatch.

A replaces= module that joins LEFT STOCK rewrites every build-report hash
while the bins stay bit-identical (trap-report-api). CI baselines the
merge-base, so those PRs cannot re-save; artifact identity is the
behaviour gate. For a case that exits non-zero the report is often the
only line, so a different refusal reason must still fail.
"""
import argparse
import pathlib
import re
import sys

CASE_RC = re.compile(r"^case .+ rc=(\d+)$")


def arts(text: str) -> dict[str, list[str]]:
    """Per-case lines that must match between manifests.

    Drop `<report>` lines when the case exited 0; keep them when rc != 0
    (those cases often have no artifact lines, so the report is the gate).
    """
    out: dict[str, list[str]] = {}
    case = None
    keep_report = False
    for line in text.splitlines():
        m = CASE_RC.match(line)
        if m:
            case = line
            keep_report = int(m.group(1)) != 0
            out[case] = []
        elif case and line.strip():
            if "<report>" in line and not keep_report:
                continue
            out[case].append(line)
    return out


def same_artifacts(baseline: str, current: str) -> bool:
    return arts(baseline) == arts(current)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("baseline", type=pathlib.Path)
    ap.add_argument("current", type=pathlib.Path)
    a = ap.parse_args(argv)
    return 0 if same_artifacts(a.baseline.read_text(), a.current.read_text()) else 1


if __name__ == "__main__":
    sys.exit(main())
