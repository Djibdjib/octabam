#!/usr/bin/env python3
"""Render one manual per official remix from the manifests.

    python3 tools/site/gen_manual.py        # also run by gen_pages.py

Writes, gitignored like the rest of the generated site:

  reference/manual/<remix>.md    the remix's manual: numbered chapters, one
                                 numbered section per module, in the order of
                                 the Octatrack's own manual (introduction,
                                 installing, the effects, then the features by
                                 area, then appendices)

Everything that can be read from the manifests is: the contents, which effect
is on FX1 and FX2, the knob layout of each effect's two pages (A to F, the
MODE renames), the settings and what this remix sets them to, the test status,
the credits. The prose is the hand-written usage fragment of each module
(the site's usage directory), inlined with its headings pushed down under the
module's section. A module with no fragment gets its manifest line, so the
manual never has a hole.

The pages sit two levels under the site root, like the per-module pages, so
the image and page links the fragments already carry resolve unchanged.
"""

import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1])); import toolpath  # noqa: E402,F401  (every tools/ dir on sys.path)

import gen_pages  # noqa: E402
from gen_pages import OUT, _author, _label, _records, _hero_key, _figure, title_case  # noqa: E402
from remix import index  # noqa: E402
from remix.schema import CATEGORY_TITLE, PROOF_TEXT, Category, Formatter, Option, Binary, Number, Pin, Trigger, Blob  # noqa: E402

USAGE = OUT.parent / pathlib.Path("usage")

# The chapters after the effects chapters, in the order a reader meets them.
# Each is (category, chapter title); a category the remix has no module in
# gets no chapter, so a small remix has a short manual.
CHAPTERS = (
    (Category.BUS, "Bus and effect setup"),
    (Category.TRACK, "Effects"),
    (Category.STOCK, "Stock effects"),
    (Category.MACHINES, "Machines and the sequencer"),
    (Category.PARTS, "Parts, Kits and scenes"),
    (Category.MIDI_USB, "MIDI and USB"),
    (Category.SETTINGS, "Settings and memory"),
    (Category.UTILITIES, "Utilities"),
    (Category.FIXES, "Fixes to stock behaviour"),
    (Category.REFERENCE, "Diagnostics"),
)

TITLES = {"octabam": "Octabam", "octabam-bus": "Octabam Bus", "cxosc-core": "Octabam CX Osc Core"}
OVERVIEW = {"octabam": "remix-octabam.md", "octabam-bus": "remix-bus.md"}
KNOB = "ABCDEF"


