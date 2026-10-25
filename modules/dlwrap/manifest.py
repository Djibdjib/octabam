"""DLWRAP -- keeps a stock reverb off demand-loaded code (spike).

Answers the dispatcher for PLATE REV's buffer: runs the stock code only while its buffer range is clear of the code
DLSTUB published, otherwise passes the audio through. A test instrument, in remixes/test/dlspike only.
"""
from remix.schema import (BusRole, Category, DspSection, Formatter, Gate, Harness, Kind, MenuEntry, Module,
                          Param, Proof, YBase)

_BLANK = Param(b"", 0)

MODULE = Module(
    name="dlwrap",
    key="DLWRAP",
    kind=Kind.DSP_EFFECT,
    category=Category.TRACK, author="sambanks", author_url="https://github.com/sambanks",
    proof=Proof.CHECK, proof_note="",
    doc="Spike: PLATE REV's wrapper, dry where its buffer would cover loaded code.",
    menu=MenuEntry(
        fx2_id=0x1e,
        donor_desc=0x400d58b8,        # DARK REV
        abbr=b"DLWR",
        fullname=b"DL WRAP",
        build_tag=False,
    ),
    params=(
        Param(b"GO", 0, 2, active=True, formatter=Formatter.STEPPED, labels=("OFF", "ON"),
              doc="unused; the wrapper reads no knob"),
        _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK,
    ),
    dsp=DspSection(
        asm="modules/dlwrap/dlwrap.asm",
        priority=20,
        bus_role=BusRole.NONE,        # an insert
        ybase=YBase.NEVER,            # no buffers of its own
        r7_latch_slot=None,
        gate_label=None,
    ),
    harness=Harness(layout_char=None, is_server=False),
)
