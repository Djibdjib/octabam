# COPY PROJECT

Duplicate a project folder on the CompactFlash card without loading it
first.

**PROJECT → CHANGE → highlight a project → FUNC+BANK → COPY** (under
RENAME / DELETE) asks for a name, confirms, and copies the source folder
byte-for-byte into a new folder — stock project files and module extras
alike. Stock SAVE TO NEW writes a fresh project and drops those extras.
After a successful copy it asks whether to open the copy (stock LOAD
PROJECT).

Entry used to be a PROJECT menu TableGrow (15→16); that blob no longer
packs beside long FX1 + QUANTIZER on a full tip (#931). The FUNC+BANK
popup grows 2→3 instead (`docs/firmware/PANEL.md`).

**Sidecars** = non-stock files modules leave in the project folder
(`kits.work` / `kits.strd`, `scenes.work`, `brain.work`, `p2lkNN.work`,
`BUFFERS/`, …). A folder copy keeps them; SAVE TO NEW does not. On a
live card set they show up next to `project.work` / `bankNN.work` (e.g.
`261018 IDLEYARD`, `!DEF_TMPL`).

## Use

1. Mount the set that holds the source project (CHANGE set if needed).
2. PROJECT → CHANGE → highlight the source (folders with `project.work` /
   `project.strd`; not `<CREATE EMPTY PROJECT>`).
3. FUNC+BANK → COPY.
4. Edit the suggested name (`PROJECT YYMMDD`, or FUNC+CUE with RND NAME)
   and YES. The name editor itself caps at 32 characters.
5. Confirm `COPY SRC -> DST?` (16-char display cap on the line).
6. On success: `PROJECT COPIED` / `OPEN IT?` — YES closes CHOOSE PROJECT,
   and if the live project is dirty asks `SAVE CURRENT PROJECT BEFORE
   OPENING COPY?` (YES = stock SAVE / card sync, then load; NO = load
   without saving). OPEN IT? NO leaves the live project as it was.
   `COPY FAILED` on error; a partial destination folder is removed so a
   retry does not hit `NAME ALREADY IN USE!`.

This is a card-to-card copy of whatever is on disk (including unsaved
`.work` cache). SAVE PROJECT on the source first if you want the last
saved state only.

Limits that refuse with `COPY FAILED` (no silent truncate / partial
copy): more than 64 projects in the set, a directory with more than 256
entries, an entry name longer than 32 characters inside the tree, or
nesting deeper than 6 folders.

## Measured

🟡 FUNC+BANK LISTPOP handlers/labels at `0x400cbaac` / `0x400cbab4`,
count poke at `0x400641a2`; selection name `0x100f8378` (same pea as
stock RENAME/DELETE). Mapped under the port 27 Oct 2026.

🟡 Dir-scan borrow/restore follows REMIX SWITCH
(`docs/contributing/FAILURE_MODES.md`). Copy uses stock `DIRSCAN`
(`0x4007f598`), mkdir (`0x46c8240a`), and file copy (`0x40016388`) from
an engine job (type 21), posted like REMIX SWITCH's deferred load.
Failed-copy cleanup uses stock's recursive walker (`0x40090a14`, mode 0).
Gated under the port: a source directory with more than 256 entries
forces `COPY FAILED`, removes the partial destination, leaves SRC
intact, and a retry with the same name does not read
`NAME ALREADY IN USE!`.

## On the unit

Flashed with CF card update and tested on the author's MKII (17 Oct 2026)
as PROJECT-menu COPY PROJECT. BUILD of that flash was not recorded.
Re-home to FUNC+BANK (#931) is port-gated; hardware re-check pending.

U1 (`LATEST U1`, 19 Oct 2026): a long project name stretched the pick
list until nothing drew — fixed by the 16-char display cap (full name
still copied). Name editor >32 is unreachable (form cap). Sidecars
present on the author's DEFAULT set (`kits.work`, `scenes.work`,
`brain.work`, `p2lk*`, `BUFFERS/`). Not tried: a directory near/over 256
entries, or copying while the sequencer plays.

## Open

- Cross-set copy (v1 is the mounted set only).
- Hardware confirm of the FUNC+BANK entry.

## Gates

`make check REMIX=copy-project` (test remix). Port gate:
`tools/verify/verify_copy_project.py` — CHANGE → FUNC+BANK → COPY,
stages SRC, copies to the stock default name under a pinned RTC, checks
`project.work` and the rest of the folder.
