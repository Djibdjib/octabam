"""modules/pextprobe/decode.py: the frame signature, the three outcomes of a rung, a frozen core."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "modules/pextprobe"))
import decode  # noqa: E402

HI, LO = 0x400000, -0x400000


def frame(mask=0, k=0, go=0, parity=0, marker=decode.MARKER):
    """The 16 + 16 samples the probe writes for one frame."""
    lw = (mask & 0x3FFF) | ((k & 3) << 14)
    rw = (k >> 2) | (go << 1) | (parity << 2) | (marker << 8)
    return ([HI if lw >> j & 1 else LO for j in range(16)], [HI if rw >> j & 1 else LO for j in range(16)])


def stream(frames, lead=0):
    L, R = [0.001] * lead, [0.001] * lead          # an unaligned start, as a capture has
    for f in frames:
        L += f[0]; R += f[1]
    return L, R


class Decode(unittest.TestCase):
    def test_every_field_round_trips(self):
        for mask, k, go, parity in ((0, 0, 0, 0), (0x1555, 7, 1, 1), (0x2AAA, 5, 1, 0), (0x3FFF, 3, 0, 1)):
            L, R = stream([frame(mask, k, go, parity)])
            ph, fr = decode.decode_stream(L, R)
            self.assertEqual((fr[0]["mask"], fr[0]["k"], fr[0]["go"], fr[0]["parity"]), (mask, k, go, parity))

    def test_the_frame_phase_is_found_in_an_unaligned_capture(self):
        for lead in (0, 3, 9, 15):
            L, R = stream([frame(0x1, 1, 1, i & 1) for i in range(40)], lead=lead)
            ph, fr = decode.decode_stream(L, R)
            self.assertEqual(ph, lead % 16)
            self.assertTrue(all(f["marker"] == decode.MARKER for f in fr[:30]))

    def test_gain_and_inversion(self):
        L, R = stream([frame(0x5, 2, 1, i & 1) for i in range(20)])
        _, fr = decode.decode_stream([s * 0.01 for s in L], [s * 0.01 for s in R])
        self.assertEqual(fr[3]["mask"], 0x5)
        _, fr = decode.decode_stream([-s for s in L], [-s for s in R], invert=True)
        self.assertEqual(fr[3]["mask"], 0x5)

    def test_no_marker_is_reported(self):
        L, R = stream([frame(0, 0, 0, 0, marker=0) for _ in range(10)])
        self.assertIn("no marker", " ".join(decode.summarise(*decode.decode_stream(L, R))))


class Outcomes(unittest.TestCase):
    def run_ladder(self, codes, frozen_at=None):
        """Frames of a ladder whose rungs returned `codes` (0..3 each); frozen_at: frames stop after rung k starts."""
        frames, mask = [], 0
        for _ in range(4):
            frames.append(frame(0, 0, 0, len(frames) & 1))
        for k, c in enumerate(codes):
            for _ in range(5):
                frames.append(frame(mask, k, 1, len(frames) & 1))
            if frozen_at == k:
                frames = frames[:-1] + [frames[-1]] * 6        # the last frame repeats: the parity stops toggling
                break
            mask |= c << (2 * k)
        else:
            for _ in range(5):
                frames.append(frame(mask, len(codes), 1, len(frames) & 1))
        return "\n".join(decode.summarise(*decode.decode_stream(*stream(frames))))

    def test_all_real(self):
        t = self.run_ladder([1] * 7)
        self.assertIn("real memory up to rung 6, P:0xffe0", t)

    def test_real_then_alias(self):
        t = self.run_ladder([1, 1, 2, 2, 2, 2, 2])
        self.assertIn("rung 1  P:0x5fe0: REAL", t)
        self.assertIn("rung 2  P:0x7fe0: ALIAS", t)
        self.assertIn("real memory up to rung 1, P:0x5fe0", t)

    def test_real_then_absent(self):
        t = self.run_ladder([1, 3, 3, 3, 3, 3, 3])
        self.assertIn("rung 1  P:0x5fe0: ABSENT", t)

    def test_a_capture_that_goes_silent_is_a_frozen_core(self):
        frames = [frame(0, 0, 1, i & 1) for i in range(20)] + [([0.0] * 16, [0.0] * 16)] * 12
        t = "\n".join(decode.summarise(*decode.decode_stream(*stream(frames))))
        self.assertIn("FRAMES STOPPED ARRIVING (12 frames without the marker after it)", t)
        self.assertIn("rung 0 (P:0x3fe0) never completed", t)

    def test_a_frozen_core_names_the_rung(self):
        t = self.run_ladder([1, 1, 1, 1, 1, 1, 1], frozen_at=2)
        self.assertIn("FRAMES STOPPED ARRIVING", t)
        self.assertIn("rung 2 (P:0x7fe0) never completed", t)
        self.assertIn("the core froze on it", t)


if __name__ == "__main__":
    unittest.main()
