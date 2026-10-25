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
| Under the port a transfer started at the entry of a frame whose ping word
| (0x800000e0, flipped once per frame) is 1 is lost, and one started at ping 0
| arrives whole (tools/verify/verify_dlpump.py, a chunk of 100 words on each
| frame of both phases, core B). The pump therefore sends on ping-0 frames only.
| Whether the unit loses the same frames is open.
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
        .equ    LIVE,   0x80000ec4              | the live FX1 and FX2 ids of tracks 1-8
        .equ    STAGE1, 0x2901                  | the first word of a staged message
        .equ    RING,   0xa55a
        .equ    PING,   0                       | the frames whose host writes the port delivers (below)

        .data
        .include "remix.inc"

        .text
        .globl  dl_pump
dl_pump:
        move.l  dl_state,%d0
        beq.w   idle
        moveq   #PING,%d1
        cmp.l   0x800000e0,%d1                  | the frame's ping word
        bne.w   9f
        move.l  dl_core,%d4
        subq.l  #1,%d0
        bne.w   2f
        move.l  dl_left,%d2                     | state 1: the next chunk
        cmp.l   #CHUNK,%d2
        bls.w   1f
        moveq   #CHUNK,%d2
1:      move.l  dl_dest,%d1
        move.l  dl_src,%a0
        move.l  %d2,%d5
        bsr.w   dl_xfer
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
        bne.w   8f
        moveq   #2,%d0
        move.l  %d0,dl_state
        bra.w   8f
2:      move.l  #BELL,%d1                       | state 2: the doorbell
        lea     dl_bell,%a0
        moveq   #1,%d2
        bsr.w   dl_xfer
        clr.l   dl_state
8:      moveq   #0,%d0
        move.b  %d0,CSEL                        | the frame code expects core A selected
9:      rts

| Idle: compare the effects the tracks use with the ones loaded, on the frames the port delivers.
| One message is armed per call: a load (the effect is used, not loaded, and its block is not
| under a stock reverb) or a withdrawal (loaded, used by no track).
idle:
        moveq   #PING,%d1
        cmp.l   0x800000e0,%d1
        bne.w   9b
        lea     dl_tab,%a2
        moveq   #0,%d6                          | the effect's index
3:      cmp.l   #DL_N,%d6
        bcc.w   9b
        move.l  %a2@,%d2                        | its id
        moveq   #0,%d3                          | used by a track
        lea     LIVE,%a1                        | FX1 ids of tracks 1-8, then FX2's
        moveq   #15,%d4
4:      cmp.b   %a1@+,%d2
        bne.w   5f
        moveq   #1,%d3
5:      subq.l  #1,%d4
        bpl.w   4b
        move.l  dl_loaded,%d0
        btst    %d6,%d0
        bne.w   6f
        tst.l   %d3                             | not loaded
        beq.w   7f
        move.l  %a2@(4),%d1                     | the track whose FX2 slot shares the block
        lea     LIVE+8,%a1
        move.b  %a1@(0,%d1:l),%d1
        cmp.b   #DL_PLATE,%d1
        beq.w   7f
        cmp.b   #DL_SPRING,%d1
        beq.w   7f
        cmp.b   #DL_DARK,%d1
        beq.w   7f
        move.l  %a2@(8),%d1                     | the staged block
        move.l  %a2@(12),%d2
        bset    %d6,%d0
        bra.w   arm
6:      tst.l   %d3                             | loaded
        bne.w   7f
        move.l  %a2@(16),%d1                    | the withdraw message
        moveq   #5,%d2
        bclr    %d6,%d0
        bra.w   arm
7:      lea     %a2@(20),%a2
        addq.l  #1,%d6
        bra.w   3b
arm:    move.l  %d0,dl_loaded
        move.l  %d1,dl_src
        move.l  %d2,dl_left
        moveq   #1,%d0
        move.l  %d0,dl_core
        move.l  #STAGE1,%d0
        move.l  %d0,dl_dest
        moveq   #1,%d0
        move.l  %d0,dl_state
        rts

| ---- the choosers: refuse an effect that cannot be loaded ------------------
| Detours at the FX1 and FX2 select handlers' "same effect?" test (0x4005272a, 0x400524ba): d1 is
| the id chosen, d0 the track's current id, d7 the track. A chosen effect that is loaded, or whose
| block is not under a stock reverb, goes on; anything else leaves the handler as if nothing changed.
        .globl  dl_sel_fx1, dl_sel_fx2
dl_sel_fx1:
        cmp.l   %d0,%d1                         | displaced: cmpl %d0,%d1 / beqw (unchanged)
        beq.w   1f
        moveq   #0,%d0
        bsr.w   dl_veto
        beq.w   1f
        jmp     0x40052730                      | moveb %d1,%a0@: the Part takes the id
1:      jmp     0x4005293a                      | the handler's exit

dl_sel_fx2:
        cmp.l   %d0,%d1
        beq.w   1f
        moveq   #1,%d0
        bsr.w   dl_veto
        beq.w   1f
        jmp     0x400524c0
1:      jmp     0x400526da

| d0 = 1 for the FX2 chooser, 0 for FX1's; d1, d7 as above. Returns Z set to refuse. Every
| register but d0 is kept.
dl_veto:
        lea     %sp@(-40),%sp
        movem.l %d1-%d7/%a0-%a2,%sp@
        move.l  %d0,%d5
        moveq   #1,%d0
        lea     dl_tab,%a2
        moveq   #0,%d6
2:      cmp.l   #DL_N,%d6
        bcc.w   9f
        cmp.l   %a2@,%d1
        bne.w   7f
        move.l  dl_loaded,%d2
        btst    %d6,%d2
        bne.w   9f                              | loaded
        move.l  %a2@(4),%d2                     | the track whose FX2 slot shares the block
        tst.l   %d5
        beq.w   3f
        cmp.l   %d7,%d2
        beq.w   9f                              | the FX2 chooser on that track replaces what is there
3:      lea     LIVE+8,%a0
        move.b  %a0@(0,%d2:l),%d2
        cmp.b   #DL_PLATE,%d2
        beq.w   8f
        cmp.b   #DL_SPRING,%d2
        beq.w   8f
        cmp.b   #DL_DARK,%d2
        beq.w   8f
        bra.w   9f
8:      moveq   #0,%d0
        bra.w   9f
7:      lea     %a2@(20),%a2
        addq.l  #1,%d6
        bra.w   2b
9:      movem.l %sp@,%d1-%d7/%a0-%a2
        lea     %sp@(40),%sp
        tst.l   %d0
        rts

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
        beq.w   3b
        moveq   #0,%d1
        move.w  (%a0)+,%d1
        moveq   #0,%d0
        move.w  %d0,HOST+0x14
        move.l  %d1,%d0
        asr.l   #8,%d0
        move.w  %d0,HOST+0x18
        move.w  %d1,HOST+0x1c
        subq.l  #1,%d3
        bne.w   3b
        rts

        .data
        .globl  dl_state, dl_core, dl_dest, dl_src, dl_left, dl_loaded
dl_state: .long 0
dl_core:  .long 0
dl_dest:  .long 0
dl_src:   .long 0
dl_left:  .long 0
dl_loaded: .long 0                      | bit k: effect k is loaded
dl_bell:  .word RING
