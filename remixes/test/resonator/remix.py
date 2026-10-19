"""RESONATOR on FX1 beside the stock effects: PLATE REV gives up its words."""
from remix.schema import Proof, Remix

REMIX = Remix(
    family="effects",
    proof=Proof.RENDER,
    proof_note="render gates only; not on hardware",
    name="resonator",
    doc="RESONATOR on FX1 beside the stock effects (all but PLATE REV).",
    modules=("RESONATOR",
             "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
             "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
             "DELAY", "SPRING REV", "DARK REV"),
    fx1=("RESONATOR",
         "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER", "CHORUS",
         "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI"),
    fallback="NONE",
)
