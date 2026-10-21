"""DISTORX on FX1 and FX2 beside the stock effects (CHORUS, PLATE REV and SPRING REV give up their words)."""

from remix.schema import Proof, Remix

REMIX = Remix(
    name="distorx",
    family="effects",
    proof=Proof.RENDER,
    proof_note="verify_distorx (dsp_host): bit-exact against distorx_ref.fixed() in every MODE, "
               "the circuit gates, MIX 0, the MODE fade",
    doc="DISTORX on FX1 and FX2 beside the stock effects (all but CHORUS, PLATE REV and SPRING REV, whose words it takes).",
    modules=(
        "DISTORX",
        "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
        "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
        "DELAY", "DARK REV",
    ),
    fx1=("DISTORX",
         "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
         "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI"),
    fallback="NONE",
)
