#!/usr/bin/env python3
"""Remove a gate's newly created virtual cards after it passes.

Only ignored, single-link regular ``out/**/*.img`` files are candidates.
Untouched cards present before the gate, pinned trees, and nested Git
worktrees are preserved. A failed or interrupted gate keeps its cards for diagnosis.
``KEEP_CARDS=1`` keeps cards from passing gates too.

    python3 tools/verify/card_retention.py run -- make check-impl REMIX=bus
"""
import argparse
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


class RetentionError(RuntimeError):
    pass


def _stamp(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
        return None
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_blocks)


def _safe_path(root, relative):
    """Recheck ancestors immediately before unlink, including late pins."""
    parent = root / "out"
    if parent.is_symlink() or (parent / ".keep-cards").exists():
        return False
    for name in relative.parts[1:-1]:
        parent /= name
        if parent.is_symlink() or (parent / ".git").exists() or (parent / ".keep-cards").exists():
            return False
    return True


def snapshot(root=ROOT):
    """Identity of eligible cards relative to root, without following links."""
    root = pathlib.Path(root).resolve()
    out = root / "out"
    if out.is_symlink():
        raise RetentionError("out/ is a symlink; refusing card cleanup")
    if not out.is_dir():
        return {}
    paths = []
    for directory, dirs, files in os.walk(out, followlinks=False):
        here = pathlib.Path(directory)
        if (here / ".keep-cards").exists():
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not (here / d).is_symlink()
                   and not (here / d / ".git").exists()]
        for name in files:
            if name.endswith(".img"):
                path = here / name
                try:
                    if _stamp(path) is not None:
                        paths.append(path.relative_to(root))
                except FileNotFoundError:
                    continue
    if not paths:
        return {}
    # Git does not report tracked files as ignored. Refuse an inspection error.
    result = subprocess.run(["git", "check-ignore", "-z", "--stdin"], cwd=root,
                            input="\0".join(map(str, paths)) + "\0", text=True,
                            capture_output=True)
    if result.returncode not in (0, 1):
        raise RetentionError(f"git check-ignore failed: {result.stderr.strip()}")
    ignored = {pathlib.Path(p) for p in result.stdout.split("\0") if p}
    answer = {}
    for path in paths:
        if path in ignored:
            try:
                stamp = _stamp(root / path)
            except FileNotFoundError:
                continue
            if stamp is not None:
                answer[path] = stamp
    return answer


def clean_new(root, before, label="gate", include_modified=False):
    """Delete cards this gate created (or, after a complete suite, changed)."""
    root = pathlib.Path(root).resolve()
    if os.environ.get("KEEP_CARDS") == "1":
        return (0, 0)
    after = snapshot(root)
    new = {p: s for p, s in after.items() if p not in before or
           (include_modified and before[p] != s)}
    if not new:
        return (0, 0)
    if not shutil.which("lsof"):
        raise RetentionError("lsof is required before card cleanup")
    # A gate may be writing its log elsewhere in out/. Inspect the candidate
    # cards themselves, so an open log cannot prevent card cleanup.
    names = [str(root / p) for p in new]
    for start in range(0, len(names), 100):
        held = subprocess.run(["lsof", "-nP", "--", *names[start:start + 100]],
                              capture_output=True, text=True)
        if held.returncode != 1 or held.stdout.strip():
            raise RetentionError("a card has open handles or lsof could not verify it is idle")
    current = snapshot(root)
    if any(current.get(p) != stamp for p, stamp in new.items()):
        raise RetentionError("card manifest changed; nothing removed")
    removed = {}
    for path, stamp in sorted(new.items()):
        if not _safe_path(root, path) or _stamp(root / path) != stamp:
            raise RetentionError("card changed during cleanup; stopped")
        (root / path).unlink()
        removed[path] = stamp[2]
    receipt = {"gate": label, "files": {str(p): n for p, n in removed.items()},
               "count": len(removed), "bytes": sum(removed.values())}
    (root / "out/card-retention.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return (receipt["count"], receipt["bytes"])


def begin(root, label):
    try:
        return snapshot(root)
    except (OSError, RetentionError, subprocess.SubprocessError) as exc:
        print(f"card retention: {label}: inspection stopped: {exc}", file=sys.stderr, flush=True)
        return None


def finish(root, before, label, passed, include_modified=False):
    """Best-effort cleanup that never changes the gate's test result."""
    if not passed or before is None:
        return
    try:
        count, size = clean_new(root, before, label, include_modified)
        if count:
            print(f"card retention: {label}: removed {count} cards ({size / 2**20:.0f} MiB)", flush=True)
    except (OSError, RetentionError, subprocess.SubprocessError) as exc:
        print(f"card retention: {label}: cleanup stopped: {exc}", file=sys.stderr, flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("run",))
    ap.add_argument("command", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    command = a.command[1:] if a.command[:1] == ["--"] else a.command
    if not command:
        ap.error("run requires a command after --")
    before = begin(ROOT, " ".join(command))
    rc = subprocess.run(command, cwd=ROOT).returncode
    finish(ROOT, before, " ".join(command), rc == 0, include_modified=True)
    return rc if rc >= 0 else 128 - rc


if __name__ == "__main__":
    sys.exit(main())
