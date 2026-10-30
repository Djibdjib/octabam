| KEY LEDS -- the CHROMATIC trig keys light the MIDI track's KEY.
|
| Stock's trig-LED pass (0x40043fdc), in CHROMATIC trig mode (0x460d16f0
| = 1), draws C major whatever the track's KEY: key k, n = k mod 12, n 0 is
| C (red and green, yellow), the white keys red, the black keys dark. On a
| MIDI track whose ARP SETUP KEY is set, this draws that KEY instead, in
| the same colours: the tonic yellow, the scale's other notes red, the
| notes outside it dark. Key 1 is C, as stock's keyboard is. KEY OFF, an
| audio track, or a KEY value past 84: stock's own loop runs.
|
| The KEY byte is the MIDI track's live setup lane, 0x46c76df1 + 68 * t
| (the byte MIDI SCALES' ms_raw reads). Values 1..24 are stock's Major /
| Minor pairs (tonic (v-1)/2, Minor when v is even); 25..84 are MIDI
| SCALES' five added modes, five per tonic (Dorian, Phrygian, Lydian,
| Mixolydian, Locrian). Without MIDI SCALES stock clamps KEY to 24, so
| only 1..24 arrive. The encoding and the seven masks are radiohagen's
| (modules/midi-scales/upstream, scales.s: ms_decode_table, ms_masks; MIT).
|
| Detour at 0x400442e2, the CHROMATIC branch's first instructions
| (`clrl %d5; clrl %d4; clrl %d6; lea SET_LEVEL,%a3`). The pass saved
| d2-d6/a2-a5 at its entry, so the loop keeps its state there; the LED
| routines are C calls (d0-d1/a0-a1 scratch). After the 16th key, stock
| goes to 0x400444f4 with d3 = 0, which is where this one ends.

        .text
        .globl  kl_chromatic
        .balign 2

        .equ    SET_LEVEL, 0x400135b0   | (id, level): the LED's brightness nibble, sent when it changes
        .equ    LED_ON,    0x400131a0   | (id): the LED's bitmap bit set
        .equ    CUR_TRACK, 0x80000000   | byte: the UI's current track
        .equ    MIDI_MODE, 0x80000012   | long: nonzero in MIDI mode
        .equ    KEY_LANE,  0x46c76df1   | + 68 * t: MIDI track t's KEY byte
        .equ    STOCK_LOOP, 0x400442ee  | stock's loop, after the displaced span
        .equ    LOOP_DONE, 0x400444f4   | stock after the 16th key, d3 = 0
        .equ    KEY_MAX,   84
        .equ    FULL,      15

| d2 = LED id (2 * key), d4 = n (key mod 12), d5 = tonic, d6 = the mode's
| mask (bit d = degree d is in the scale).
kl_chromatic:
        tst.l   MIDI_MODE
        beq.w   kl_stock
        mvz.b   CUR_TRACK,%d0
        and.l   #7,%d0
        move.l  %d0,%d1
        lsl.l   #6,%d0
        lsl.l   #2,%d1
        add.l   %d1,%d0                 | 68 * t
        lea     KEY_LANE,%a0
        mvz.b   (%a0,%d0.l),%d0
        tst.l   %d0
        beq.w   kl_stock                | KEY OFF
        cmpi.l  #KEY_MAX,%d0
        bhi.w   kl_stock
        lea     kl_masks,%a0
        cmpi.l  #24,%d0
        bhi.s   1f
        subq.l  #1,%d0                  | 1..24: (tonic << 1) | Minor
        move.l  %d0,%d5
        lsr.l   #1,%d5
        moveq   #0,%d1                  | Major
        btst    #0,%d0
        beq.s   2f
        moveq   #5,%d1                  | Minor
        bra.s   2f
1:      subi.l  #25,%d0                 | 25..84: tonic * 5 + mode
        moveq   #0,%d5
3:      cmpi.l  #5,%d0
        blt.s   4f
        subq.l  #5,%d0
        addq.l  #1,%d5
        bra.s   3b
4:      lea     kl_added,%a1
        mvz.b   (%a1,%d0.l),%d1
2:      mvz.w   (%a0,%d1.l*2),%d6
        moveq   #0,%d2
        moveq   #0,%d4
| one key: red and green levels, then the bits on, as stock's loop does
5:      move.l  %d4,%d0
        sub.l   %d5,%d0
        bpl.s   6f
        addi.l  #12,%d0                 | the degree above the tonic
6:      moveq   #0,%d3                  | green
        moveq   #0,%d1                  | red
        tst.l   %d0
        bne.s   7f
        moveq   #FULL,%d3               | the tonic: yellow
        moveq   #FULL,%d1
        bra.s   8f
7:      btst    %d0,%d6
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

| KEY OFF, an audio track, or an out-of-range KEY: stock's loop, whole.
kl_stock:
        clr.l   %d5
        clr.l   %d4
        clr.l   %d6
        lea     SET_LEVEL,%a3
        jmp     STOCK_LOOP

        .balign 2
| MAJ DOR PHR LYD MIX MIN LOC: bit d = d semitones above the tonic
kl_masks:
        .word   0xab5,0x6ad,0x5ab,0xad5,0x6b5,0x5ad,0x56b
| 25..84's five modes, in MIDI SCALES' order: DOR PHR LYD MIX LOC
kl_added:
        .byte   1,2,3,4,6
        .balign 2
