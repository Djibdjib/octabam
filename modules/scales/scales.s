| SCALES -- one catalogue of scales for every module, a scale chooser, and
| the CHROMATIC trig keys lit with the scale.
|
| The catalogue. A scale is a 12-bit mask over the semitones above its
| tonic: bit d set = d semitones above the tonic is in the scale (bit 0,
| the tonic, always). Written from the tonic up, IONIAN is 1010 1101 0101
| (C . D . E F . G . A . B), the word 0xab5. A scale's ID (1..SC_COUNT)
| names it for good: a saved ID never changes meaning, a new scale takes
| the next ID. The IDs are grouped in families (MAJOR and its modes,
| MELODIC MINOR and its modes, ...), in the chooser's order.
|
| The service (README "Service"), register calls, d0-d1/a0-a1 scratch:
|   sc_count    -> d0 = SC_COUNT
|   sc_mask     d0 ID -> d0 = its mask, 0 for no such ID
|   sc_name     d0 ID -> a0 = its name (the chooser's), d0 = 0 for no such ID
|   sc_short    d0 ID -> a0 = its 4-character name (the KEY field's)
|   sc_family   d0 ID -> d0 = its family 0..SC_FAMILIES-1, -1 for no such ID
|   sc_snap     d0 note 0..127, d1 = ID << 4 | tonic -> d0 = the nearest
|               note of that scale (ties downward); every other register kept
|   sc_pick     d0 the ID shown first, a0 = a routine to call with the ID
|               chosen (d0): the chooser (C call, UI task only)
|   sc_track    d0 MIDI track 0..7 -> d0 = ID << 4 | tonic, -1 for KEY OFF
|
| The chooser is stock's list window (0x4006d94c, the one BRAIN and STORE
| open): the families, then the chosen family's scales. YES picks a row,
| NO closes it.
|
| A MIDI track's scale. Its KEY (ARP SETUP, setup record +0x11) keeps the
| tonic and, for the seven diatonic modes, the mode -- the values stock
| (1..24) and MIDI SCALES (25..84) gave it, so a project saved with either
| plays as before. A scale outside those seven also writes its ID in the
| setup record's +0x12, a byte with no parameter (CTRL1's setup slot 0,
| MIDI_TRACKS.md): stock loads it (clamped to 127) and saves it, and
| CTRL1's commit-all writes back the value its window read. The KEY then
| holds the tonic in Major or Minor (the scale's third), what stock plays
| for it. +0x12 = 0: the KEY's own mode.
|
| ARP SETUP's KEY (encoder F): turned, the tonic (OFF, C .. B), the scale
| kept; pressed and released without a turn, the chooser. The sequencer's
| and the arpeggiator's notes snap to the scale at stock's output
| quantization point (0x4009fb58); stock's Major / Minor stay stock's.
|
| The CHROMATIC keys. Stock's trig-LED pass (0x40043fdc), in CHROMATIC trig
| mode (0x460d16f0 = 1), draws C major whatever the track's KEY: key k,
| n = k mod 12, n 0 is C (red and green, yellow), the white keys red, the
| black keys dark. This draws the scale kl_source gives for the current
| track instead, in the same colours: the tonic yellow, the scale's other
| notes red, the notes outside it dark. No scale: stock's own loop runs.
| kl_source is the one question the display asks (README "Sources"); on a
| MIDI track sc_track answers it (key 1 = C, as stock's keyboard is), on an
| audio track SCALE QUANTIZER when the remix has it (its SCALE on its ROOT,
| key 1 = ROOT, as its keyboard plays).
|
| Detour at 0x400442e2, the CHROMATIC branch's first instructions
| (`clrl %d5; clrl %d4; clrl %d6; lea SET_LEVEL,%a3`). The pass saved
| d2-d6/a2-a5 at its entry, so the loop keeps its state there; the LED
| routines and the sources are C calls (d0-d1/a0-a1 scratch). After the
| 16th key, stock goes to 0x400444f4 with d3 = 0, which is where this one
| ends.
|
| Stock runs the pass when a key or a mode change asks the LED dispatcher
| for it, not when a KEY, a SCALE or a ROOT is turned. Detour at
| 0x40056ab8, the UI task's per-tick routine (`tstl 0x460d1e4c`): in
| CHROMATIC, kl_tick asks the source again and, when the answer differs
| from what the keyboard shows, asks the dispatcher for the trig LEDs
| (0x4007e998(0)), as stock does after a CHROMATIC key. The same tick
| watches encoder F's push switch while ARP SETUP is open.

        .include "remix.inc"            | HAVE_SCALE_QUANTIZER

        .text
        .globl  sc_count, sc_mask, sc_name, sc_short, sc_family, sc_snap
        .globl  sc_pick, sc_track
        .globl  kl_chromatic, kl_source, kl_tick
        .globl  sc_encoder, sc_output, sc_format
        .balign 2

        .equ    SC_COUNT,  52
        .equ    SC_FAMILIES, 9
        .equ    DIATONIC,  7            | IDs 1..7: the KEY's own modes, +0x12 = 0
        .equ    MINOR,     5            | the KEY's mode of natural Minor (ID 6)
        .equ    STOCK_KEYS, 24          | stock's KEY values: 12 tonics x Major / Minor
        .equ    LAST_KEY,  84           | MIDI SCALES' last KEY value

        .equ    SCALE_AT,  0x400d2ca8   | SCALE QUANTIZER: d0 := the ROOT-rotated SCALE mask, 0 OFF; clobbers a0
        .equ    NV_ROOT,   0x100b14ee   | SCALE QUANTIZER: ROOT, 0..11 = C .. B
        .equ    SET_LEVEL, 0x400135b0   | (id, level): the LED's brightness nibble, sent when it changes
        .equ    LED_ON,    0x400131a0   | (id): the LED's bitmap bit set
        .equ    CUR_TRACK, 0x80000000   | byte: the UI's current track
        .equ    MIDI_MODE, 0x80000012   | long: nonzero in MIDI mode
        .equ    LIVE_SETUP, 0x46c76de0  | + 68 * t + offset: MIDI track t's live setup byte
        .equ    KEY,       0x11         | the setup record's KEY
        .equ    EXT,       0x12         | the setup record's scale ID byte (CTRL1 setup slot 0, no parameter)
        .equ    TRIG_MODE, 0x460d16f0   | long: the trig mode, 1 = CHROMATIC
        .equ    LED_PASS,  0x4007e998   | (slot): the LED dispatcher; slot 0 runs the trig-LED pass
        .equ    TICK_BACK, 0x40056abe   | the per-tick routine after its first instruction
        .equ    TICK_FLAG, 0x460d1e4c   | what that instruction tests
        .equ    STOCK_LOOP, 0x400442ee  | stock's loop, after the displaced span
        .equ    LOOP_DONE, 0x400444f4   | stock after the 16th key, d3 = 0
        .equ    FULL,      15

        .equ    UI_TRACK,  0x100b14cc   | byte: the setup windows' MIDI track
        .equ    UI_PART,   0x100b14cf   | byte: the current Part
        .equ    BANK_RAM,  0x46c82456   | long: the current bank's RAM
        .equ    PART_SETUP, 0x8f262     | + bank RAM + 0x18b2 * p + 0x24 * t: the Part's setup record
        .equ    CS1_SETUP, 0x100a53b0   | + 0x18b2 * p + 0x24 * t: its CS1 mirror
        .equ    PART_LEN,  0x18b2
        .equ    DIRTY_BANK, 0x95048     | + bank RAM: byte, 1 << p = the Part unsaved
        .equ    DIRTY,     0x100b145e   | byte, 1 << p
        .equ    CHANGED_BANK, 0x9b332   | + bank RAM: long 1 (MIDI_TRACKS.md section 3)
        .equ    CHANGED,   0x100f8598   | long 1
        .equ    EDIT_OPEN, 0x40027de4   | what stock's setup writers call first
        .equ    EDIT_DONE, 0x40027e00   | ... and after the stores
        .equ    ARP_WINDOW, 0x400cfebe  | long: ARP SETUP's window, 0 closed
        .equ    ARP_DRAW,  0x40079d48   | () ARP SETUP's draw
        .equ    KEY_DONE,  0x4007a3ea   | ARP SETUP's KEY store, d5 = the change
        .equ    KEY_OTHER, 0x4007a4cc   | ARP SETUP's handler for encoders past F
        .equ    UI_DELTA,  0x40032510   | (encoder, movement, 1024): stock's detent accumulator
        .equ    OUT_STOCK, 0x4009fb5e   | stock's output quantization
        .equ    OUT_DONE,  0x4009fb80   | ... and after it
        .equ    LISTPOP,   0x4006d94c   | (count, sel, &sel, labels, handlers): stock's list window
        .equ    LIST_OPEN, 0x460e5e30   | long: nonzero while a list window is open
        .equ    DIALOG_OPEN, 0x460e5cd0 | long: nonzero while a stock dialog owns the keys
        .equ    TEXT_OPEN, 0x460e7612   | long: nonzero while a text editor is open
        .equ    PUSH_F,    0x46c7d8de+0x10+0x3d*0x18 | long: nonzero while encoder F is pushed (key 0x3d)

| ==== the catalogue ========================================================

sc_count:
        moveq   #SC_COUNT,%d0
        rts

| d0 ID -> d0 = ID - 1, Z clear and the carry clear for an ID in 1..SC_COUNT.
sc_index:
        subq.l  #1,%d0
        cmpi.l  #SC_COUNT,%d0
        rts                             | bcc: no such ID (0 wraps to 0xffffffff)

sc_mask:
        bsr.s   sc_index
        bcc.s   1f
        lea     sc_masks,%a0
        mvz.w   (%a0,%d0.l*2),%d0
        rts
1:      moveq   #0,%d0
        rts

sc_name:
        bsr.s   sc_index
        bcc.s   1f
        lea     sc_names,%a0
        move.l  (%a0,%d0.l*4),%a0
        moveq   #1,%d0
        rts
1:      moveq   #0,%d0
        rts

sc_short:
        bsr.s   sc_index
        bcc.s   1f
        lea     sc_shorts,%a0
        lsl.l   #2,%d0
        adda.l  %d0,%a0
        moveq   #1,%d0
        rts
1:      moveq   #0,%d0
        rts

sc_family:
        bsr.s   sc_index
        bcc.s   1f
        lea     sc_families,%a0
        mvz.b   (%a0,%d0.l),%d0
        rts
1:      moveq   #-1,%d0
        rts

| d0 note, d1 = ID << 4 | tonic -> d0 = the nearest note in the scale, ties
| downward (MIDI SCALES' rule); an unknown ID or a note past 127: d0 kept.
sc_snap:
        lea     -24(%sp),%sp
        movem.l %d1-%d5/%a0,(%sp)
        move.l  %d0,%d2                 | the note
        cmpi.l  #127,%d2
        bhi.s   9f
        move.l  %d1,%d3
        andi.l  #15,%d3                 | the tonic
        move.l  %d1,%d0
        lsr.l   #4,%d0
        bsr.w   sc_mask
        move.l  %d0,%d4                 | the mask
        beq.s   9f
        moveq   #0,%d5                  | the distance
1:      move.l  %d2,%d0
        sub.l   %d5,%d0
        bmi.s   2f
        bsr.s   3f
        bne.s   8f
2:      move.l  %d2,%d0
        add.l   %d5,%d0
        cmpi.l  #127,%d0
        bhi.s   4f
        bsr.s   3f
        bne.s   8f
4:      addq.l  #1,%d5
        bra.s   1b
| d0 note -> Z clear when its degree above the tonic is in the mask.
3:      move.l  %d0,%d1
        sub.l   %d3,%d1
        addi.l  #120,%d1                | >= 0 for any note and tonic
5:      cmpi.l  #12,%d1
        blt.s   6f
        subi.l  #12,%d1
        bra.s   5b
6:      btst    %d1,%d4
        rts
8:      move.l  %d0,%d2
9:      move.l  %d2,%d0
        movem.l (%sp),%d1-%d5/%a0
        lea     24(%sp),%sp
        rts

| ==== a MIDI track's scale =================================================

| d0 KEY value -> d0 = mode << 4 | tonic (mode in kl_masks' order: MAJ DOR
| PHR LYD MIX MIN LOC = ID - 1), -1 for OFF or past MIDI SCALES' values.
sc_key_decode:
        tst.l   %d0
        beq.s   9f
        cmpi.l  #LAST_KEY,%d0
        bhi.s   9f
        cmpi.l  #STOCK_KEYS,%d0
        bhi.s   2f
        subq.l  #1,%d0                  | stock: (tonic << 1) | Minor
        move.l  %d0,%d1
        lsr.l   #1,%d0                  | the tonic
        andi.l  #1,%d1
        beq.s   1f
        ori.l   #MINOR << 4,%d0
1:      rts
2:      subi.l  #STOCK_KEYS + 1,%d0     | MIDI SCALES: 5 modes a tonic, DOR PHR LYD MIX LOC
        moveq   #0,%d1
3:      cmpi.l  #5,%d0
        blt.s   4f
        subq.l  #5,%d0
        addq.l  #1,%d1
        bra.s   3b
4:      addq.l  #1,%d0                  | DOR = 1 .. MIX = 4
        cmpi.l  #5,%d0
        bne.s   5f
        moveq   #6,%d0                  | LOC
5:      lsl.l   #4,%d0
        or.l    %d1,%d0
        rts
9:      moveq   #-1,%d0
        rts

| d0 = mode << 4 | tonic -> d0 = the KEY value (the inverse of sc_key_decode).
sc_key_encode:
        move.l  %d0,%d1
        andi.l  #15,%d1                 | the tonic
        lsr.l   #4,%d0                  | the mode
        bne.s   1f
        add.l   %d1,%d1                 | Major: 2 * tonic + 1
        move.l  %d1,%d0
        addq.l  #1,%d0
        rts
1:      cmpi.l  #MINOR,%d0
        bne.s   2f
        add.l   %d1,%d1                 | Minor: 2 * tonic + 2
        move.l  %d1,%d0
        addq.l  #2,%d0
        rts
2:      cmpi.l  #6,%d0
        bne.s   3f
        moveq   #5,%d0                  | LOC is MIDI SCALES' fifth
3:      subq.l  #1,%d0
        add.l   %d1,%d0                 | 25 + 5 * tonic + (mode - 1)
        lsl.l   #2,%d1
        add.l   %d1,%d0
        addi.l  #STOCK_KEYS + 1,%d0
        rts

| d0 ID -> d0 = the KEY mode that stands for it: the ID's own for 1..7,
| else Minor when the scale has a minor third and no major one, else Major
| (no ID, 0, too).
sc_key_mode:
        tst.l   %d0
        beq.s   2f
        cmpi.l  #DIATONIC,%d0
        bhi.s   1f
        subq.l  #1,%d0
        rts
1:      bsr.w   sc_mask
        btst    #4,%d0
        bne.s   2f
        btst    #3,%d0
        beq.s   2f
        moveq   #MINOR,%d0
        rts
2:      moveq   #0,%d0
        rts

| d0 MIDI track 0..7 -> a0 = its live setup record.
sc_live:
        move.l  %d0,%d1
        lsl.l   #6,%d0
        lsl.l   #2,%d1
        add.l   %d1,%d0                 | 68 * t
        lea     LIVE_SETUP,%a0
        adda.l  %d0,%a0
        rts

sc_track:
        bsr.s   sc_live
        mvz.b   KEY(%a0),%d0
        mvz.b   EXT(%a0),%d1
        move.l  %d1,-(%sp)
        bsr.w   sc_key_decode
        move.l  (%sp)+,%d1
        tst.l   %d0
        bmi.s   9f                      | KEY OFF
        subq.l  #1,%d1
        cmpi.l  #SC_COUNT,%d1
        bcs.s   1f                      | +0x12 names a scale
        move.l  %d0,%d1
        lsr.l   #4,%d1                  | else the KEY's mode: ID - 1
1:      addq.l  #1,%d1
        lsl.l   #4,%d1
        andi.l  #15,%d0
        or.l    %d1,%d0
9:      rts

| ==== the chooser ==========================================================

| sc_pick: d0 the ID shown first, a0 the routine the chosen ID goes to.
sc_pick:
        move.l  %a0,sc_client
        move.l  %d0,sc_shown
        bsr.w   sc_family
        tst.l   %d0
        bpl.s   1f
        moveq   #0,%d0
1:      move.l  %d0,sc_famsel
        pea     sc_fam_cbs
        pea     sc_fam_labels
        pea     sc_famsel
        move.l  %d0,-(%sp)
        pea     SC_FAMILIES
        jsr     LISTPOP
        lea     20(%sp),%sp
        rts

| A family row (C call, no argument): its scales, the one shown first
| selected when it is in this family.
sc_fam_cb:
        move.l  %d2,-(%sp)
        move.l  sc_famsel,%d2
        cmpi.l  #SC_FAMILIES,%d2
        bcc.s   9f
        lea     sc_fam_first,%a0
        mvz.b   (%a0,%d2.l),%d1         | the family's first ID - 1
        move.l  %d1,sc_modebase
        mvz.b   1(%a0,%d2.l),%d0
        sub.l   %d1,%d0                 | its count
        move.l  sc_shown,%d2
        subq.l  #1,%d2
        sub.l   %d1,%d2                 | the shown ID's row
        cmp.l   %d0,%d2
        bcs.s   1f
        moveq   #0,%d2
1:      move.l  %d2,sc_modesel
        pea     sc_mode_cbs
        lea     sc_names,%a0
        lsl.l   #2,%d1
        pea     (%a0,%d1.l)
        pea     sc_modesel
        move.l  %d2,-(%sp)
        move.l  %d0,-(%sp)
        jsr     LISTPOP
        lea     20(%sp),%sp
9:      move.l  (%sp)+,%d2
        rts

| A scale row: its ID to the client.
sc_mode_cb:
        lea     -24(%sp),%sp
        movem.l %d2-%d7,(%sp)
        move.l  sc_modebase,%d0
        add.l   sc_modesel,%d0
        addq.l  #1,%d0
        move.l  sc_client,%d1
        beq.s   1f
        move.l  %d1,%a0
        jsr     (%a0)
1:      movem.l (%sp),%d2-%d7
        lea     24(%sp),%sp
        rts

| ==== ARP SETUP's KEY ======================================================

| d0 setup offset, d1 value: the UI track's setup byte, stored as stock's
| ARP SETUP writer stores the KEY (0x4007a3ea..): the Part, the CS1 mirror,
| the unsaved flags, the live byte.
sc_setup_write:
        lea     -16(%sp),%sp
        movem.l %d2-%d4/%a2,(%sp)
        move.l  %d0,%d2
        move.l  %d1,%d3
        jsr     EDIT_OPEN
        mvz.b   UI_PART,%d4
        mvz.b   UI_TRACK,%d0
        move.l  %d0,%d1
        lsl.l   #5,%d0
        lsl.l   #2,%d1
        add.l   %d1,%d0                 | 36 * t
        add.l   %d2,%d0                 | + offset
        move.l  #PART_LEN,%d1
        muls.l  %d4,%d1
        add.l   %d1,%d0                 | + 0x18b2 * p
        move.l  BANK_RAM,%a2
        lea     (%a2,%d0.l),%a0
        adda.l  #PART_SETUP,%a0
        move.b  %d3,(%a0)
        lea     CS1_SETUP,%a0
        move.b  %d3,(%a0,%d0.l)
        moveq   #1,%d1
        lsl.l   %d4,%d1
        lea     (%a2),%a0
        adda.l  #DIRTY_BANK,%a0
        mvz.b   (%a0),%d0
        or.l    %d1,%d0
        move.b  %d0,(%a0)
        mvz.b   DIRTY,%d0
        or.l    %d1,%d0
        move.b  %d0,DIRTY
        moveq   #1,%d0
        lea     (%a2),%a0
        adda.l  #CHANGED_BANK,%a0
        move.l  %d0,(%a0)
        move.l  %d0,CHANGED
        jsr     EDIT_DONE
        mvz.b   UI_TRACK,%d0
        bsr.w   sc_live
        move.b  %d3,(%a0,%d2.l)
        movem.l (%sp),%d2-%d4/%a2
        lea     16(%sp),%sp
        rts

| The chooser's client for ARP SETUP: d0 the chosen ID -> the KEY (the
| tonic kept, C when it was OFF) and +0x12.
sc_key_chosen:
        lea     -12(%sp),%sp
        movem.l %d2-%d4,(%sp)
        move.l  %d0,%d2                 | the ID
        mvz.b   UI_TRACK,%d0
        bsr.w   sc_live
        mvz.b   KEY(%a0),%d0
        bsr.w   sc_key_decode
        moveq   #15,%d3
        and.l   %d0,%d3                 | the tonic
        tst.l   %d0
        bpl.s   1f
        moveq   #0,%d3                  | OFF: C
1:      move.l  %d2,%d0
        bsr.w   sc_key_mode
        lsl.l   #4,%d0
        or.l    %d3,%d0
        bsr.w   sc_key_encode
        move.l  %d0,%d1
        moveq   #KEY,%d0
        bsr.w   sc_setup_write
        moveq   #0,%d1                  | IDs 1..7: the KEY says it
        cmpi.l  #DIATONIC,%d2
        bls.s   2f
        move.l  %d2,%d1
2:      moveq   #EXT,%d0
        bsr.w   sc_setup_write
        tst.l   ARP_WINDOW
        beq.s   3f
        jsr     ARP_DRAW
3:      movem.l (%sp),%d2-%d4
        lea     12(%sp),%sp
        rts

| Detour at 0x4007a3e2 (`moveq #5,%d1; cmpl %d0,%d1; bnew 0x4007a4cc`), in
| ARP SETUP's encoder handler: d0 the encoder, d5 its movement. Encoder F
| (5): the tonic, OFF and C .. B, one a detent; the scale kept. The change
| goes to stock's store in d5, which clamps and stores as for any KEY.
sc_encoder:
        moveq   #5,%d1
        cmp.l   %d0,%d1
        bne.w   9f
        lea     -20(%sp),%sp
        movem.l %d0-%d3/%a0,(%sp)
        moveq   #1,%d0
        move.l  %d0,sc_turned           | a turn while pushed is no press
        mvz.b   UI_TRACK,%d0
        bsr.w   sc_live
        mvz.b   KEY(%a0),%d2            | the KEY before
        mvz.b   EXT(%a0),%d3
        move.l  %d2,%d0
        bsr.w   sc_key_decode
        moveq   #0,%d1                  | OFF: ordinal 0
        tst.l   %d0
        bmi.s   1f
        move.l  %d0,%d1
        andi.l  #15,%d1
        addq.l  #1,%d1                  | C .. B: 1 .. 12
1:      move.l  %d1,-(%sp)              | the ordinal
        move.l  %d0,-(%sp)              | mode << 4 | tonic, or -1
        move.l  %d5,%d1
        cmpi.l  #4,%d1                  | MIDI SCALES' accumulator: four counts a step
        ble.s   2f
        moveq   #4,%d1
2:      cmpi.l  #-4,%d1
        bge.s   3f
        moveq   #-4,%d1
3:      pea     1024
        move.l  %d1,-(%sp)
        pea     5
        jsr     UI_DELTA
        lea     12(%sp),%sp
        move.l  (%sp)+,%d1              | mode << 4 | tonic, or -1
        add.l   (%sp)+,%d0              | the new ordinal
        bpl.s   4f
        moveq   #0,%d0
4:      cmpi.l  #12,%d0
        ble.s   5f
        moveq   #12,%d0
5:      tst.l   %d0
        beq.s   8f                      | OFF: KEY 0
        subq.l  #1,%d0                  | the new tonic
        tst.l   %d1
        bmi.s   6f
        andi.l  #0xf0,%d1               | the mode kept
        bra.s   7f
6:      move.l  %d0,-(%sp)              | from OFF: the mode for +0x12's scale
        move.l  %d3,%d0
        bsr.w   sc_key_mode
        move.l  %d0,%d1
        lsl.l   #4,%d1
        move.l  (%sp)+,%d0
7:      or.l    %d1,%d0
        bsr.w   sc_key_encode
8:      sub.l   %d2,%d0
        move.l  %d0,%d5                 | the change, for stock's store
        movem.l (%sp),%d0-%d3/%a0
        lea     20(%sp),%sp
        jmp     KEY_DONE
9:      jmp     KEY_OTHER

| Detour at 0x4009fb58 (`tstl %fp@(-64); bles 0x4009fb80`), stock's output
| quantization: d7 the MIDI track, a2 the note. A scale stock does not play
| (MIDI SCALES' modes, +0x12's) snaps here; stock's Major / Minor and OFF
| go on as stock's.
sc_output:
        lea     -12(%sp),%sp
        movem.l %d0-%d1/%a0,(%sp)
        move.l  %d7,%d0
        bsr.w   sc_live
        mvz.b   EXT(%a0),%d1
        mvz.b   KEY(%a0),%d0
        beq.s   8f                      | OFF
        subq.l  #1,%d1
        cmpi.l  #SC_COUNT,%d1
        bcs.s   1f                      | +0x12 names a scale
        cmpi.l  #STOCK_KEYS,%d0
        bls.s   8f                      | stock's own
1:      move.l  %d7,%d0
        bsr.w   sc_track
        tst.l   %d0
        bmi.s   8f
        move.l  %d0,%d1
        moveq   #0,%d0
        move.b  (%a2),%d0
        bsr.w   sc_snap
        move.b  %d0,(%a2)
        movem.l (%sp),%d0-%d1/%a0
        lea     12(%sp),%sp
        jmp     OUT_DONE
8:      movem.l (%sp),%d0-%d1/%a0
        lea     12(%sp),%sp
        tst.l   -64(%fp)
        ble.s   9f
        jmp     OUT_STOCK
9:      jmp     OUT_DONE

| Stock's KEY formatter (pointer at 0x400d40c6): two five-byte strings, the
| tonic and the scale's 4-character name.
sc_format:
        lea     -8(%sp),%sp
        movem.l %d2/%a2,(%sp)
        move.l  12(%sp),%a2
        clr.l   (%a2)
        clr.l   4(%a2)
        clr.w   8(%a2)
        mvz.b   UI_TRACK,%d0
        bsr.w   sc_track
        tst.l   %d0
        bmi.s   1f
        move.l  %d0,%d2
        andi.l  #15,%d0
        lea     sc_tonics,%a0
        move.w  (%a0,%d0.l*2),(%a2)
        move.l  %d2,%d0
        lsr.l   #4,%d0
        bsr.w   sc_short
        move.l  (%a0),5(%a2)
        bra.s   2f
1:      move.l  #0x4f464600,(%a2)       | "OFF"
2:      movem.l (%sp),%d2/%a2
        lea     8(%sp),%sp
        rts

| ==== the CHROMATIC keys ===================================================

| d2 = LED id (2 * key), d4 = the pitch class key k sounds (key 1's, then
| + 1 mod 12), d5 = the tonic, d6 = the scale's pitch classes (bit p =
| pitch class p, C = 0).
kl_chromatic:
        bsr.w   kl_current
        move.l  %d0,kl_shown
        tst.l   %d0
        bmi.w   kl_stock
        move.l  %d0,%d5
        and.l   #15,%d5
        move.l  %d0,%d4
        lsr.l   #4,%d4
        and.l   #15,%d4
        move.l  %d0,%d6
        lsr.l   #8,%d6
        moveq   #0,%d2
| one key: red and green levels, then the bits on, as stock's loop does
5:      moveq   #0,%d3                  | green
        moveq   #0,%d1                  | red
        cmp.l   %d5,%d4
        bne.s   7f
        moveq   #FULL,%d3               | the tonic: yellow
        moveq   #FULL,%d1
        bra.s   8f
7:      btst    %d4,%d6
        beq.s   8f
        moveq   #FULL,%d1               | in the scale: red
8:      move.l  %d1,-(%sp)
        move.l  %d2,-(%sp)
        jsr     SET_LEVEL
        move.l  %d2,(%sp)
        jsr     LED_ON
        addq.l  #1,%d2
        move.l  %d3,4(%sp)
        move.l  %d2,(%sp)
        jsr     SET_LEVEL
        move.l  %d2,(%sp)
        jsr     LED_ON
        addq.l  #8,%sp
        addq.l  #1,%d2
        addq.l  #1,%d4
        cmpi.l  #12,%d4
        bne.s   9f
        moveq   #0,%d4
9:      cmpi.l  #32,%d2
        bne.s   5b
        moveq   #0,%d3
        jmp     LOOP_DONE

| No scale: stock's loop, whole.
kl_stock:
        clr.l   %d5
        clr.l   %d4
        clr.l   %d6
        lea     SET_LEVEL,%a3
        jmp     STOCK_LOOP

| The per-tick routine. ARP SETUP open on a MIDI track: encoder F pushed
| and released with no turn between opens the chooser. CHROMATIC: the
| current answer against the one the keyboard shows; a difference asks the
| dispatcher for the trig LEDs (the pass, then kl_chromatic, records the
| new one). Outside CHROMATIC the record is cleared, so entering it draws
| as stock does, unprompted.
kl_tick:
        tst.l   ARP_WINDOW
        beq.s   4f
        tst.l   MIDI_MODE
        beq.s   4f
        tst.l   PUSH_F
        beq.s   5f
        tst.l   sc_pushed
        bne.s   6f
        moveq   #1,%d0                  | pushed now
        move.l  %d0,sc_pushed
        clr.l   sc_turned
        bra.s   6f
5:      tst.l   sc_pushed
        beq.s   6f
        clr.l   sc_pushed               | released
        tst.l   sc_turned
        bne.s   6f
        tst.l   LIST_OPEN
        bne.s   6f
        tst.l   DIALOG_OPEN
        bne.s   6f
        tst.l   TEXT_OPEN
        bne.s   6f
        mvz.b   UI_TRACK,%d0
        bsr.w   sc_track
        lsr.l   #4,%d0                  | the ID shown first (OFF: none)
        lea     sc_key_chosen,%a0
        bsr.w   sc_pick
        bra.s   6f
4:      clr.l   sc_pushed
6:      moveq   #1,%d0
        cmp.l   TRIG_MODE,%d0
        bne.s   2f
        bsr.w   kl_current
        cmp.l   kl_shown,%d0
        beq.s   3f
        clr.l   -(%sp)
        jsr     LED_PASS
        addq.l  #4,%sp
        bra.s   3f
2:      moveq   #-2,%d0                 | no answer is -2: the next CHROMATIC pass sets it
        move.l  %d0,kl_shown
3:      tst.l   TICK_FLAG               | the displaced instruction; its flags go on
        jmp     TICK_BACK

| The current track's answer, on the side the MIDI key selects.
kl_current:
        mvz.b   CUR_TRACK,%d0
        and.l   #7,%d0
        moveq   #0,%d1                  | audio
        tst.l   MIDI_MODE
        beq.s   kl_source
        moveq   #1,%d1                  | MIDI

| kl_source: d0 = track 0..7, d1 = 0 audio / 1 MIDI -> d0 = mask << 8 |
| key1 << 4 | tonic: mask bit p = pitch class p in the scale, key1 = the
| pitch class trig key 1 sounds, tonic = the scale's (C = 0 .. B = 11); or
| -1 for stock's keyboard. Scratches d0-d1/a0-a1, as a C call.
kl_source:
        tst.l   %d1
        bne.s   kl_midi
        .if     HAVE_SCALE_QUANTIZER
        jsr     SCALE_AT                | the SCALE's pitch classes on ROOT
        tst.l   %d0
        beq.s   kl_none                 | SCALE OFF: stock's keyboard
        mvz.b   NV_ROOT,%d1
        lsl.l   #8,%d0
        or.l    %d1,%d0                 | tonic = ROOT
        lsl.l   #4,%d1
        or.l    %d1,%d0                 | key 1 sounds ROOT
        rts
        .else
        bra.s   kl_none                 | audio: no source
        .endif
kl_midi:
        bsr.w   sc_track
        tst.l   %d0
        bmi.s   kl_none                 | KEY OFF
        moveq   #15,%d1
        and.l   %d0,%d1                 | the tonic
        lsr.l   #4,%d0
        move.l  %d1,-(%sp)
        bsr.w   sc_mask                 | the scale on C
        move.l  (%sp),%d1
        lsl.l   %d1,%d0                 | on the tonic: bits 0..22 ...
        move.l  %d0,%d1
        lsr.l   #8,%d1
        lsr.l   #4,%d1
        or.l    %d1,%d0                 | ... the ones past B back at the bottom
        andi.l  #0xfff,%d0
        lsl.l   #8,%d0
        or.l    (%sp)+,%d0              | key 1 sounds C (key1 = 0)
        rts
kl_none:
        moveq   #-1,%d0
        rts

| ==== tables ===============================================================

        .balign 2
| Each ID's mask, from ID 1: bit d = d semitones above the tonic.
sc_masks:
        .word   0xab5,0x6ad,0x5ab,0xad5,0x6b5,0x5ad,0x56b       | MAJOR
        .word   0xaad,0x6ab,0xb55,0x6d5,0x5b5,0x56d,0x55b       | MELODIC MINOR
        .word   0x9ad,0x66b,0xb35,0x6cd,0x5b3,0xad9,0x35b       | HARMONIC MINOR
        .word   0x9b5,0x66d,0x59b,0xacd,0x6b3,0xb59,0x36b       | HARMONIC MAJOR
        .word   0x9b3,0xcd9,0x39b,0x9cd,0x673,0xb39,0x367       | DOUBLE HARMONIC
        .word   0x295,0x4a5,0x529,0x2a5,0x4a9                   | PENTATONIC
        .word   0x4e9,0x29d                                     | BLUES
        .word   0x18d,0x4a3,0x463,0x28d,0x18b                   | JAPANESE
        .word   0x555,0xb6d,0x6db,0x999,0xfff                   | SYMMETRIC

| Each family's first ID - 1, and one past its last (the next family's).
sc_fam_first:
        .byte   0,7,14,21,28,35,40,42,47,52
