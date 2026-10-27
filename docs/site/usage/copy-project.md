Duplicate a project folder on the CompactFlash card without loading it
first — stock files and module extras (`kits.work`, `scenes.work`,
`brain.work`, `p2lk*`, `BUFFERS/`, …). Stock SAVE TO NEW does not keep
those extras.

## Access

MAIN MENU → PROJECT → CHANGE → highlight a project → FUNC+BANK → COPY
(under RENAME / DELETE). Mount the set that holds the source first
(CHANGE set if needed). Not available on `<CREATE EMPTY PROJECT>`.

## Operation

1. Open the CHANGE project list and highlight the source.
2. FUNC+BANK → COPY.
3. Edit the suggested name (`PROJECT` + date). With RND NAME in the
   remix, FUNC+CUE fills `YYMMDD` + two pool words. The name editor
   caps at 32 characters.
4. Confirm `COPY SRC -> DST?`.
5. On success: `PROJECT COPIED` / `OPEN IT?` — YES closes CHOOSE PROJECT.
   If the live project is dirty: `SAVE CURRENT PROJECT BEFORE OPENING
   COPY?` (YES saves then loads, NO loads without saving). OPEN IT? NO
   leaves the live project as it was. `COPY FAILED` on error; a partial
   destination folder is removed.

This copies whatever is on disk (including unsaved `.work` cache). SAVE
PROJECT on the source first if you want the last saved state only. v1
copies within the mounted set only. Also refuses (no silent truncate)
when the set has more than 64 projects, a directory has more than 256
entries, or an entry name inside the tree is longer than 32 characters.
