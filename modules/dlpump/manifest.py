"""DLPUMP -- sends a staged block to a DSP core's X memory a chunk per frame interrupt.

Called from LOAD METER's entry code (docs/proposals/DEMAND_LOAD.md, decision 9).
"""
from remix.schema import Category, Kind, Linked, Module, Proof

MODULE = Module(
    name="dlpump",
    key="DLPUMP",
    kind=Kind.CF_PATCH,
    category=Category.REFERENCE, author="sambanks", author_url="https://github.com/sambanks",
    proof=Proof.CHECK, proof_note="",
    doc="Host-writes a staged block to a DSP core, a chunk per frame interrupt (demand loader).",
    linked=(Linked("dlpump", "modules/dlpump/pump.s", cpu="5475", dram=True),),
)
