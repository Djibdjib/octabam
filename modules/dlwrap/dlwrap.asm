; ---------------------------------------------------------------------------
; DLWRAP -- keeps a stock reverb off demand-loaded code (modules/dlwrap/README.md).
;
; PLATE REV writes its instance buffer from the base the allocator hands the slot
; (the entry whose address is in x:$213 at init) up to a measured extent. When that range covers the window words
; DLSTUB published as occupied, the reverb must not run there: this wrapper answers
; the dispatcher for the stock id and runs the stock init and proc only while the
; range is clear; otherwise the instance passes the audio through. The decision is
; taken at init and re-checked every frame, so code that arrives later is never
; written over. An instance that went dry stays dry until it is selected again.
;
; This copy fronts PLATE REV on payload A: its entries (P:$1000, P:$1055) and its
; extent (the highest word it writes, $37ff above the base) are the three literals
; below.
;
; Per core (X, private), one word per instance at idx = (r7 >> 8) & $3f:
;   x:$3e00+idx  0 never initialised, 1 running the stock code, 2 dry
;   x:$3e40+idx  the buffer base the instance was given
; Shared (written by DLCOPY: the entry of effect 0, x:$33da3 + 8 k): x:$33da3 BOUND, x:$33da6 / x:$33da7 the span.
; ---------------------------------------------------------------------------

init:
        move    x:>$213,r5               ; the address of this slot's entry in the allocator table
        move    r7,a
        asr     #$8,a,a
        and     #>$3f,a
        move    a1,r2
        move    #>$3e40,x0
        add     x0,a
        move    a1,r3
        move    r2,a
        move    #>$3e00,x0
        add     x0,a
        move    a1,r4
        move    x:(r5),x1                ; the buffer base: the entry's contents
        move    x1,x:(r3)                ; remember it
        bsr     dw_over
        tst     a
        bne     dw_off
        move    #>$1,x0
        move    x0,x:(r4)                ; running
        move    #>$1000,r2               ; the stock init
        jmp     (r2)
dw_off:
        move    #>$2,x0
        move    x0,x:(r4)                ; dry
        rts

proc:
        move    a1,x:>$3ee0              ; proc is called with a = 0 or 1 in a: kept for the stock proc
        move    r7,a
        asr     #$8,a,a
        and     #>$3f,a
        move    a1,r2
        move    #>$3e40,x0
        add     x0,a
        move    a1,r3
        move    r2,a
        move    #>$3e00,x0
        add     x0,a
        move    a1,r4
        move    x:(r4),a
        cmp     #>$1,a
        bne     dw_pass
        move    x:(r3),x1
        bsr     dw_over
        tst     a
        bne     dw_now
        move    x:>$3ee0,a
        move    #>$1055,r2               ; the stock proc
        jmp     (r2)
dw_now:
        move    #>$2,x0
        move    x0,x:(r4)
dw_pass:
        move    r0,r1
        do      n7,>dw_end
        move    x:(r0)+,a
        move    x:(r0)+,b
        move    a,x:(r1)+
        move    b,x:(r1)+
dw_end:
        rts

; a = 1 when the range [x1, x1 + $3800) covers any word of the loaded code, else 0.
dw_over:
        move    x:>$33da3,a
        move    #>$b0a5ed,x0
        cmp     x0,a
        bne     dw_none
        move    x1,a
        move    x:>$33da7,x0
        cmp     x0,a
        bge     dw_none                  ; the range starts at or after the end of the code
        move    #>$3800,x0
        add     x0,a
        move    x:>$33da6,x0
        cmp     x0,a
        ble     dw_none                  ; the range ends at or before the start of the code
        move    #>$1,a
        rts
dw_none:
        clr     a
        rts