| Each ID's family.
sc_families:
        .byte   0,0,0,0,0,0,0, 1,1,1,1,1,1,1, 2,2,2,2,2,2,2, 3,3,3,3,3,3,3
        .byte   4,4,4,4,4,4,4, 5,5,5,5,5, 6,6, 7,7,7,7,7, 8,8,8,8,8

| Each ID's 4-character name, NUL-padded: the KEY field's.
sc_shorts:
        .ascii  "MAJ\0DOR\0PHR\0LYD\0MIX\0MIN\0LOC\0"
        .ascii  "MMINDOb2LYD+LYDDMXb6LC#2ALT\0"
        .ascii  "HMINLC#6IO#5DO#4PHRDLY#2ALT7"
        .ascii  "HMAJDOb5PHb4LYb3MXb2LA#2LCb7"
        .ascii  "DHARL#26UPHRHUNGORNTI#25LC37"
        .ascii  "PMAJEGYPMGNGRITUPMIN"
        .ascii  "BLUSBMAJ"
        .ascii  "HIRAINSNIWATKUMOPELG"
        .ascii  "WHOLDWH\0DHW\0AUG\0CHRM"

sc_tonics:
        .ascii  "C\0C#D\0D#E\0F\0F#G\0G#A\0A#B\0"

        .balign 4
