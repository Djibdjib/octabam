"""tools/hw/ot_matrix.py's detectors on synthetic audio: a clean copy of BASE is
unflagged; a click train, added noise, a dropout, a level drop, silence and
clipping each raise their flag. No unit and no firmware."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "hw"))

try:
    import numpy as np
except ImportError:                     # pragma: no cover
    np = None


@unittest.skipIf(np is None, "numpy is not installed")
class MatrixDetectors(unittest.TestCase):
    FS = 44100

    @classmethod
    def setUpClass(cls):
        import ot_matrix
        cls.m = ot_matrix
        rng = np.random.default_rng(1)
        t = np.arange(cls.FS * 12) / cls.FS
        env = np.exp(-((t * 2) % 1) * 6)
        cls.sig = (0.3 * np.sin(2 * np.pi * 220 * t) * env + 1e-4 * rng.standard_normal(len(t))).astype(np.float32)
        cls.rng = rng
        cls.base = ot_matrix.measure(cls.stereo(cls.sig), cls.FS, 12)

    @staticmethod
    def stereo(s):
        return np.stack([s, s], axis=1)

    def flags(self, s):
        return self.m.judge(self.m.measure(self.stereo(s), self.FS, 12), self.base)

    def test_clean_copy(self):
        self.assertEqual(self.flags(self.sig.copy())[0], [])

    def test_clicks(self):
        s = self.sig.copy()
        for i in range(20):
            s[self.FS + i * 4000] += 0.4
        self.assertIn("CLICKS", self.flags(s)[0])

    def test_static(self):
        s = self.sig + (0.02 * self.rng.standard_normal(len(self.sig))).astype(np.float32)
        self.assertIn("STATIC", self.flags(s)[0])

    def test_dropout_is_a_freeze_at_its_second(self):
        s = self.sig.copy()
        s[5 * self.FS:7 * self.FS] = 0
        flags, at = self.flags(s)
        self.assertIn("FREEZE", flags)
        self.assertEqual(at, [5.0])

    def test_level(self):
        self.assertIn("LEVEL", self.flags(self.sig * 0.2)[0])

    def test_silence_is_a_crash(self):
        self.assertEqual(self.flags(np.zeros_like(self.sig))[0], ["CRASH"])

    def test_clip(self):
        self.assertIn("CLIP", self.flags(np.clip(self.sig * 4, -1, 1))[0])


if __name__ == "__main__":
    unittest.main()


@unittest.skipIf(np is None, "numpy is not installed")
class MatrixStimuliProject(unittest.TestCase):
    """The pieces of `ot_matrix.py proj --stimuli` that need no source project."""

    @classmethod
    def setUpClass(cls):
        import ot_matrix
        cls.m = ot_matrix

    def test_round_robin_assignment(self):
        self.assertEqual(self.m.stim_assign(["a", "b", "c"], [1, 2, 3, 4, 5]),
                         [(0, 1), (1, 2), (2, 3), (3, 1), (4, 2)])

    def test_sample_blocks_replace_only_the_named_slots(self):
        import tempfile
        import pathlib
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            old = (b"[SAMPLE]\r\nTYPE=FLEX\r\nSLOT=001\r\nPATH=old.wav\r\n[/SAMPLE]\r\n\r\n"
                   b"[SAMPLE]\r\nTYPE=FLEX\r\nSLOT=129\r\nPATH=\r\n[/SAMPLE]\r\n\r\n")
            for f in ("project.work", "project.strd"):
                (d / f).write_bytes(b"HEAD\r\n" + old)
            self.m._stim_text(d, ["hits", "pink"], {"hits": 176400, "pink": 352800})
            t = (d / "project.work").read_bytes().decode()
            self.assertNotIn("old.wav", t)
            self.assertIn("SLOT=129", t)
            self.assertIn("SLOT=001\r\nPATH=hits.wav\r\nTRIM_BARSx100=200", t)
            self.assertIn("SLOT=002\r\nPATH=pink.wav\r\nTRIM_BARSx100=400", t)
            self.assertEqual((d / "project.work").read_bytes(), (d / "project.strd").read_bytes())

    def test_markers_hold_the_trim_end_and_a_valid_sum(self):
        import struct
        import tempfile
        import pathlib
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / "markers.work").write_bytes(bytes(0x16 + 784 * 4 + 2))
            self.m._stim_markers(d, ["hits", "pink"], {"hits": 176400, "pink": 352800})
            b = (d / "markers.work").read_bytes()
            self.assertEqual(struct.unpack(">III", b[0x16:0x16 + 12]), (0, 176400, 0))
            self.assertEqual(struct.unpack(">III", b[0x16 + 784:0x16 + 784 + 12]), (0, 352800, 0))
            self.assertEqual(int.from_bytes(b[-2:], "big"), sum(b[0x10:-2]) & 0xFFFF)


@unittest.skipIf(np is None, "numpy is not installed")
class MatrixProjectText(unittest.TestCase):
    TEXT = (b"[SETTINGS]\r\nTEMPOx24=2908\r\nMIDI_CLOCK_RECEIVE=0\r\nMIDI_TRANSPORT_RECEIVE=1\r\n"
            b"MIDI_PROGRAM_CHANGE_RECEIVE_CH=-1\r\n[/SETTINGS]\r\n\r\n[STATES]\r\nBANK=2\r\nTRACK_MUTE_MASK=127\r\n[/STATES]\r\n")

    @classmethod
    def setUpClass(cls):
        import ot_matrix
        cls.m = ot_matrix

    def stamp(self, settings, states):
        import pathlib
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            for f in ("project.work", "project.strd"):
                (d / f).write_bytes(self.TEXT)
            changed = self.m.stamp_text(d, settings, states)
            return changed, (d / "project.work").read_bytes().decode(), (d / "project.strd").read_bytes().decode()

    def test_keys_change_in_both_files_and_nothing_else(self):
        changed, work, strd = self.stamp({"MIDI_CLOCK_RECEIVE": 1, "MIDI_PROGRAM_CHANGE_RECEIVE_CH": 0, "TEMPOx24": 2880},
                                         {"BANK": 0, "TRACK_MUTE_MASK": 0})
        self.assertEqual(work, strd)
        self.assertIn("MIDI_CLOCK_RECEIVE=1\r\n", work)
        self.assertIn("MIDI_PROGRAM_CHANGE_RECEIVE_CH=0\r\n", work)
        self.assertIn("MIDI_TRANSPORT_RECEIVE=1\r\n", work)
        self.assertIn("BANK=0\r\nTRACK_MUTE_MASK=0\r\n", work)
        self.assertEqual(changed, {"MIDI_CLOCK_RECEIVE": [0, 1], "MIDI_PROGRAM_CHANGE_RECEIVE_CH": [-1, 0],
                                   "TEMPOx24": [2908, 2880], "BANK": [2, 0], "TRACK_MUTE_MASK": [127, 0]})

    def test_a_missing_key_is_refused(self):
        with self.assertRaises(SystemExit):
            self.stamp({"NO_SUCH_KEY": 1}, {})

    def test_the_test_settings_name_keys_the_unit_writes(self):
        s = self.m.test_settings(3)
        self.assertEqual(s["MIDI_PROGRAM_CHANGE_RECEIVE_CH"], 2)
        self.assertEqual([s[f"MIDI_TRIG_CH{t}"] for t in range(1, 9)], list(range(8)))
