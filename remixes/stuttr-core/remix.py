"""STUTTR unit handoff: CORE + REMIX SWITCH + STUTTR on stock FX (no PLATE)."""

from remix.schema import Pin, Proof, Remix

CORE = ("BRAIN", "STORE", "KITS", "MIDI SCENES", "SCENES P2", "PLOCKS P2",
        "CC MAP", "CC FEEDBACK", "USB",
        "RECORDER LOOP FIX", "BATCH_BUGFIXES", "ERASE_EMPTY_TRIGLESS_LOCKS",
        "QUANTIZE_LIVE_REC_TOGGLE", "REC_TRIG_MUTE", "MUTE_MODES",
        "SCALE QUANTIZER", "TUNER", "DIRECT_JUMP_KYOTI", "RELOAD_FROM_PROJECT",
        "RLEN PLEN", "ATA WRITE GUARD", "REMIX SWITCH")
STOCK = ("FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER", "CHORUS",
         "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI", "DELAY",
         "SPRING REV", "DARK REV")

REMIX = Remix(
    name="stuttr-core",
    family="effects",
    proof=Proof.RENDER,
    proof_note="verify_stuttr; CORE handoff for unit try (declick fades).",
    doc="CORE + REMIX SWITCH + STUTTR beside stock FX (PLATE REV harvested).",
    modules=CORE + ("LOFI AMF FIX", "STUTTR") + STOCK,
    fallback="NONE",
    settings={("octabam.usb", "TRACKS"): "PRE", ("octabam.usb", "MAIN"): 1,
              ("octabam.usb", "CUE"): 1, ("octabam.usb", "MASTER"): 0,
              ("octabam.usb", "IN"): Pin("OFF"),
              ("kyoti.mute-modes", "PLACE"): Pin("DRAM")},
)
