"""Artificial capture dossiers under work/, never measurements or ML results.

Some fixtures deliberately emulate hardware metadata to exercise validation;
their origin remains a unit-test generator, not a physical sensor.
"""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

from gestureos.capture import CaptureStore
from gestureos.dataset import load_capture, scan
from gestureos.prepare import main
from gestureos.protocol import CaptureParser, PROTOCOL, Request
from gestureos.split import grouped_split, group_key
from test_capture import fixture, frame


class DatasetTest(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir="work", prefix="synthetic-dataset-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "raw"
        self.next_id = 1

    def capture(self, subject="s1", session="day1", label="shake", value=None, source="hardware"):
        number = self.next_id
        self.next_id += 1
        request = Request(f"{number:032x}", label, 50)
        lines = fixture(request)
        for i in range(1, 51):
            lines[i] = lines[i].replace(b"0.0000", f"{number / 100 if value is None else value:.4f}".encode(), 1)
        end = json.loads(lines[-1])
        end["crc32"] = f"{zlib.crc32(b''.join(lines[1:-1])):08x}"
        lines[-1] = frame(end)
        store = CaptureStore(self.root, subject, session, request, source_kind=source)
        store.record(frame({"type": "ready", "protocol": PROTOCOL, "rate_hz": 100}))
        parser = CaptureParser(request)
        for line in lines:
            store.record(line)
            parser.feed(line)
        store.finish(parser)
        return store.path

    def mutate_json(self, directory, file, **changes):
        path = directory / file
        obj = json.loads(path.read_text())
        obj.update(changes)
        path.write_text(json.dumps(obj))  # Only disposable artificial fixtures.

    def entries(self):
        for subject in ("s1", "s2", "s3", "s4", "s5"):
            for label in ("shake", "unknown"):
                self.capture(subject=subject, label=label)
        entries, rejected = scan(self.root, ["shake", "unknown"])
        self.assertEqual(rejected, [])
        return entries

    def test_validated_dossier_and_raw_immutability(self):
        directory = self.capture()
        before = {p.name: p.read_bytes() for p in directory.iterdir()}
        entry = load_capture(directory, self.root, ["shake"])
        self.assertEqual(entry["samples"], 50)
        self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})

    def test_reject_synthetic_incomplete_derived_and_bad_identity(self):
        for filename, changes in (
            ("result.json", {"status": "incomplete"}),
            ("request.json", {"parent_capture_id": "x"}),
            ("request.json", {"session_id": "other"}),
            ("result.json", {"eligible_for_training": False}),
        ):
            directory = self.capture()
            self.mutate_json(directory, filename, **changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                load_capture(directory, self.root, ["shake"])
        with self.assertRaisesRegex(ValueError, "provenance"):
            load_capture(self.capture(source="synthetic_test"), self.root, ["shake"])

    def test_raw_checksum_csv_and_result_tampering(self):
        for filename in ("serial.raw", "samples.csv", "result.json"):
            directory = self.capture()
            if filename == "result.json":
                self.mutate_json(directory, filename, metrics={})
            else:
                with (directory / filename).open("ab") as stream:
                    stream.write(b"corrupt\n")
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                load_capture(directory, self.root, ["shake"])

    def test_missing_file_and_symlink(self):
        directory = self.capture()
        (directory / "result.json").unlink()
        accepted, rejected = scan(self.root, ["shake"])
        self.assertEqual(accepted, [])
        self.assertEqual(len(rejected), 1)
        directory = self.capture()
        target = directory / "saved.csv"
        (directory / "samples.csv").rename(target)
        (directory / "samples.csv").symlink_to("saved.csv")
        with self.assertRaisesRegex(ValueError, "symlinked"):
            load_capture(directory, self.root, ["shake"])

    def test_renamed_duplicate_signals_reject_both(self):
        self.capture(value=.25)
        self.capture(session="day2", value=.25)
        accepted, rejected = scan(self.root, ["shake"])
        self.assertEqual(accepted, [])
        self.assertEqual(len(rejected), 2)

    def test_split_disjoint_complete_balanced_and_reproducible(self):
        entries = self.entries()
        for grouping in ("session", "subject"):
            result = grouped_split(entries, ["shake", "unknown"], group_by=grouping)
            self.assertEqual(result, grouped_split(list(reversed(entries)), ["unknown", "shake"], group_by=grouping))
            lookup = {e["capture_id"]: e for e in entries}
            seen = set()
            all_ids = []
            for ids in result["partitions"].values():
                groups = {group_key(lookup[i], grouping) for i in ids}
                self.assertTrue(seen.isdisjoint(groups))
                seen.update(groups)
                all_ids.extend(ids)
                self.assertEqual({lookup[i]["label"] for i in ids}, {"shake", "unknown"})
            self.assertEqual(sorted(all_ids), sorted(lookup))

    def test_insufficient_groups_or_label_coverage_never_fallback(self):
        entries = self.entries()
        with self.assertRaisesRegex(ValueError, "3 independent"):
            grouped_split(entries[:4], ["shake", "unknown"])
        missing = [e for e in entries if e["label"] != "unknown"] + [entries[1]]
        with self.assertRaisesRegex(ValueError, "Label 'unknown'"):
            grouped_split(missing, ["shake", "unknown"])

    def test_sessions_are_scoped_by_subject_and_subject_split_is_stronger(self):
        entries = self.entries()
        self.assertEqual(len({group_key(e, "session") for e in entries}), 5)
        for e in entries:
            e["session_id"], e["subject_id"] = e["subject_id"], "same_user"
        self.assertIsNotNone(grouped_split(entries, ["shake", "unknown"], group_by="session"))
        with self.assertRaisesRegex(ValueError, "3 independent"):
            grouped_split(entries, ["shake", "unknown"], group_by="subject")

    def test_cli_manifest_and_refusal_to_overwrite(self):
        self.entries()
        config = Path(self.temp.name) / "config.json"
        config.write_text(json.dumps({"labels": ["shake", "unknown"]}))
        output = Path(self.temp.name) / "manifest.json"
        args = ["prepare", "--root", str(self.root), "--config", str(config), "--output", str(output)]
        with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)
        first = output.read_bytes()
        with patch.object(sys, "argv", args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main()
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(first, output.read_bytes())

    def test_cli_blocked_report_for_insufficient_data(self):
        self.capture()
        config = Path(self.temp.name) / "config.json"
        config.write_text(json.dumps({"labels": ["shake"]}))
        output = Path(self.temp.name) / "blocked.json"
        args = ["prepare", "--root", str(self.root), "--config", str(config), "--output", str(output)]
        with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 1)
        self.assertIsNone(json.loads(output.read_text())["split"])


if __name__ == "__main__":
    unittest.main()
