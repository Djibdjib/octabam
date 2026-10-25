"""DLSTUB -- the lazy-binding stub for a demand-loaded effect (spike).

An insert on id 0x1b that is dry until the code it fronts is resident, then runs it:
modules/dlstub/README.md. A test instrument, in remixes/test/dlspike only.
"""
from remix.schema import (BusRole, Category, DspSection, Formatter, Gate, Harness, Kind, MenuEntry, Module,
                          Param, Proof, YBase)

_BLANK = Param(b"", 0)

MODULE = Module(
    name="dlstub",
    key="DLSTUB",
    kind=Kind.DSP_EFFECT,
    category=Category.TRACK, author="sambanks", author_url="https://github.com/sambanks",
    proof=Proof.CHECK, proof_note="",
    doc="Spike: dry until the demand-loaded code is resident, then runs it.",
    menu=MenuEntry(
        fx2_id=0x1b,
        donor_desc=0x400d58b8,        # DARK REV
        abbr=b"DLST",
        fullname=b"DL STUB",
        build_tag=False,
    ),
    params=(
        Param(b"GO", 0, 2, active=True, formatter=Formatter.STEPPED, labels=("OFF", "ON"),
              doc="unused; the stub reads no knob"),
        _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK, _BLANK,
    ),
    dsp=DspSection(
        asm="modules/dlstub/dlstub.asm",
        priority=19,
        bus_role=BusRole.NONE,        # an insert
        ybase=YBase.NEVER,            # no buffers
        r7_latch_slot=None,
        gate_label=None,
    ),
    harness=Harness(layout_char=None, is_server=False),
)
