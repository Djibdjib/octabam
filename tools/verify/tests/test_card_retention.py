"""Cards from passing gates leave no disk residue; failures retain evidence."""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
import card_retention  # noqa: E402
import step  # noqa: E402
import module_gates  # noqa: E402


class CardRetention(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text("out/\n")
        (self.root / "out").mkdir()

    def card(self, name, data=b"card"):
        path = self.root / "out" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_success_removes_new_cards_and_preserves_prior_cards(self):
        prior = self.card("prior.img")
        before = card_retention.snapshot(self.root)
        created = self.card("gate/card.img")
        count, size = card_retention.clean_new(self.root, before, "gate")
        self.assertEqual((count, size), (1, 4))
        self.assertTrue(prior.is_file())
        self.assertFalse(created.exists())
        self.assertEqual(__import__("json").loads((self.root / "out/card-retention.json").read_text())["files"],
                         {"out/gate/card.img": 4})

    def test_complete_suite_can_remove_changed_cards(self):
        card = self.card("reused.img", b"old")
        before = card_retention.snapshot(self.root)
        card.write_bytes(b"new-longer")
        self.assertEqual(card_retention.clean_new(self.root, before, include_modified=True), (1, 10))
        self.assertFalse(card.exists())

    def test_failed_gate_and_keep_cards_retain_images(self):
        before = card_retention.snapshot(self.root)
        failed = self.card("failure.img")
        card_retention.finish(self.root, before, "failed", False)
        self.assertTrue(failed.exists())
        with mock.patch.dict(os.environ, {"KEEP_CARDS": "1"}):
            card_retention.finish(self.root, before, "kept", True)
        self.assertTrue(failed.exists())

    def test_open_card_is_kept_but_an_open_log_does_not_block_cleanup(self):
        before = card_retention.snapshot(self.root)
        card = self.card("open.img")
        with card.open("rb"):
            with self.assertRaises(card_retention.RetentionError):
                card_retention.clean_new(self.root, before)
        self.assertTrue(card.exists())
        log = self.root / "out/gate.log"
        with log.open("w"):
            self.assertEqual(card_retention.clean_new(self.root, before), (1, 4))
        self.assertFalse(card.exists())

    def test_pin_nested_repo_and_non_regular_cards_are_protected(self):
        pinned = self.root / "out/pinned"
        pinned.mkdir()
        (pinned / ".keep-cards").touch()
        self.card("pinned/card.img")
        nested = self.root / "out/shards/0"
        nested.mkdir(parents=True)
        (nested / ".git").write_text("gitdir: elsewhere\n")
        self.card("shards/0/card.img")
        real = self.card("real.img")
        (self.root / "out/link.img").symlink_to(real)
        os.link(real, self.root / "out/hard.img")
        self.assertEqual(card_retention.snapshot(self.root), {})

    def test_step_cleans_success_and_keeps_failure(self):
        script = "import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes(b'card');sys.exit(int(sys.argv[2]))"
        with mock.patch.object(card_retention, "ROOT", self.root):
            passed = self.root / "out/passed.img"
            failed = self.root / "out/failed.img"
            self.assertEqual(step.main(["--cards", sys.executable, "-c", script, str(passed), "0"]), 0)
            self.assertFalse(passed.exists())
            self.assertEqual(step.main(["--cards", sys.executable, "-c", script, str(failed), "2"]), 2)
            self.assertTrue(failed.exists())

    def test_later_gate_failure_does_not_keep_earlier_gate_cards(self):
        scripts = []
        for name, code in (("passed", 0), ("failed", 1)):
            rel = pathlib.Path("tools/verify") / f"{name}.py"
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("from pathlib import Path\n"
                            f"Path('out/{name}.img').write_bytes(b'card')\n"
                            f"raise SystemExit({code})\n")
            scripts.append(SimpleNamespace(script=str(rel), remix_arg=False, venv=False))
        gates = [(name, gate) for name, gate in zip(("PASS", "FAIL"), scripts)]
        with (mock.patch.object(module_gates, "ROOT", self.root),
              mock.patch.object(module_gates.registry, "remix", return_value=SimpleNamespace(name="fake")),
              mock.patch.object(module_gates.registry, "selected", return_value=[]),
              mock.patch.object(module_gates, "collect", return_value=gates),
              mock.patch.object(module_gates, "port_built", return_value=True),
              mock.patch.object(module_gates, "command",
                                side_effect=lambda gate, name: [sys.executable, str(self.root / gate.script)]),
              mock.patch.object(module_gates.gate_ledger, "record")):
            self.assertEqual(module_gates.main(["fake", "--stage", "image"]), 1)
        self.assertFalse((self.root / "out/passed.img").exists())
        self.assertTrue((self.root / "out/failed.img").exists())


if __name__ == "__main__":
    unittest.main()