def slug(text: str) -> str:
    """The anchor MkDocs gives a heading (python-markdown's toc slugify)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", text).strip().lower())


def title(name: str) -> str:
    return TITLES.get(name, title_case(name.replace("-", " ")))


# ---- the fragment -------------------------------------------------------

def _demote(text: str, by: int) -> str:
    """Push a fragment's headings down `by` levels, leaving fenced code alone
    (a bash comment starts with the same character)."""
    out, fence = [], None
    for line in text.splitlines():
        m = re.match(r"\s*(```+|~~~+)", line)
        if m:
            fence = None if fence == m.group(1)[:3] else (fence or m.group(1)[:3])
        elif fence is None and re.match(r"#{1,5} ", line):
            line = "#" * by + line
        out.append(line)
    return "\n".join(out)


def _relink(text: str) -> str:
    """A fragment is written for the module pages (reference/modules/), whose
    sibling links are bare file names; the manual sits one directory over."""
    return re.sub(r"\]\((?!https?:|#|\.\./|/)([\w-]+\.md)", r"](../modules/\1", text)


def _without_parameters(text: str) -> str:
    """Drop a fragment's own Parameters table: the manual prints the knobs
    from the manifest, which is the one place a knob's name, range and default
    are declared. (The module's own page keeps the hand-written table.)"""
    return re.sub(r"(?ms)^## Parameters\n.*?(?=^## |\Z)", "", text).strip()


def _fragment(m) -> str | None:
    path = USAGE / f"{m.name}.md"
    if not path.is_file():
        return None
    text = path.read_text().strip()
    if _drawn(m):
        text = _without_parameters(text)
    return _relink(text)


# ---- the facts ----------------------------------------------------------

def _values(p, label_of=None) -> str:
    """What a knob's range reads as on the panel."""
    if p.labels:
        return " / ".join(p.labels)
    if p.formatter is Formatter.BIPOLAR:
        return "−64 to +63"
    if p.count and p.count != 128:
        return f"1 to {p.count}" if p.formatter in (Formatter.STEPPED, Formatter.WIDE_STEPPED) else f"0 to {p.count - 1}"
    return "0 to 127"


def _default(p) -> str:
    if p.default is None:
        return "—"
    if p.labels:
        return p.labels[p.default]
    if p.formatter is Formatter.BIPOLAR:
        return f"{p.default - 64:+d}" if p.default != 64 else "0"
    return str(p.default)


def _drawn(m) -> bool:
    return m.menu is not None and any(p.active for p in m.params)


def controls(m) -> list[str]:
    """The two effect pages as the panel lays them out, then each knob."""
    lines = ["#### Controls", ""]
    for page in (0, 1):
        slots = range(page * 6, page * 6 + 6)
        if not any(m.params[i].active for i in slots):
            continue
        lines += [f"**Page {page + 1}**", "",
                  "| Knob | Name | Values | Default | What it does |", "|---|---|---|---|---|"]
        for i in slots:
            p = m.params[i]
            if not p.active:
                continue
            doc = (p.doc or "").replace("|", "\\|")
            lines.append(f"| {KNOB[i % 6]} | {p.name.decode()} | {_values(p)} | {_default(p)} | {doc} |")
        lines.append("")
    if m.mode_slot is not None and m.mode_views:
        mode = m.params[m.mode_slot]
        renames = [(v, {s: n.decode() for s, n in v.names.items()}) for v in m.mode_views if v.names]
        if renames:
            lines += [f"**What {mode.name.decode()} renames**", "",
                      "| " + mode.name.decode() + " | Knob | Reads as |", "|---|---|---|"]
            for v, names in renames:
                label = mode.labels[v.mode] if mode.labels and v.mode < len(mode.labels) else str(v.mode)
                for slot, name in sorted(names.items()):
                    lines.append(f"| {label} | {KNOB[slot % 6]} on page {slot // 6 + 1} "
                                 f"({m.canon_name(slot) or '—'}) | {name} |")
            lines.append("")
    return lines


def _kind_text(k) -> str:
    if isinstance(k, Binary):
        return "off / on"
    if isinstance(k, Option):
        return " / ".join(k.labels)
    if isinstance(k, Number):
        return f"{k.min} to {k.max}" + (f" {k.unit}" if k.unit else "")
    if isinstance(k, Trigger):
        return "an action"
    if isinstance(k, Blob):
        return "text"
    return "?"


def _setting_value(k, v) -> str:
    if isinstance(k, Binary):
        return "on" if v else "off"
    if isinstance(k, Option):
        i = k.index(v)
        return k.labels[i] if i is not None else str(v)
    return str(v)


def settings(m, r) -> list[str]:
    """The module's settings with the value this remix gives them: a pinned
    setting has no menu row and cannot be changed on the unit."""
    if not m.settings or m.store is None:
        return []
    lines = ["#### Settings in this image", "",
             "| Setting | Values | In this image | Takes effect | What it does |", "|---|---|---|---|---|"]
    applies = {"live": "at once", "callback": "after a load or an edit", "next_boot": "at the next boot",
               "build": "set when the image is built"}
    for s in m.settings:
        mine = r.settings.get((m.store.id, s.name), s.default)
        if isinstance(mine, Pin):
            now = f"{_setting_value(s.kind, mine.value)} (fixed)"
        else:
            now = _setting_value(s.kind, mine)
        when = applies[s.apply.value]
        if s.apply.value != "build":
            when += " (stored with the project)" if s.scope.value == "project" else " (stored on the card)"
        doc = (s.doc or "").replace("|", "\\|")
        lines.append(f"| {s.name} | {_kind_text(s.kind)} | {now} | {when} | {doc} |")
    return lines + [""]


def relations(m, mods) -> list[str]:
    out = []
    if m.requires:
        out.append("Needs " + ", ".join(_ref(mods, k) for k in m.requires) + " in the same image.")
    for other, why in m.conflicts:
        out.append(f"Cannot share an image with {_ref(mods, other)}: {why}.")
    return [" ".join(out), ""] if out else []


def _ref(mods, key) -> str:
    return f"[{_label(mods[key])}](../modules/{mods[key].name}.md)" if key in mods else key


def _on_fx2(m, r) -> bool:
    """FX2 unless the module has a SLOTS build setting that this remix leaves
    on FX1 (the stations: an FX2 instance there is a dry pass)."""
    for s in m.settings:
        if s.name == "SLOTS" and isinstance(s.kind, Option) and m.store is not None:
            mine = r.settings.get((m.store.id, s.name), s.default)
            mine = mine.value if isinstance(mine, Pin) else mine
            i = s.kind.index(mine)
            return i is not None and "FX2" in s.kind.labels[i]
    return True


def where(m, r) -> str | None:
    """Which chooser an effect is in, read from the remix."""
    if m.menu is None or m.is_stock:
        return None
    on = [n for n, ok in (("FX1", m.key in r.fx1), ("FX2", _on_fx2(m, r))) if ok]
    text = " and ".join(on)
    if m.key in r.locked:
        text += " (locked to its host track; the chooser cannot change it)"
    if m.menu.replaces:
        text += f", in place of {m.menu.replaces}"
    return text


# ---- sections ------------------------------------------------------------

def module_section(num: str, m, r, mods) -> list[str]:
    head = f"{num} {_label(m)}"
    lines = [f"### {head}", ""]
    if not m.is_stock:
        lines += [f"*By {_author(m)}.* **Test status:** {index.proof_text(m)}.", ""]
    place = where(m, r)
    if place:
        lines += [f"**Chooser:** {place}.", ""]
    recs = _records(m)
    key = _hero_key(m)
    if key:
        lines += _figure(recs[key])
    frag = _fragment(m)
    lines += [_demote(frag, 2) if frag else m.doc, ""]
    if _drawn(m):
        lines += controls(m)
    lines += settings(m, r)
    lines += relations(m, mods)
    rest = [rec for k, rec in recs.items() if k != key]
    if rest:
        lines += ["#### Screens", ""]
        for rec in rest:
            lines += _figure(rec)
    return lines


def stock_table(r, mods) -> list[str]:
    stock = [mods[k] for k in r.modules if mods[k].is_stock]
    names = [m.key for m in stock]
    fx1_only = [k for k in r.fx1 if k not in mods or k not in r.modules]
    lines = ["| Effect | FX1 | FX2 |", "|---|---|---|"]
    seen = set()
    for k in list(r.fx1) + names:
        if k in seen or (k in mods and not mods[k].is_stock):
            continue
        seen.add(k)
        lines.append(f"| {k} | {'✓' if k in r.fx1 else '—'} | {'✓' if k in names else '—'} |")
    return lines + [""]


def chapters_of(r, mods) -> list[tuple[str, list]]:
    """(chapter title, modules) for each chapter this remix has."""
    out = []
    for cat, name in CHAPTERS:
        ms = [mods[k] for k in r.modules if (mods[k].category or Category.REFERENCE) is cat]
        if ms:
            out.append((name, sorted(ms, key=lambda m: _label(m).lower())))
    return out


def manual(name: str, r, mods) -> str:
    heading = title(name)
    chaps = chapters_of(r, mods)
    first = 3                         # chapters 1 and 2 are fixed
    numbered = [(f"{first + i}", t, ms) for i, (t, ms) in enumerate(chaps)]
    appendices = (("A", "Effect controls at a glance"), ("B", "Test status"), ("C", "Credits"))
    toc = [("1", "Introduction"), ("2", "Installing")] + [(n, t) for n, t, _ in numbered] + list(appendices)

    def h(num, text):
        return f"Appendix {num}: {text}" if num.isalpha() else f"{num} {text}"

    L = [f"# {heading} Manual", "",
         f"The manual for the **{heading}** image: an Octatrack OS 1.40C patched by "
         f"the modules listed here, each credited to its author. This manual is "
         f"generated from the module manifests, so it lists what this image contains "
         f"and nothing else.", ""]
    if name in OVERVIEW:
        L += [f"For the short version, see the [{heading} overview](../../{OVERVIEW[name]}).", ""]
    L += ["## Contents", ""]
    for num, text in toc:
        label = h(num, text)
        L.append(f"- [{label}](#{slug(label)})")
    L.append("")

    # 1 Introduction
    L += ["## 1 Introduction", "", f"### 1.1 About {heading}", "", r.doc, "",
          f"**Where it has run:** {index.proof_text(r)}.", "",
          "### 1.2 Conventions", "",
          "Names in capitals are what the unit's screen prints. Effects sit on the FX1 and "
          "FX2 keys; each has two pages of six knobs, A to F, reached with the PAGE keys "
          "as on any Octatrack effect. A module's **Test status** says how far it has been proven:", "",
          gen_pages.PROOF_LEGEND, ""]
    L += ["### 1.3 What is in this image", "",
          "| Chapter | Features |", "|---|---|"]
    for num, t, ms in numbered:
        L.append(f"| [{num} {t}](#{slug(f'{num} {t}')}) | " + ", ".join(_label(m) for m in ms) + " |")
    L.append("")

    # 2 Installing
    L += ["## 2 Installing", "",
          f"Build the image from your own copy of OS 1.40C and install it as described in "
          f"[Build and Install](../../web-builder.md). Nothing from Elektron is in the repository "
          f"or on this site; the builder patches your copy in your browser. "
          f"After the flash, SYSTEM STATUS → OS VERSION shows `{r.name.upper()}` and the build tag.", "",
          "Back up the card first. To go back to stock, follow [Safety and Recovery](../../safety.md).", ""]

    # 3.. the chapters
    for num, t, ms in numbered:
        L += [f"## {num} {t}", ""]
        if t == "Stock effects":
            L += ["These stock effects stay in the chooser as Elektron made them.", ""]
            L += stock_table(r, mods)
            continue
        for i, m in enumerate(ms, 1):
            L += module_section(f"{num}.{i}", m, r, mods)

    # Appendices
    effects = [m for _, _, ms in numbered for m in ms if _drawn(m) and not m.is_stock]
    L += [f"## {h(*appendices[0])}", "",
          "Knob names as the panel prints them (a MODE can rename some; see each effect).", ""]
    for page in (0, 1):
        L += [f"**Page {page + 1}**", "",
              "| Effect | " + " | ".join(KNOB) + " |", "|---|" + "---|" * 6]
        for m in sorted(effects, key=lambda m: _label(m).lower()):
            row = [(m.params[i].name or b"").decode() or "—" if m.params[i].active else "—"
                   for i in range(page * 6, page * 6 + 6)]
            if all(c == "—" for c in row):
                continue
            L.append(f"| {_label(m)} | " + " | ".join(row) + " |")
        L.append("")
    L += [f"## {h(*appendices[1])}", "",
          "| Feature | Status |", "|---|---|"]
    for _, _, ms in numbered:
        for m in ms:
            if not m.is_stock:
                L.append(f"| {_label(m)} | {PROOF_TEXT[m.proof]} |")
    L += ["", f"## {h(*appendices[2])}", ""]
    by_author = {}
    for _, _, ms in numbered:
        for m in ms:
            if not m.is_stock:
                by_author.setdefault((m.author, m.author_url), []).append(m)
    for (author, url), ms in sorted(by_author.items(), key=lambda kv: kv[0][0].lower()):
        who = f"[{author}]({url})" if url else author
        L.append(f"- {who}: " + ", ".join(_label(m) for m in sorted(ms, key=lambda m: m.key)))
    L += ["", "[Feature directory](../modules.md)"]
    return "\n".join(L) + "\n"


def main(mods, official, quiet: bool = False) -> dict[str, str]:
    """The manual pages, keyed by their path under reference/."""
    jobs = {}
    for name, r in official:
        jobs[f"manual/{name}.md"] = manual(name, r, mods)
    return jobs


if __name__ == "__main__":
    sys.exit(gen_pages.main())
