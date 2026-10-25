"""DLCOPY -- the demand loader's copier: a frame hook on payload B that moves a block the ColdFire has
staged into the shared window and publishes it (docs/proposals/DEMAND_LOAD.md).
"""
from remix.schema import Category, DspHook, DspSection, Kind, Module, Proof

MODULE = Module(
    name="dlcopy",
    key="DLCOPY",
    kind=Kind.HYBRID,
    category=Category.REFERENCE, author="sambanks", author_url="https://github.com/sambanks",
    proof=Proof.CHECK, proof_note="",
    doc="Frame hook on payload B: copies a staged block into the shared window (demand loader).",
    dsp=DspSection(
        asm="modules/dlcopy/dlcopy.asm",
        priority=22,
        payloads=frozenset({"B"}),
        hooks=(DspHook({"B": 0x76}, (0x667000, 0x000207), "dlc_start",
                       "frame head, after the host handlers' masks are set: the staged block is copied"),),
    ),
)
