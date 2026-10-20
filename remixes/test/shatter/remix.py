"""SHATTER beside stock FX (PLATE REV harvested for its words)."""

from remix.schema import Proof, Remix

REMIX = Remix(
    name="shatter",
    family="effects",
    proof=Proof.RENDER,
    proof_note="verify_shatter. Solo gate remix. Prior MKII G4 was glitch from "
               "c1ea1c53 (SHATTER+STUTTR, old FOLD); tip FOLD re-proof pending.",
    doc="SHATTER beside the stock effects (all but PLATE REV, whose words it takes).",
    modules=(
        "SHATTER",
        "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
        "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
        "DELAY", "SPRING REV", "DARK REV",
    ),
    fallback="NONE",
)
