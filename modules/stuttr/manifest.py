"""STUTTR -- buffer freeze / slice repeater / dropout glitch.

A per-track insert using the stock FX instance buffer as a short ring.
SIZE is (kn+1)^2 words, DECY step is kn^2 (0=hold). RATE clocks re-grabs,
JITR nudges each grab's start, MODE selects LOOP / REV / DROP / SCRAM.
MIX 0 is bit-exact dry.
"""

from remix.schema import (BusRole, Category, Claims, DspSection, Formatter, Gate,
                          Harness, Kind, MenuEntry, Module, Param, Proof, YBase)

_P = Formatter.PLAIN
_S = Formatter.STEPPED
_BLANK = Param(b"", 0)

MODULE = Module(
    name="stuttr",
    key="STUTTR",
    kind=Kind.DSP_EFFECT,
    category=Category.TRACK, author="ilia-murzinov",
    author_url="https://github.com/ilia-murzinov",
    proof=Proof.HARDWARE,
    proof_note="Ilia's MKII, remix glitch BUILD G4 (OCTABAMG4 / GLITCH G4.RMX), "
               "19 Oct 2026: every page-1/page-2 knob exercised; verify_stuttr",
    doc="Buffer glitch: freeze, slice-repeat, reverse, dropout, scramble.",
    menu=MenuEntry(
        # MULTIBCOMP 0x19 — stock null stub, FX2-only; page clone still from
        # DARK REV. Leaves free-pool ids alone.
        fx2_id=0x19,
        replaces="MULTIBCOMP",
        donor_desc=0x400d58b8,
        abbr=b"STUT",
        fullname=b"Stuttr",
        build_tag=False,
    ),
    params=(
        Param(b"SIZE", 40, active=True, formatter=_P,
              doc="slice length ((kn+1)^2 words; FX2 ~0.1..180 ms)"),
        Param(b"RATE", 40, active=True, formatter=_P,
              doc="re-grab speed (slow left, fast right); keep below SIZE"),
        Param(b"JITR", 0, active=True, formatter=_P,
              doc="0 = exact grab; higher = random start further behind write"),
        Param(b"FDBK", 0, active=True, formatter=_P,
              doc="recirculate slice into the write head"),
        Param(b"DECY", 0, active=True, formatter=_P,
              doc="fade into dry; 0 = hold, higher = faster (step = kn^2)"),
        Param(b"MIX", 127, active=True, formatter=_P,
              doc="dry/wet; after DECY the dry path returns (track never mutes)"),
        Param(b"MODE", 0, 4, active=True, formatter=_S,
              labels=("LOOP", "REV", "DROP", "SCRAM"),
              doc="forward loop, reverse, gated holes, scramble read"),
        Param(b"SYNC", 0, 4, active=True, formatter=_S,
              labels=("FREE", "16", "8", "4"),
              doc="divisions of the grab clock"),
        _BLANK, _BLANK, _BLANK, _BLANK,
    ),
    mode_slot=6,
    dsp=DspSection(
        asm="modules/stuttr/stuttr.asm",
        priority=19,
        bus_role=BusRole.NONE,
        ybase=YBase.NEVER,
        r7_latch_slot=None,
        gate_label=None,
    ),
    # 15,862 words: under the FX2 rule (+$3DFD, #785) so SIDECHAIN_COMPRESSOR's
    # shared-window keybus stays out of the instance ring.
    claims=Claims(stock_instance_buffer=True, buffer_words=15862),
    harness=Harness(layout_char="M", is_server=False),
    gates=(Gate("tools/verify/verify_stuttr.py", remix_arg=False),),
    dear={"SIZE": 48, "RATE": 36, "JITR": 0, "FDBK": 0, "DECY": 0,
          "MIX": 127, "MODE": 0, "SYNC": 0},
)
