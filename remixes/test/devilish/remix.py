"""OCTA303 + dEVILish beside the stock effects (PHASER, whose id dEVILish takes, gives up its words)."""

from remix.schema import Proof, Remix

REMIX = Remix(
    name="devilish",
    family="mods",
    proof=Proof.PORT,
    proof_note="test_octa303 (the Devil Fish engine bit-exact against ref303.py, dEVILish's id, knob "
               "order and defaults agreeing with the engine) and verify_octa303_ui under the port",
    doc="OCTA303 and dEVILish (the Devil Fish mods on FX1 or FX2 of an OCTA-303 track) beside the stock effects but PHASER.",
    modules=(
        "OCTA303", "DEVILISH",
        "FILTER", "EQUALIZER", "DJ EQ", "FLANGER", "CHORUS",
        "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
        "DELAY", "PLATE REV", "SPRING REV", "DARK REV",
    ),
    fx1=("DEVILISH",
         "FILTER", "EQUALIZER", "DJ EQ", "FLANGER", "CHORUS",
         "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI"),
    fallback="NONE",
)
