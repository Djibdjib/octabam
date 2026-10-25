| DLPUMP -- sends a staged block to a DSP core's X memory, CHUNK words per
| frame interrupt, then the doorbell word one frame later.
|
| dl_pump is called from LOAD METER's lm_in (the frame interrupt's entry, after
| its prologue and entry stamp), where every register is saved and the
| stock frame chain has not started. The transfer is the stock host write
| (FUN_40001b18): destination word, count-1, then three register writes per word;
| only the low 16 bits of each word arrive, so the block is halfwords (the
| DSP copier reassembles the 24-bit code words). The chip-select goes back to
| core A on exit: the frame interrupt sends 0x8c to whichever core is selected.
|
| State, set by whoever arms the pump (dl_state last):
|   dl_core  0 = core A, 1 = core B
|   dl_dest  X word address of the first halfword (0x0000..0x3fff)
|   dl_src   address of the first halfword (.word)
|   dl_left  halfwords to send
|   dl_state 0 idle, 1 sending, 2 doorbell due (set by the pump)

        .equ    HOST,   0x20000000
        .equ    CSEL,   0xfc0a400c
        .equ    CHUNK,  100
        .equ    BELL,   0x2900                  | X staging word the DSP polls
        .equ    RING,   0xa55a

        .text
        .globl  dl_pump
dl_pump:
        move.l  dl_state,%d0
        beq.s   9f
        move.l  dl_core,%d4
        subq.l  #1,%d0
        bne.s   2f
        move.l  dl_left,%d2                     | state 1: the next chunk
        cmp.l   #CHUNK,%d2
        bls.s   1f
        moveq   #CHUNK,%d2
1:      move.l  dl_dest,%d1
        move.l  dl_src,%a0
        move.l  %d2,%d5
        bsr.s   dl_xfer
        lea     dl_dest,%a1
        add.l   %d5,%a1@                        | dest += n
        lea     dl_src,%a1
        add.l   %d5,%d5
        add.l   %d5,%a1@                        | src += 2n
        lea     dl_left,%a1
        move.l  %a1@,%d0
        asr.l   #1,%d5
        sub.l   %d5,%d0
        move.l  %d0,%a1@
        bne.s   8f
        moveq   #2,%d0
        move.l  %d0,dl_state
        bra.s   8f
2:      move.l  #BELL,%d1                       | state 2: the doorbell
        lea     dl_bell,%a0
        moveq   #1,%d2
        bsr.s   dl_xfer
        clr.l   dl_state
8:      moveq   #0,%d0
        move.b  %d0,CSEL                        | the frame code expects core A selected
9:      rts

| d4 core, d1 X word, d2 words, a0 source halfwords
dl_xfer:
        move.b  %d4,CSEL
        moveq   #0x7f,%d0
        addq.l  #2,%d0
        move.w  %d0,HOST
        or.l    #0x4000,%d1
        move.w  %d1,HOST+0x1c
        subq.l  #1,%d2
        move.w  %d2,HOST+0x1c
        addq.l  #1,%d2
        move.l  #0x88,%d0
        move.w  %d0,HOST+4
        move.l  %d2,%d3
3:      move.w  HOST+8,%d0
        and.l   #6,%d0
        beq.s   3b
        moveq   #0,%d1
        move.w  (%a0)+,%d1
        moveq   #0,%d0
        move.w  %d0,HOST+0x14
        move.l  %d1,%d0
        asr.l   #8,%d0
        move.w  %d0,HOST+0x18
        move.w  %d1,HOST+0x1c
        subq.l  #1,%d3
        bne.s   3b
        rts

        .data
        .globl  dl_state, dl_core, dl_dest, dl_src, dl_left
dl_state: .long 0
dl_core:  .long 0
dl_dest:  .long 0
dl_src:   .long 0
dl_left:  .long 0
dl_bell:  .word RING
