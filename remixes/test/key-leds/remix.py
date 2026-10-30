from remix.schema import Proof, Remix

REMIX = Remix(
    name="key-leds",
    family="mods",
    proof=Proof.PORT,
    proof_note="verify_key_leds",
    doc="KEY LEDS alone, on the 14 stock effects: stock's Major / Minor KEY on the CHROMATIC keys.",
    modules=("KEY LEDS", "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
             "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
             "DELAY", "PLATE REV", "SPRING REV", "DARK REV"),
    fallback="NONE",
)
