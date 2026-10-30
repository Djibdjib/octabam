"""KEY LEDS -- the CHROMATIC trig keys light the MIDI track's KEY.

Stock lights the CHROMATIC keyboard as C major whatever the KEY of MIDI
ARP SETUP says: C yellow (keys 1 and 13), the other white keys red, the
black keys dark. On a MIDI track with a KEY set, KEY LEDS lights that KEY
in the same colours: the tonic yellow, the scale's other notes red, the
rest dark. Stock's Major / Minor in every key; with MIDI SCALES, its five
added modes too. KEY OFF and the audio tracks keep stock's keyboard.

One detour at the trig-LED pass's CHROMATIC branch (0x400442e2); no menu,
no setting, nothing saved.
"""

from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof

MODULE = Module(
    name="key-leds",
    key="KEY LEDS",
    kind=Kind.CF_PATCH,
    category=Category.MIDI_USB,
    author="djib",
    author_url="https://github.com/Djibdjib",
    proof=Proof.PORT,
    proof_note="verify_key_leds: the trig LEDs decoded from the panel stream, MKI and MKII, "
               "every KEY 0..84 on a MIDI track and the audio side; not yet on a unit",
    doc="On a MIDI track in CHROMATIC trig mode the trig keys light its ARP SETUP KEY "
        "(the tonic yellow, the scale red, the rest dark) instead of stock's fixed C major; "
        "MIDI SCALES' modes too. KEY OFF and audio tracks: stock.",
    linked=(Linked("kl", "modules/key-leds/key_leds.s", dram=True),),
    detours=(
        Detour(0x400442E2, bytes.fromhex("42854284428647f9400135b0"), "kl", "kl_chromatic",
               "trig-LED pass, CHROMATIC branch: the MIDI track's KEY instead of C major",
               pad_to=12),
    ),
    gates=(Gate("tools/verify/verify_key_leds.py", venv=True),),
)
