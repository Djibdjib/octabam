"""core-copy -- STACK CORE + FUNC+BANK COPY PROJECT (#931).

No SYNTH / VOID / RESONATOR / SC. Unit try of the re-homed COPY entry.
"""

from remix.schema import Pin, Proof, Remix

CORE = (
    "BRAIN", "STORE", "KITS", "MIDI SCENES", "SCENES P2", "PLOCKS P2",
    "CC MAP", "CC FEEDBACK", "USB",
    "RECORDER LOOP FIX", "BATCH_BUGFIXES", "ERASE_EMPTY_TRIGLESS_LOCKS",
    "QUANTIZE_LIVE_REC_TOGGLE", "REC_TRIG_MUTE", "MUTE_MODES",
    "SCALE QUANTIZER", "TUNER", "DIRECT_JUMP_KYOTI", "RELOAD_FROM_PROJECT",
    "RLEN PLEN",
    "ATA WRITE GUARD", "EVENTS",
    "RND NAME",
    "EUCLID FILL",
    "COPY PROJECT",
    "PERSISTENT BUFFERS",
    "REMIX SWITCH",
    "MEMORY",
    "STEM REC",
)

REMIX = Remix(
    name="core-copy",
    family="mods",
    proof=Proof.PORT,
    proof_note="CORE + re-homed COPY PROJECT (CHANGE→FUNC+BANK); port-gated #931",
    doc="STACK CORE with COPY on CHANGE→FUNC+BANK; stock FX1 for a playable tip try.",
    modules=CORE + (
        "LOFI AMF FIX",
        "FILTER",
        "EQUALIZER",
        "DJ EQ",
        "PHASER",
        "FLANGER",
        "CHORUS",
        "SPATIALIZER",
        "COMB FILTER",
        "COMPRESSOR",
        "LO-FI",
        "DELAY",
        "PLATE REV",
        "SPRING REV",
        "DARK REV",
    ),
    fx1=(
        "FILTER",
        "EQUALIZER",
        "DJ EQ",
        "PHASER",
        "FLANGER",
        "CHORUS",
        "SPATIALIZER",
        "COMB FILTER",
        "COMPRESSOR",
        "LO-FI",
    ),
    fallback="NONE",
    settings={
        ("octabam.usb", "TRACKS"): "OFF",
        ("octabam.usb", "MAIN"): 1,
        ("octabam.usb", "CUE"): 0,
        ("octabam.usb", "MASTER"): 0,
        ("octabam.usb", "IN"): "OFF",
        ("kyoti.mute-modes", "PLACE"): Pin("DRAM"),
    },
)
