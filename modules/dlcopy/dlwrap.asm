; ---------------------------------------------------------------------------
; DLWRAP -- keeps the stock buffered reverbs off demand-loaded code
; (docs/proposals/DEMAND_LOAD.md). A template: the build assembles one copy per
; payload (the stock entries differ), with a pair of trampolines per guarded reverb
; where the markers below are, and points the reverbs' ids at them.
;
; The reverb writes its instance buffer from the base the allocator hands the slot
; (the entry whose address is in x:$213 at init) up to a measured extent. When that
; range covers words a loaded effect occupies, the reverb must not run there: the
; wrapper answers the dispatcher for the stock id and runs the stock init and proc
; only while the range is clear of every loaded effect's span; otherwise the instance
; passes the audio through. The decision is taken at init and re-checked every frame,
; so code that arrives later is never written over. An instance that went dry stays
; dry until it is selected again.
;
; A trampoline leaves the reverb's stock entry (its init or its proc on this payload)
; in x:$3fd1 and its extent (one more than the highest word it writes above its base)
; in x:$3fd2, and enters `init` or `proc`.
;
; Per core (X, private), one word per instance at idx = (r7 >> 8) & $3f:
;   x:$3f50+idx  0 never initialised, 1 running the stock code, 2 dry
;   x:$3f90+idx  the buffer base the instance was given
; x:$3fd0 the proc's entry a   x:$3fd1 the stock entry   x:$3fd2 the extent
; Shared (DLCOPY writes the entry of each loaded effect, x:$33da3 + 8 k): +0 BOUND,
; +3 and +4 the span [first word, word after the last).
; ---------------------------------------------------------------------------

; TRAMPOLINES_I
init:
        move    x:>$213,r5               ; the address of this slot's entry in the allocator table
        move    r7,a
        asr     #$8,a,a
        and     #>$3f,a
        move    a1,r2
        move    #>$3f90,x0
        add     x0,a
        move    a1,r3
        move    r2,a
        move    #>$3f50,x0
        add     x0,a
        move    a1,r4
        move    x:(r5),x1                ; the buffer base: the entry's contents
        move    x1,x:(r3)                ; remember it
        bsr     dw_over
        tst     a
        bne     dw_off
        move    #>$1,x0
        move    x0,x:(r4)                ; running
        move    x:>$3fd1,r2
        jmp     (r2)
dw_off:
        move    #>$2,x0
        move    x0,x:(r4)                ; dry
        rts

; TRAMPOLINES_P
proc:
        move    a1,x:>$3fd0              ; proc is called with a = 0 or 1 in a: kept for the stock proc
        move    r7,a
        asr     #$8,a,a
        and     #>$3f,a
        move    a1,r2
        move    #>$3f90,x0
        add     x0,a
        move    a1,r3
        move    r2,a
        move    #>$3f50,x0
        add     x0,a
        move    a1,r4
        move    x:(r4),a
        cmp     #>$1,a
        bne     dw_pass
        move    x:(r3),x1
        bsr     dw_over
        tst     a
        bne     dw_now
        move    x:>$3fd0,a
        move    x:>$3fd1,r2
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

; a = 1 when the range [x1, x1 + extent) covers any word of any loaded effect's code, else 0.
dw_over:
        clr     b
        move    #>$33da3,r5
        do      #4,>dw_next
        move    x:(r5),a
        move    #>$b0a5ed,x0
        cmp     x0,a
        bne     dw_skip
        move    x1,a
        move    x:(r5+4),x0
        cmp     x0,a
        bge     dw_skip                  ; the range starts at or after the end of the code
        move    x:>$3fd2,x0
        add     x0,a
        move    x:(r5+3),x0
        cmp     x0,a
        ble     dw_skip                  ; the range ends at or before the start of the code
        move    #>$1,b
dw_skip:
        lua     (r5+8),r5
dw_next:
        move    b,a
        rts
