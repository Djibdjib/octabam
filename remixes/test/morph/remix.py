"""MORPH alone: track + UP / DOWN runs a track's scene morph by itself, with STORE and the stock effects."""

from remix.schema import Proof, Remix

REMIX = Remix(
    name="morph",
    family="mods", proof=Proof.CHECK,
    proof_note="22 Oct 2026: tools/morph/test_morph.py (source level, saving against STORE mocks) and "
               "tools/morph/port_morph.py (under the port, with a project); the module on the owner's MKI "
               "inside aCiDtRacK (ACIDV74MP); this remix not flashed",
    doc="MORPH (track + UP / DOWN: the scene morph by itself, saved with the project) with STORE and the stock effects.",
    modules=("MORPH", "STORE", "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
             "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
             "DELAY", "PLATE REV", "SPRING REV", "DARK REV"),
    fallback="NONE",
)
