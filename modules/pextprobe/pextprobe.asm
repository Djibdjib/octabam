; ---------------------------------------------------------------------------
; PEXT PROBE -- how far does P memory reach above P:0x2000 on this core?
; (modules/pextprobe/README.md: what it proves, how to run it, how to read it.)
;
; Insert contract: frames in place at x:(r0) / x:(r0+n0), knobs from r6,
; state in this instance's r7 block. No bus, no buffers.
;
; The ladder is seven rungs at P:0x3fe0, 0x5fe0 ... 0xffe0: the top 32 words
; of each 8 K block above the first. Each is congruent to the base P:0x1fe0
; modulo 0x2000, and P:0x1fe0 .. 0x1fff is unused on both payloads (payload A's
; top is 0x1fdf, B's 0x1d9f), so a rung that wraps onto a power-of-two memory
; lands on spare words, not on code.
;
; A rung:  write SENTINEL to the base; write PATTERN to the rung address;
;          read the base: PATTERN there -> the rung wrapped onto it (ALIAS);
;          else read the rung: PATTERN there, and the base still SENTINEL
;          -> its own memory (REAL); anything else -> ABSENT.
;          A rung that freezes the core leaves its index in the last frame.
; Code per rung: 1 REAL, 2 ALIAS, 3 ABSENT, in two bits of a mask.
;
; ---- what each frame carries (read by modules/pextprobe/decode.py) -----------
; Thirty-two bits, one per sample slot: L sample j = bit j, R sample j = bit
; 16 + j; a one is +0.5 (0x400000), a zero -0.5 (0xc00000). Only the sign is
; read, so any gain on the track leaves it intact.
;   L bits 0..13   the mask: rung m's code in bits 2m, 2m+1
;   L bits 14..15  the rung index k, low two bits   (k = 7: ladder finished)
;   R bit 0        k, bit 2
;   R bit 1        GO was seen (the knob)
;   R bit 2        parity of the frame counter
;   R bits 8..15   0xa5, the frame marker
; ---- r7 slots ---------------------------------------------------------------
;   $10 k, the next rung   $11 frames until it runs   $12 the mask
;   $13 the frame counter  $14 GO   $15 the L word   $16 the R word
; ---------------------------------------------------------------------------

init:
        clr     a
        move    a,x:(r7+$10)
        move    a,x:(r7+$12)
        move    a,x:(r7+$13)
        move    a,x:(r7+$14)
        move    #>64,x0
        move    x0,x:(r7+$11)            ; 64 frames of idle signature before the first rung
        rts

proc:
        move    #$1,n0
        move    x:(r7+$13),a
        add     #>$1,a
        move    a1,x:(r7+$13)
        move    x:(r6+$0),a              ; GO, slot 0: the value in bits 22..16
        and     #>$7f0000,a
        asr     #$10,a,a
        move    a1,x:(r7+$14)
        tst     a
        beq     px_pub                   ; idle until GO
        move    x:(r7+$10),a
        cmp     #>$7,a
        bge     px_pub                   ; finished
        move    x:(r7+$11),a
        sub     #>$1,a
        move    a1,x:(r7+$11)
        bne     px_pub
        move    #>64,x0
        move    x0,x:(r7+$11)            ; 64 frames between rungs
        move    x:(r7+$10),a
        tst     a
        beq     pxr0
        cmp     #>$1,a
        beq     pxr1
        cmp     #>$2,a
        beq     pxr2
        cmp     #>$3,a
        beq     pxr3
        cmp     #>$4,a
        beq     pxr4
        cmp     #>$5,a
        beq     pxr5
        cmp     #>$6,a
        beq     pxr6
        bra     px_pub

; ---- rung 0: P:0x3fe0 --------------------------------------------------------
pxr0:
        move    #>$5a5a5a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)
        move    #>$123456,x0
        move    #>$3fe0,r1
        move    x0,p:(r1)
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a                     ; A2-clean before the compare
        cmp     x0,a
        beq     pxa0
        move    #>$3fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        cmp     x0,a
        bne     pxb0
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        move    #>$5a5a5a,x0
        cmp     x0,a
        bne     pxb0
        move    #>$1,x0
        bra     pxd0
pxa0:
        move    #>$2,x0
        bra     pxd0
pxb0:
        move    #>$3,x0
pxd0:
        move    x:(r7+$12),a
        or      x0,a
        move    a1,x:(r7+$12)
        clr     a
        move    a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)               ; the base back to zero
        move    x:(r7+$10),a
        add     #>$1,a
        move    a1,x:(r7+$10)
        bra     px_pub

