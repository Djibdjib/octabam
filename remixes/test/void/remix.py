"""VOID replaces COMB FILTER; PLATE REV words host its DSP."""
from remix.schema import Proof, Remix

REMIX = Remix(
    family="effects",
    proof=Proof.HARDWARE,
    proof_note="MKII VOID V7 (handoff y0 mpy) + VOID V8 tip asm 471c7d5b; verify_void.py",
    name="void",
    doc="VOID replaces COMB FILTER; PLATE REV words host its DSP.",
    modules=("VOID",
             "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
             "CHORUS", "SPATIALIZER", "COMPRESSOR", "LO-FI",
             "DELAY", "SPRING REV", "DARK REV"),
    fallback="NONE",
)
