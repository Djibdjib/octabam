| KEY LEDS -- the CHROMATIC trig keys light the track's scale.
|
| Stock's trig-LED pass (0x40043fdc), in CHROMATIC trig mode (0x460d16f0
| = 1), draws C major whatever the track's KEY: key k, n = k mod 12, n 0 is
| C (red and green, yellow), the white keys red, the black keys dark. This
| draws the scale a SOURCE gives for the current track instead, in the same
| colours: the tonic yellow, the scale's other notes red, the notes outside
| it dark. Key 1 is C, as stock's keyboard is. No scale from the source:
| stock's own loop runs.
|
| The display and the scale are apart. kl_source is the one question the
| display asks (README "Sources"); which modules answer it is decided at
| build time, from the remix (remix.inc):
|
|   MIDI side   MIDI SCALES in the remix: its own ms_raw / ms_decode (the
|               KEY it stores, its modes, its source rules), so nothing of
|               its encoding is copied here. Without it: stock's KEY,
|               1..24 = Major / Minor pairs, tonic (v-1)/2, Minor when v
|               is even, read from the MIDI track's live setup lane
|               0x46c76df1 + 68 * t (the byte ms_raw reads).
|   audio side  SCALE QUANTIZER in the remix: its own SCALE_AT
|               (0x400d2ca8, the pinned `jmp qz_scale_mask`: the SCALE's
|               pitch classes rotated by ROOT, 0 = OFF) and ROOT; with a
|               scale on, its keyboard is transposed so that key 1 sounds
|               ROOT (its README, "key 1 sounds the root"). Without it, or
|               SCALE OFF: stock's keyboard.
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
| (0x4007e998(0)), as stock does after a CHROMATIC key.

        .include "remix.inc"            | HAVE_MIDI_SCALES, HAVE_SCALE_QUANTIZER

        .text
        .globl  kl_chromatic, kl_source, kl_tick
        .balign 2

        .if     HAVE_MIDI_SCALES
        .extern ms_raw                  | MIDI SCALES: d0 track -> its KEY byte
        .extern ms_decode               | MIDI SCALES: d0 KEY -> tonic << 2 | mode << 6, -1 OFF
        .endif

        .equ    SCALE_AT,  0x400d2ca8   | SCALE QUANTIZER: d0 := the ROOT-rotated SCALE mask, 0 OFF; clobbers a0
        .equ    NV_ROOT,   0x100b14ee   | SCALE QUANTIZER: ROOT, 0..11 = C .. B
        .equ    SET_LEVEL, 0x400135b0   | (id, level): the LED's brightness nibble, sent when it changes
        .equ    LED_ON,    0x400131a0   | (id): the LED's bitmap bit set
        .equ    CUR_TRACK, 0x80000000   | byte: the UI's current track
        .equ    MIDI_MODE, 0x80000012   | long: nonzero in MIDI mode
        .equ    KEY_LANE,  0x46c76df1   | + 68 * t: MIDI track t's KEY byte
        .equ    TRIG_MODE, 0x460d16f0   | long: the trig mode, 1 = CHROMATIC
        .equ    LED_PASS,  0x4007e998   | (slot): the LED dispatcher; slot 0 runs the trig-LED pass
        .equ    TICK_BACK, 0x40056abe   | the per-tick routine after its first instruction
        .equ    TICK_FLAG, 0x460d1e4c   | what that instruction tests
        .equ    STOCK_LOOP, 0x400442ee  | stock's loop, after the displaced span
        .equ    LOOP_DONE, 0x400444f4   | stock after the 16th key, d3 = 0
        .equ    STOCK_KEYS, 24          | stock's KEY values: 12 tonics x Major / Minor
        .equ    MINOR,     5            | kl_masks' index of natural Minor
        .equ    FULL,      15

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

| The per-tick check: in CHROMATIC, the current answer against the one the
| keyboard shows; a difference asks the dispatcher for the trig LEDs (the
| pass, then kl_chromatic, records the new one). Outside CHROMATIC the
| record is cleared, so entering it draws as stock does, unprompted.
kl_tick:
        moveq   #1,%d0
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
        .if     HAVE_MIDI_SCALES
        jsr     ms_raw
        jsr     ms_decode
        tst.l   %d0
        bmi.s   kl_none                 | KEY OFF
        move.l  %d0,%d1
        lsr.l   #2,%d1
        and.l   #15,%d1                 | tonic
        lsr.l   #6,%d0                  | mode, kl_masks' order (MIDI SCALES' own)
        .else
        move.l  %d0,%d1
        lsl.l   #6,%d0
        lsl.l   #2,%d1
        add.l   %d1,%d0                 | 68 * t
        lea     KEY_LANE,%a0
        mvz.b   (%a0,%d0.l),%d0
        tst.l   %d0
        beq.s   kl_none                 | KEY OFF
        cmpi.l  #STOCK_KEYS,%d0
        bhi.s   kl_none
        subq.l  #1,%d0                  | (tonic << 1) | Minor
        move.l  %d0,%d1
        lsr.l   #1,%d1                  | tonic
        and.l   #1,%d0
        beq.s   1f                      | Major: mode 0
        moveq   #MINOR,%d0
1:
        .endif
        lea     kl_masks,%a0
        mvz.w   (%a0,%d0.l*2),%d0       | the mode on C
        lsl.l   %d1,%d0                 | on the tonic: bits 0..22 ...
        move.l  %d1,-(%sp)
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

        .balign 2
| MAJ DOR PHR LYD MIX MIN LOC on C: bit d = d semitones above the tonic. The
| seven diatonic modes, in the order MIDI SCALES' ms_decode numbers them.
kl_masks:
        .word   0xab5,0x6ad,0x5ab,0xad5,0x6b5,0x5ad,0x56b

        .data
        .balign 4
kl_shown:                               | the answer the keyboard shows, -2 none
        .long   -2