; ---- rung 1: P:0x5fe0 --------------------------------------------------------
pxr1:
        move    #>$5a5a5a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)
        move    #>$123456,x0
        move    #>$5fe0,r1
        move    x0,p:(r1)
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a                     ; A2-clean before the compare
        cmp     x0,a
        beq     pxa1
        move    #>$5fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        cmp     x0,a
        bne     pxb1
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        move    #>$5a5a5a,x0
        cmp     x0,a
        bne     pxb1
        move    #>$4,x0
        bra     pxd1
pxa1:
        move    #>$8,x0
        bra     pxd1
pxb1:
        move    #>$c,x0
pxd1:
        move    x:(r7+$12),a
        or      x0,a
        move    a1,x:(r7+$12)
        clr     a
        move    a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)               ; the base back to zero
        move    x:(r7+$10),a
        add     #>$1,a
        move    a1,x:(r7+$10)
        bra     px_pub

; ---- rung 2: P:0x7fe0 --------------------------------------------------------
pxr2:
        move    #>$5a5a5a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)
        move    #>$123456,x0
        move    #>$7fe0,r1
        move    x0,p:(r1)
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a                     ; A2-clean before the compare
        cmp     x0,a
        beq     pxa2
        move    #>$7fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        cmp     x0,a
        bne     pxb2
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        move    #>$5a5a5a,x0
        cmp     x0,a
        bne     pxb2
        move    #>$10,x0
        bra     pxd2
pxa2:
        move    #>$20,x0
        bra     pxd2
pxb2:
        move    #>$30,x0
pxd2:
        move    x:(r7+$12),a
        or      x0,a
        move    a1,x:(r7+$12)
        clr     a
        move    a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)               ; the base back to zero
        move    x:(r7+$10),a
        add     #>$1,a
        move    a1,x:(r7+$10)
        bra     px_pub

; ---- rung 3: P:0x9fe0 --------------------------------------------------------
pxr3:
        move    #>$5a5a5a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)
        move    #>$123456,x0
        move    #>$9fe0,r1
        move    x0,p:(r1)
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a                     ; A2-clean before the compare
        cmp     x0,a
        beq     pxa3
        move    #>$9fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        cmp     x0,a
        bne     pxb3
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        move    #>$5a5a5a,x0
        cmp     x0,a
        bne     pxb3
        move    #>$40,x0
        bra     pxd3
pxa3:
        move    #>$80,x0
        bra     pxd3
pxb3:
        move    #>$c0,x0
pxd3:
        move    x:(r7+$12),a
        or      x0,a
        move    a1,x:(r7+$12)
        clr     a
        move    a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)               ; the base back to zero
        move    x:(r7+$10),a
        add     #>$1,a
        move    a1,x:(r7+$10)
        bra     px_pub

; ---- rung 4: P:0xbfe0 --------------------------------------------------------
pxr4:
        move    #>$5a5a5a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)
        move    #>$123456,x0
        move    #>$bfe0,r1
        move    x0,p:(r1)
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a                     ; A2-clean before the compare
        cmp     x0,a
        beq     pxa4
        move    #>$bfe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        cmp     x0,a
        bne     pxb4
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        move    #>$5a5a5a,x0
        cmp     x0,a
        bne     pxb4
        move    #>$100,x0
        bra     pxd4
