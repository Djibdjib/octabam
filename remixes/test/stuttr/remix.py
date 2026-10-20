"""STUTTR beside stock FX (PLATE REV harvested for its words)."""

from remix.schema import Proof, Remix

REMIX = Remix(
    name="stuttr",
    family="effects",
    proof=Proof.HARDWARE,
    proof_note="Ilia's MKII, remix glitch BUILD G4 (OCTABAMG4 / GLITCH G4.RMX), "
               "19 Oct 2026: every STUTTR page-1/page-2 knob exercised; "
               "verify_stuttr. Solo remix here; G4 was SHATTER+STUTTR.",
    doc="STUTTR beside the stock effects (all but PLATE REV, whose words it takes).",
    modules=(
        "STUTTR",
        "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
        "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
        "DELAY", "SPRING REV", "DARK REV",
    ),
    fallback="NONE",
)
