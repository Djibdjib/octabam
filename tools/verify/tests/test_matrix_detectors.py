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
