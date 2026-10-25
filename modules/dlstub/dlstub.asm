; ---------------------------------------------------------------------------
; DLSTUB -- the lazy-binding stub in front of one demand-loaded effect
; (modules/dlstub/README.md).
;
; The dispatch tables point this effect's id here. While the real code is not
; resident the stub passes the audio through (the stock null stub's loop). Once
; the ColdFire has loaded the code and the copier has published it, each
; instance runs the real init once, with the proc's registers kept, and from
; then on jumps to the real proc. Every path that selects an effect ends in
; INIT[id] and PROCESS[id], so nothing on the ColdFire side has to guard the
; setters.
;
; Shared words (the window, seen by both cores; below the lowest window code,
; so payload A's boot zero loop clears them):
;   x:$33da0  BOUND    $b0a5ed when the code is resident, anything else if not
;   x:$33da1  the real init   x:$33da2  the real proc
; Per core (X, private): x:$3f00..$3f3f one word per instance, 1 once its init
; has run; x:$3f40..$3f4a the registers kept across the init.
;
; Staging (X, private to the core the ColdFire writes it on), written by the
; ColdFire's host transfer, whose words carry 16 bits each:
;   x:$2900  doorbell, written last: $a55a when the block is complete
;   x:$2901  destination P address   x:$2902  the number of code words N
;   x:$2903  the real init           x:$2904  the real proc
;   x:$2905.. 2 N words: each 24-bit code word as its high 16 bits, then its low 8
; x:$2910 is set to 1 by the dry path: someone is waiting for the code.
; An instance that finds the code absent and a complete block staged copies it into
; the window, publishes BOUND last, clears the doorbell (the ColdFire reads 0 there
; once the block is consumed) and runs the real code in that same call. With no
; block it passes the audio through.
; ---------------------------------------------------------------------------

init:
        move    r7,a
        asr     #$8,a,a
        and     #>$3f,a
        move    #>$3f00,x0
        add     x0,a
        move    a1,r2
        clr     a
        move    a,x:(r2)                 ; this instance has not run the real init
        rts

proc:
        move    x:>$33da0,a
        move    #>$b0a5ed,x0
        cmp     x0,a
        beq     dl_bound
        move    x:>$2900,a
        move    #>$a55a,x0
        cmp     x0,a
        bne     dl_pass
        bsr     dl_copy
dl_bound:
        move    r7,a
        asr     #$8,a,a
        and     #>$3f,a
        move    #>$3f00,x0
        add     x0,a
        move    a1,r2
        move    x:(r2),a
        tst     a
        bne     dl_run
        move    r2,x:>$3f4a
        move    r0,x:>$3f40
        move    n0,x:>$3f41
        move    r6,x:>$3f42
        move    r7,x:>$3f43
        move    n7,x:>$3f44
        move    m0,x:>$3f45
        move    m1,x:>$3f46
        move    x:>$33da1,r2
        jsr     (r2)
        move    x:>$3f40,r0
        move    x:>$3f41,n0
        move    x:>$3f42,r6
        move    x:>$3f43,r7
        move    x:>$3f44,n7
        move    x:>$3f45,m0
        move    x:>$3f46,m1
        move    x:>$3f4a,r2
        move    #>$1,x0
        move    x0,x:(r2)
dl_run:
        move    x:>$33da2,r2
        jmp     (r2)
dl_pass:
        move    #>$1,x0
        move    x0,x:>$2910              ; an instance wants the code
        move    r0,r1
        do      n7,>dl_end
        move    x:(r0)+,a
        move    x:(r0)+,b
        move    a,x:(r1)+
        move    b,x:(r1)+
dl_end:
        rts

dl_copy:
        move    x:>$2901,r1              ; the destination
        move    x:>$2902,x0              ; N
        move    #>$2905,r2
        do      x0,>dl_cpy
        move    x:(r2)+,a
        and     #>$ffff,a
        asl     #$8,a,a
        move    x:(r2)+,b
        and     #>$ff,b
        add     b,a
        move    a1,x0
        move    x0,p:(r1)+
dl_cpy:
        move    x:>$2903,x0
        move    x0,x:>$33da1
        move    x:>$2904,x0
        move    x0,x:>$33da2
        move    #>$b0a5ed,x0
        move    x0,x:>$33da0             ; BOUND, after the code and both entries
        clr     a
        move    a,x:>$2900               ; consumed
        rts
