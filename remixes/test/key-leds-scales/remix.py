from remix.schema import Proof, Remix

REMIX = Remix(
    name="key-leds-scales",
    family="mods",
    proof=Proof.PORT,
    proof_note="verify_key_leds",
    doc="KEY LEDS beside MIDI SCALES: every KEY 1..84, the five added modes included, on the CHROMATIC keys.",
    modules=("KEY LEDS", "MIDI SCALES", "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
             "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
             "DELAY", "PLATE REV", "SPRING REV", "DARK REV"),
    fallback="NONE",
)
