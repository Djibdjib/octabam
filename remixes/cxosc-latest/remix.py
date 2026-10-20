"""cxosc-latest -- ilia latest stack with CX OSC instead of SYNTH MACHINE.

SHATTER / STUTTR are not in this worktree. SIDECHAIN_COMPRESSOR is. No TAPE ECHO
(quartet stall when those glitch modules return).
"""

from remix.schema import Pin, Proof, Remix

CORE = (
    "BRAIN", "STORE", "KITS", "MIDI SCENES", "SCENES P2", "PLOCKS P2",
    "CC MAP", "CC FEEDBACK", "USB",
    "RECORDER LOOP FIX", "BATCH_BUGFIXES", "ERASE_EMPTY_TRIGLESS_LOCKS",
    "QUANTIZE_LIVE_REC_TOGGLE", "REC_TRIG_MUTE", "MUTE_MODES",
    "SCALE QUANTIZER", "TUNER", "DIRECT_JUMP_KYOTI", "RELOAD_FROM_PROJECT",
    "RLEN PLEN",
    "RND NAME",
    "EUCLID FILL",
    "COPY PROJECT",
    "PERSISTENT BUFFERS",
    "REMIX SWITCH",
)

REMIX = Remix(
    name="cxosc-latest",
    family="mods",
    proof=Proof.CHECK,
    proof_note="latest stack + CX OSC + SC (no FM / SHATTER / STUTTR / TAPE)",
    doc="Ilia latest without SYNTH MACHINE; CX OSC in its place. SC on. No SHATTER/STUTTR/TAPE.",
    modules=CORE + (
        "MEMORY",
        "STEM REC",
        "CX OSC",
        "SIDECHAIN_COMPRESSOR",
        "LOFI AMF FIX",
        "FILTER",
        "EQUALIZER",
        "DJ EQ",
        "PHASER",
        "FLANGER",
        "CHORUS",
        "SPATIALIZER",
        "COMB FILTER",
        "LO-FI",
        "DELAY",
        "DARK REV",
    ),
    fx1=(
        "FILTER",
        "EQUALIZER",
        "DJ EQ",
        "PHASER",
        "FLANGER",
        "CHORUS",
        "COMB FILTER",
        "SIDECHAIN_COMPRESSOR",
        "LO-FI",
    ),
    fallback="NONE",
    settings={
        ("octabam.usb", "TRACKS"): "PRE",
        ("octabam.usb", "MAIN"): 1,
        ("octabam.usb", "CUE"): 1,
        ("octabam.usb", "MASTER"): 0,
        ("octabam.usb", "IN"): Pin("OFF"),
        ("kyoti.mute-modes", "PLACE"): Pin("DRAM"),
    },
)
