"""KEY LEDS -- the CHROMATIC trig keys light the MIDI track's KEY.

Stock lights the CHROMATIC keyboard as C major whatever the KEY of MIDI
ARP SETUP says: C yellow (keys 1 and 13), the other white keys red, the
black keys dark. On a MIDI track with a KEY set, KEY LEDS lights that KEY
in the same colours: the tonic yellow, the scale's other notes red, the
rest dark. Stock's Major / Minor in every key; with MIDI SCALES, its five
added modes too. With SCALE QUANTIZER, the audio tracks light its SCALE
on its ROOT (key 1 = ROOT, as its keyboard plays). KEY OFF, SCALE OFF and
an audio track without SCALE QUANTIZER keep stock's keyboard.

The display asks one question, kl_source (track, audio / MIDI -> tonic and
mask); the modules that answer it are chosen at build time: stock's KEY,
or MIDI SCALES' own ms_raw / ms_decode when it is in the remix; on the
audio side SCALE QUANTIZER's own SCALE_AT and ROOT. One detour
at the trig-LED pass's CHROMATIC branch (0x400442e2); no menu, no
setting, nothing saved.
"""

from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof


def _sources(modules, _remix):
    """remix.inc: which modules answer kl_source (README "Sources")."""
    return (f".set HAVE_MIDI_SCALES, {int('MIDI SCALES' in modules)}\n"
            f".set HAVE_SCALE_QUANTIZER, {int('SCALE QUANTIZER' in modules)}\n")


MODULE = Module(
    name="key-leds",
    key="KEY LEDS",
    kind=Kind.CF_PATCH,
    category=Category.MIDI_USB,
    author="djib",
    author_url="https://github.com/Djibdjib",
    proof=Proof.PORT,
    proof_note="verify_key_leds: the trig LEDs decoded from the panel stream, MKI and MKII, "
               "every KEY 0..84 on a MIDI track, SCALE QUANTIZER's SCALE / ROOT on an audio track; "
               "not yet on a unit",
    doc="In CHROMATIC trig mode the trig keys light the track's scale (the tonic yellow, the "
        "scale red, the rest dark) instead of stock's fixed C major: a MIDI track's ARP SETUP KEY "
        "(MIDI SCALES' modes too), an audio track's SCALE QUANTIZER SCALE on ROOT. KEY OFF, "
        "SCALE OFF: stock.",
    linked=(Linked("kl", "modules/key-leds/key_leds.s", dram=True, include=_sources),),
    detours=(
        Detour(0x400442E2, bytes.fromhex("42854284428647f9400135b0"), "kl", "kl_chromatic",
               "trig-LED pass, CHROMATIC branch: the track's scale instead of C major",
               pad_to=12),
    ),
    gates=(Gate("tools/verify/verify_key_leds.py", venv=True),),
)
