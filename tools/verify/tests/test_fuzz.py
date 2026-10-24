"""tools/hw/ot_fuzz.py's sequence generator: the same seed gives the same sequence, the operations are
valid MIDI for the project's layouts, bursts are bursts, and a profile only uses its own operations."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "hw"))


class FuzzGen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ot_fuzz
        cls.f = ot_fuzz

    def test_same_seed_same_sequence(self):
        a, b = self.f.gen(7, 3, 28, "mix"), self.f.gen(7, 3, 28, "mix")
        self.assertEqual(a, b)
        self.assertNotEqual(a["ops"], self.f.gen(8, 3, 28, "mix")["ops"])

    def test_operations_are_sorted_and_start_with_a_start(self):
        s = self.f.gen(1, 2, 28, "mix")["ops"]
        self.assertEqual(s[0]["op"], "start")
        self.assertEqual([o["t"] for o in s], sorted(o["t"] for o in s))
        self.assertEqual(s[-1]["op"], "stop")

    def test_program_changes_name_layouts_of_the_project(self):
        programs = {self.f.program_of(i) for i in range(28)}
        for o in self.f.gen(3, 5, 28, "pc")["ops"]:
            if o["op"] == "pc":
                self.assertEqual(o["bytes"][0], 0xC0)
                self.assertIn(o["bytes"][1], programs)

    def test_program_of_matches_the_project_layout(self):
        # ot_matrix: slot i is bank i // 4, pattern i % 4 + 1, program 16 * bank + pattern - 1
        self.assertEqual([self.f.program_of(i) for i in (0, 3, 4, 27)], [0, 3, 16, 99])

    def test_bursts_come_close_together(self):
        groups = {}
        for o in self.f.gen(5, 10, 28, "pc")["ops"]:
            if o["note"].startswith("burst "):
                groups.setdefault(o["note"].split()[1].split(".")[0], []).append(o["t"])
        self.assertTrue(groups)
        for ts in groups.values():
            self.assertGreaterEqual(len(ts), 3)
            self.assertLessEqual(max(b - a for a, b in zip(ts, ts[1:])), 0.41)

    def test_a_profile_uses_its_own_operations(self):
        kinds = {o["op"] for o in self.f.gen(2, 10, 28, "pc")["ops"]}
        self.assertTrue(kinds <= {"start", "stop", "pc"})
        kinds = {o["op"] for o in self.f.gen(2, 10, 28, "xf")["ops"]}
        self.assertTrue({"cc"} <= kinds and "tempo" not in kinds)

    def test_midi_bytes_are_in_range(self):
        for o in self.f.gen(9, 10, 28, "mix")["ops"]:
            for b in o["bytes"][1:]:
                self.assertTrue(0 <= b <= 127, o)
            if o["bytes"] and o["bytes"][0] & 0xF0 == 0xB0:
                self.assertIn(o["bytes"][1], list(range(34, 46)) + [7, 48, 49, 55, 56])


if __name__ == "__main__":
    unittest.main()