| The chooser's rows: each family, then each ID's name (sc_fam_cb lists a
| family's run of this table).
sc_fam_labels:
        .long   f_maj,f_mel,f_hmin,f_hmaj,f_dbl,f_pent,f_blues,f_jap,f_sym
sc_names:
        .long   n1,n2,n3,n4,n5,n6,n7,n8,n9,n10,n11,n12,n13,n14,n15,n16,n17,n18
        .long   n19,n20,n21,n22,n23,n24,n25,n26,n27,n28,n29,n30,n31,n32,n33,n34
        .long   n35,n36,n37,n38,n39,n40,n41,n42,n43,n44,n45,n46,n47,n48,n49,n50
        .long   n51,n52
sc_fam_cbs:
        .rept   SC_FAMILIES
        .long   sc_fam_cb
        .endr
sc_mode_cbs:
        .rept   DIATONIC                | the largest family
        .long   sc_mode_cb
        .endr

f_maj:  .asciz  "MAJOR"
f_mel:  .asciz  "MELODIC MINOR"
f_hmin: .asciz  "HARMONIC MINOR"
f_hmaj: .asciz  "HARMONIC MAJOR"
f_dbl:  .asciz  "DOUBLE HARMONIC"
f_pent: .asciz  "PENTATONIC"
f_blues: .asciz "BLUES"
f_jap:  .asciz  "JAPANESE"
f_sym:  .asciz  "SYMMETRIC"
n1:     .asciz  "IONIAN (MAJOR)"
n2:     .asciz  "DORIAN"
n3:     .asciz  "PHRYGIAN"
n4:     .asciz  "LYDIAN"
n5:     .asciz  "MIXOLYDIAN"
n6:     .asciz  "AEOLIAN (MINOR)"
n7:     .asciz  "LOCRIAN"
n8:     .asciz  "MELODIC MINOR"
n9:     .asciz  "DORIAN b2"
n10:    .asciz  "LYDIAN AUGMENTED"
n11:    .asciz  "LYDIAN DOMINANT"
n12:    .asciz  "MIXOLYDIAN b6"
n13:    .asciz  "LOCRIAN #2"
n14:    .asciz  "ALTERED"
n15:    .asciz  "HARMONIC MINOR"
n16:    .asciz  "LOCRIAN #6"
n17:    .asciz  "IONIAN #5"
n18:    .asciz  "DORIAN #4"
n19:    .asciz  "PHRYGIAN DOMINANT"
n20:    .asciz  "LYDIAN #2"
n21:    .asciz  "ALTERED bb7"
n22:    .asciz  "HARMONIC MAJOR"
n23:    .asciz  "DORIAN b5"
n24:    .asciz  "PHRYGIAN b4"
n25:    .asciz  "LYDIAN b3"
n26:    .asciz  "MIXOLYDIAN b2"
n27:    .asciz  "LYDIAN AUG #2"
n28:    .asciz  "LOCRIAN bb7"
n29:    .asciz  "DOUBLE HARMONIC"
n30:    .asciz  "LYDIAN #2 #6"
n31:    .asciz  "ULTRAPHRYGIAN"
n32:    .asciz  "HUNGARIAN MINOR"
n33:    .asciz  "ORIENTAL"
n34:    .asciz  "IONIAN #2 #5"
n35:    .asciz  "LOCRIAN bb3 bb7"
n36:    .asciz  "MAJOR PENTATONIC"
n37:    .asciz  "EGYPTIAN"
n38:    .asciz  "MAN GONG"
n39:    .asciz  "RITUSEN"
n40:    .asciz  "MINOR PENTATONIC"
n41:    .asciz  "BLUES"
n42:    .asciz  "MAJOR BLUES"
n43:    .asciz  "HIRAJOSHI"
n44:    .asciz  "IN-SEN"
n45:    .asciz  "IWATO"
n46:    .asciz  "KUMOI"
n47:    .asciz  "PELOG"
n48:    .asciz  "WHOLE TONE"
n49:    .asciz  "DIMINISHED W-H"
n50:    .asciz  "DIMINISHED H-W"
n51:    .asciz  "AUGMENTED"
n52:    .asciz  "CHROMATIC"

        .data
        .balign 4
kl_shown:                               | the answer the keyboard shows, -2 none
        .long   -2
sc_pushed:  .long 0                     | encoder F was pushed at the last tick
sc_turned:  .long 0                     | ... and turned since
sc_client:  .long 0                     | the chooser's client
sc_shown:   .long 0                     | the ID it opened on
sc_famsel:  .long 0                     | the family row chosen
sc_modesel: .long 0                     | the scale row chosen
sc_modebase: .long 0                    | the chosen family's first ID - 1