pxa4:
        move    #>$200,x0
        bra     pxd4
pxb4:
        move    #>$300,x0
pxd4:
        move    x:(r7+$12),a
        or      x0,a
        move    a1,x:(r7+$12)
        clr     a
        move    a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)               ; the base back to zero
        move    x:(r7+$10),a
        add     #>$1,a
        move    a1,x:(r7+$10)
        bra     px_pub

; ---- rung 5: P:0xdfe0 --------------------------------------------------------
pxr5:
        move    #>$5a5a5a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)
        move    #>$123456,x0
        move    #>$dfe0,r1
        move    x0,p:(r1)
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a                     ; A2-clean before the compare
        cmp     x0,a
        beq     pxa5
        move    #>$dfe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        cmp     x0,a
        bne     pxb5
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        move    #>$5a5a5a,x0
        cmp     x0,a
        bne     pxb5
        move    #>$400,x0
        bra     pxd5
pxa5:
        move    #>$800,x0
        bra     pxd5
pxb5:
        move    #>$c00,x0
pxd5:
        move    x:(r7+$12),a
        or      x0,a
        move    a1,x:(r7+$12)
        clr     a
        move    a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)               ; the base back to zero
        move    x:(r7+$10),a
        add     #>$1,a
        move    a1,x:(r7+$10)
        bra     px_pub

; ---- rung 6: P:0xffe0 --------------------------------------------------------
pxr6:
        move    #>$5a5a5a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)
        move    #>$123456,x0
        move    #>$ffe0,r1
        move    x0,p:(r1)
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a                     ; A2-clean before the compare
        cmp     x0,a
        beq     pxa6
        move    #>$ffe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        cmp     x0,a
        bne     pxb6
        move    #>$1fe0,r5
        move    p:(r5),a
        move    a1,x1
        move    x1,a
        move    #>$5a5a5a,x0
        cmp     x0,a
        bne     pxb6
        move    #>$1000,x0
        bra     pxd6
pxa6:
        move    #>$2000,x0
        bra     pxd6
pxb6:
        move    #>$3000,x0
pxd6:
        move    x:(r7+$12),a
        or      x0,a
        move    a1,x:(r7+$12)
        clr     a
        move    a,x0
        move    #>$1fe0,r1
        move    x0,p:(r1)               ; the base back to zero
        move    x:(r7+$10),a
        add     #>$1,a
        move    a1,x:(r7+$10)
        bra     px_pub

; ---- publish: the 32 bits into the frame --------------------------------------
px_pub:
; L word = mask + (k & 3) << 14
        move    x:(r7+$10),a
        and     #>$3,a
        asl     #$e,a,a
        move    x:(r7+$12),x0
        add     x0,a
        move    a1,x:(r7+$15)
; R word = k >> 2 + GO << 1 + parity << 2 + 0xa500
        move    x:(r7+$10),a
        asr     #$2,a,a
        move    x:(r7+$14),b
        and     #>$1,b
        asl     #$1,b,b
        add     b,a
        move    x:(r7+$13),b
        and     #>$1,b
        asl     #$2,b,b
        add     b,a
        add     #>$a500,a
        move    a1,x:(r7+$16)
        do      n7,>pxl                  ; 16 on the unit
        move    x:(r7+$15),a
        and     #>$1,a
        move    #>$c00000,b
        move    #>$400000,x1
        tne     x1,b
        move    b,x:(r0)
        move    x:(r7+$16),a
        and     #>$1,a
        move    #>$c00000,b
        tne     x1,b
        move    b,x:(r0+n0)
        move    x:(r7+$15),a
        asr     #$1,a,a
        move    a1,x:(r7+$15)
        move    x:(r7+$16),a
        asr     #$1,a,a
        move    a1,x:(r7+$16)
        move    (r0)+n0
        move    (r0)+n0
pxl:
        rts
