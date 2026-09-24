"""Offline collection/flash orchestration tests; synthetic serial frames, no real hardware."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from gestureos.capture import CaptureStore
from gestureos.offline import configuration, publish_capture, run_session, session_counts, usb_ports
from gestureos.protocol import CaptureParser, PROTOCOL, Request
import test_capture as fixtures

spec = importlib.util.spec_from_file_location("flash_offline", "scripts/flash_offline.py")
flash = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flash)


def fake_collect(port, store, *, countdown=0):
    store.record(fixtures.frame({"type": "ready", "protocol": PROTOCOL, "rate_hz": 100}))
    parser = CaptureParser(store.request)
    for line in fixtures.fixture(store.request):
        store.record(line)
        parser.feed(line)
    return store.finish(parser)


class OfflineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="work", prefix="synthetic-offline-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = configuration(Path("configs/collection.json"))

    def session(self, answers, collector=fake_collect):
        iterator = iter(answers)
        with patch("gestureos.offline.collect", side_effect=collector), contextlib.redirect_stdout(io.StringIO()):
            return run_session("/dev/TEST", "user01", "session01", self.root, self.config,
                               ask=lambda _: next(iterator))

    def test_accepted_capture_is_copied_exactly_and_counted(self):
        self.assertEqual(self.session(["main droite, fixture", "1", "o", "q"]), 0)
        source = next((self.root / "pending/user01/session01").iterdir())
        dest = self.root / "raw/user01/session01" / source.name
        for name in ("request.json", "serial.raw", "samples.csv", "result.json"):
            self.assertEqual((source / name).read_bytes(), (dest / name).read_bytes())
        self.assertEqual(json.loads((dest / "human_review.json").read_text())["decision"], "accepted")
        counts, invalid = session_counts(self.root / "raw", "user01", "session01", self.config["labels"])
        self.assertEqual(sum(counts.values()), 1)
        self.assertEqual(counts["swipe_left"], 1)
        self.assertEqual(invalid, 0)
        with self.assertRaises(FileExistsError):
            publish_capture(source, self.root / "pending", self.root / "raw", self.config["labels"])

    def test_rejected_and_unanswered_reviews_never_enter_raw(self):
        self.session(["fixture", "1", "n", "q"])
        self.assertFalse((self.root / "raw").exists())
        source = next((self.root / "pending/user01/session01").iterdir())
        self.assertEqual(json.loads((source / "review.json").read_text())["decision"], "not_accepted")
        self.assertTrue((source / "serial.raw").is_file())
        with self.assertRaises(StopIteration):
            self.session(["fixture", "1"])
        self.assertFalse((self.root / "raw").exists())
        self.assertEqual(len(list((self.root / "pending/user01/session01").iterdir())), 2)

    def test_disconnection_keeps_failure_outside_raw(self):
        def failure(_, store, **kwargs):
            store.record(b"artificial disconnect\n")
            return store.finish(None, "artificial disconnect")
        self.session(["fixture", "1", "q"], collector=failure)
        self.assertFalse((self.root / "raw").exists())
        result = next((self.root / "pending").glob("*/*/*/result.json"))
        self.assertEqual(json.loads(result.read_text())["status"], "incomplete")

    def test_repeat_session_preserves_previous_captures_and_notes(self):
        self.session(["first fixture", "1", "o", "q"])
        snapshot = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.session(["second fixture", "2", "o", "q"])
        self.assertTrue(all(p.read_bytes() == data for p, data in snapshot.items()))
        counts, _ = session_counts(self.root / "raw", "user01", "session01", self.config["labels"])
        self.assertEqual(sum(counts.values()), 2)
        self.assertEqual(len(list((self.root / "session_notes/user01/session01").glob("*.json"))), 2)

    def test_publish_revalidates_raw_and_never_copies_corrupt_capture(self):
        store = CaptureStore(self.root / "pending", "user01", "session01", Request("a"*32, "shake", 50))
        fake_collect(None, store)
        with (store.path / "serial.raw").open("ab") as stream:
            stream.write(b"changed\n")
        with self.assertRaises(ValueError):
            publish_capture(store.path, self.root / "pending", self.root / "raw", self.config["labels"])
        self.assertFalse((self.root / "raw").exists())

    def test_synthetic_provenance_is_not_published(self):
        store = CaptureStore(self.root / "pending", "user01", "session01", Request("a"*32, "shake", 50), source_kind="synthetic_test")
        fake_collect(None, store)
        with self.assertRaises(ValueError):
            publish_capture(store.path, self.root / "pending", self.root / "raw", self.config["labels"])

    def test_bad_identity_and_menu_choices_do_not_create_capture(self):
        with self.assertRaises(ValueError):
            run_session("/dev/TEST", "../escape", "s1", self.root, self.config)
        self.session(["fixture", "invalid", "99", "q"])
        self.assertFalse((self.root / "pending").exists())

    def test_local_check_does_not_use_network_or_open_serial(self):
        from gestureos.offline import main
        with (patch.object(sys, "argv", ["offline", "--check"]),
              patch("socket.socket", side_effect=AssertionError("network forbidden")),
              patch("serial.Serial", side_effect=AssertionError("serial opening forbidden")),
              contextlib.redirect_stdout(io.StringIO())):
            self.assertEqual(main(), 0)

    def test_usb_discovery_excludes_legacy_ttys(self):
        from types import SimpleNamespace
        ports = [SimpleNamespace(device="/dev/ttyS0", vid=None),
                 SimpleNamespace(device="/dev/ttyUSB0", vid=0x10c4)]
        with patch("serial.tools.list_ports.comports", return_value=ports):
            self.assertEqual(usb_ports(), ports[1:])


class OfflineFlashTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir="work", prefix="synthetic-flash-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def invoke(self, runner, answer="INSTALLER"):
        with (patch.object(sys, "argv", ["flash", "dataset", "--port", "/dev/TEST"]),
              patch.object(flash, "PROJECT", self.root),
              patch.object(flash, "image_path", return_value=self.root / "fake.bin"),
              patch.object(flash.subprocess, "run", side_effect=runner) as calls,
              patch("builtins.input", return_value=answer), contextlib.redirect_stdout(io.StringIO())):
            result = flash.main()
        return result, calls

    def test_flash_runs_only_after_complete_backup(self):
        commands = []
        def runner(command, **kwargs):
            commands.append(command)
            if "read_flash" in command:
                Path(command[-1]).write_bytes(b"\0" * 4194304)  # deliberate fake Flash, under work/
            else:
                self.assertTrue(next((self.root / "backups").glob("*/backup.json")).is_file())
        result, _ = self.invoke(runner)
        self.assertEqual(result, 0)
        self.assertIn("read_flash", commands[0])
        self.assertIn("write_flash", commands[1])
        self.assertNotIn("--force", commands[1])
        self.assertNotIn("--erase-all", commands[1])

    def test_incomplete_backup_prevents_flash(self):
        commands = []
        def runner(command, **kwargs):
            commands.append(command)
            Path(command[-1]).write_bytes(b"partial fake backup")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
            self.invoke(runner)
        self.assertEqual(exc.exception.code, 2)
        self.assertEqual(len(commands), 1)
        self.assertIn("read_flash", commands[0])

    def test_cancel_does_not_open_device(self):
        result, calls = self.invoke(lambda *_a, **_k: self.fail("must not run"), answer="non")
        self.assertEqual(result, 0)
        calls.assert_not_called()

    def test_both_bundled_image_checksums_match(self):
        for profile in ("bench", "dataset"):
            self.assertTrue(flash.image_path(profile).is_file())


if __name__ == "__main__":
    unittest.main()
