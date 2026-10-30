from remix.schema import Proof, Remix

REMIX = Remix(
    name="key-leds-quantizer",
    family="mods",
    proof=Proof.PORT,
    proof_note="verify_key_leds",
    doc="KEY LEDS beside SCALE QUANTIZER: the audio tracks' CHROMATIC keys light SCALE on ROOT.",
    modules=("KEY LEDS", "SCALE QUANTIZER", "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
             "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
             "DELAY", "PLATE REV", "SPRING REV", "DARK REV"),
    fallback="NONE",
)
