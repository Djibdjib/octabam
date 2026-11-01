#!/usr/bin/env python3
"""Render the manual site's generated pages from the manifests.

    python3 tools/site/gen_pages.py

Writes the generated pages (gitignored, so the deploy builds them fresh):

  manual/<remix>/...   the manual of each published remix (gen_manual.py)
  _remix-<name>.md     the module table of each published remix's overview page

Only the remixes in release.REMIXES are published. The pages are rendered at
deploy time (the Pages workflow on main; the site job of ci.yml on a PR), so
the site and the manifests cannot drift. Stdlib only, like the rest of the
tools. The registry execs the manifests, so the author submodules must be
checked out first (git submodule update --init).

Links to the repository are written as full https URLs; no literal
repository path appears in this file on purpose: tools/verify/doclinks.py
scans it too, and every path it finds must exist.
"""

import pathlib
import json
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / pathlib.Path("docs") / "site" / "reference"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1])); import toolpath  # noqa: E402,F401  (every tools/ dir on sys.path)

from remix import registry  # noqa: E402

_SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with", "over"}
_UPPER = {"os", "din", "dj", "eq", "bd", "usb", "midi", "cc", "cpu", "dsp", "cf", "lfo", "ata", "txtr", "amf",
          "fx1", "fx2", "lofi2", "brain", "ui", "id", "sd"}


def title_case(text: str) -> str:
    """Title Case for headings and nav labels. Tokens that already carry capitals
    or digits (device labels, acronyms) and links/code are kept as written."""
    out, started, after_colon = [], False, False
    for tok in text.replace("octabam-", "octabam ").split(" "):
        word = tok.strip(":,()")
        if re.fullmatch(r"[a-z]+(-[a-z]+)+", word):
            tok = tok.replace(word, "-".join(x.upper() if x in _UPPER else x.capitalize() for x in word.split("-")), 1)
            out.append(tok)
            started = True
            continue
        if not re.fullmatch(r"[a-z][a-z']*", word):
            out.append(tok)
            started = started or bool(re.search(r"[A-Za-z]", tok))
            after_colon = tok.endswith(":")
            continue
        if word in _UPPER:
            new = word.upper()
        elif word in _SMALL and started and not after_colon:
            new = word
        else:
            new = word.capitalize()
        out.append(tok.replace(word, new, 1))
        started = True
        after_colon = tok.endswith(":")
    return " ".join(out)


def _label(m) -> str:
    """Readable headings; manifest keys and device labels keep their spelling."""
    names = {
        "analog-bassdrum": "Analog BD",
        "ata-write-guard": "ATA write guard",
        "bbd": "BBD delay",
        "blackpyramids-303": "BlackPyramids 303",
        "character-txtr": "Character TXTR",
        "devilish": "dEVILish",
        "dlcopy": "Effect loader (copier)",
        "dlpump": "Effect loader (sender)",
        "direct-jump-kyoti": "Direct jump (Kyoti)",
        "distorx": "DisTorX",
        "lofi-amf-fix": "Lo-Fi AMF fix",
        "octa303": "OCTA-303",
        "plocks-p2": "Page 2 parameter locks",
        "rec-trig-mute": "Recorder trig mute",
        "rlen-plen": "RLEN PLEN",
        "rnd-name": "Random naming",
        "scenes-p2": "Page 2 scene locks",
        "stems": "Stem recording",
        "tempo-bus": "Tempo controls",
    }
    if m.name in names:
        return title_case(names[m.name])
    acronyms = {"USB", "MIDI", "CC", "FX1", "FX2", "DSP", "CPU", "CF", "LFO", "LOFI2", "BRAIN"}
    words = m.key.replace("_", " ").split()
    return title_case(" ".join(word if word in acronyms else word.lower() for word in words))


def _author(m) -> str:
    if m.is_stock:
        return "stock"
    return f"[{m.author}]({m.author_url})" if m.author_url else (m.author or "?")


def _records(m) -> dict:
    path = OUT.parent / "screenshots.json"
    records = json.loads(path.read_text()) if path.exists() else {}
    return records.get(m.name, {})


def main(quiet: bool = False) -> int:
    import gen_manual
    import release
    mods = registry.modules()
    official = [(n, registry.remix(n)) for n in release.REMIXES]
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {}
    for name, r in official:
        jobs[f"_remix-{name}.md"] = "\n".join(gen_manual.remix_table(name, r, mods)) + "\n"
    jobs.update(gen_manual.main(mods, official))
    for name, text in sorted(jobs.items()):
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        (OUT / name).write_text(text)
        if not quiet:
            print(f"wrote docs/site/reference/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
