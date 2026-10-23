"""scope -- SCOPE + TUNER on stock FX (shared TEMPO opener)."""

from remix.schema import Proof, Remix

REMIX = Remix(
    name="scope",
    family="mods",
    proof=Proof.CHECK,
    proof_note="port: make check REMIX=test/scope; unit tip LSCOPE BH under test 23 Oct 2026",
    doc="stock effects with SCOPE + TUNER (shared TEMPO detours).",
    modules=(
        "TUNER",
        "SCOPE",
        "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
        "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
        "DELAY", "PLATE REV", "SPRING REV", "DARK REV",
    ),
    fallback="NONE",
)
