"""Algorithmic fixtures only, stored under work/ and never used as ML results."""
import contextlib
import copy
import io
import json
from pathlib import Path
import statistics
import sys
import unittest
from unittest.mock import patch

from gestureos.dataset import fingerprint
from gestureos.features import FEATURE_NAMES, extract_features
from gestureos.manifest import load_manifest
from gestureos.preprocess import main
from gestureos.preprocessing import CONTRACT, prepare_partitions, resample, validate_config
from gestureos.split import grouped_split
import test_dataset as fixtures


class NumericalTest(unittest.TestCase):
    def test_irregular_linear_signal_interpolates_exactly(self):
        times = [10**15, 10**15 + 100000, 10**15 + 300000]
        values = [[x, 2*x, -x, 0, 0, 0] for x in (0.0, .1, .3)]
        original = copy.deepcopy(values)
        sequence, duration = resample(times, values, 4)
        self.assertEqual(duration, .3)
        for row, expected in zip(sequence, (0, .1, .2, .3)):
            self.assertAlmostEqual(row[0], expected)
            self.assertAlmostEqual(row[1], 2*expected)
        self.assertEqual(values, original)
        self.assertEqual(sequence[0], values[0])
        self.assertEqual(sequence[-1], values[-1])

    def test_downsampling_and_bad_signals_are_rejected(self):
        valid = [[0, 0, 1, 0, 0, 0]] * 3
        cases = [([0, 1, 2], valid, 2), ([0, 0, 2], valid, 3),
                 ([0, 2, 1], valid, 3), ([0, 1], valid, 3),
                 ([0, 1, 2], [[float("nan")] * 6] * 3, 3),
                 ([0, 1, 2], [[0] * 5] * 3, 3)]
        for args in cases:
            with self.subTest(args=args[0]), self.assertRaises(ValueError):
                resample(*args)

    def test_constant_gravity_is_preserved_and_features_finite(self):
        sequence, duration = resample([0, 1000000], [[0, 0, 1, 0, 0, 0]] * 2, 10)
        features = dict(zip(FEATURE_NAMES, extract_features(sequence, duration)))
        self.assertEqual(len(features), 64)
        self.assertEqual(features["az_g_mean"], 1)
        self.assertEqual(features["acc_magnitude_g_mean"], 1)
        self.assertEqual(features["az_g_std"], 0)
        self.assertEqual(features["acc_jerk_rms_g_s"], 0)
        self.assertEqual(features["corr_ax_g_ay_g"], 0)

    def test_ramp_statistics_correlations_and_physical_time_derivative(self):
        sequence = [[x, 2*x, -x, 0, 0, 0] for x in (0, 1, 2, 3)]
        result = dict(zip(FEATURE_NAMES, extract_features(sequence, 3)))
        self.assertEqual(result["ax_g_mean"], 1.5)
        self.assertAlmostEqual(result["ax_g_std"], 1.25**.5)
        self.assertEqual(result["ax_g_iqr"], 1.5)
        self.assertEqual(result["ax_g_median"], 1.5)
        self.assertAlmostEqual(result["corr_ax_g_ay_g"], 1)
        self.assertAlmostEqual(result["corr_ax_g_az_g"], -1)
        self.assertAlmostEqual(result["acc_jerk_rms_g_s"], 6**.5)
        slower = dict(zip(FEATURE_NAMES, extract_features(sequence, 6)))
        self.assertAlmostEqual(slower["acc_jerk_rms_g_s"], 6**.5 / 2)

    def test_config_does_not_silently_ignore_unknown_options(self):
        for config in ({**CONTRACT, "target_points": 200, "low_pass": True},
                       {**CONTRACT, "target_points": 0},
                       {**CONTRACT, "target_points": 200, "gravity": "remove"}):
            with self.assertRaises(ValueError):
                validate_config(config)


class ManifestAndPipelineTest(unittest.TestCase):
    def setUp(self):
        # Reuse the deliberately artificial capture generator, not its test class.
        builder = fixtures.DatasetTest()
        builder.setUp()
        self.addCleanup(builder.doCleanups)
        self.builder = builder
        self.root = builder.root
        self.temp = Path(builder.temp.name)
        self.entries = builder.entries()
        self.collection = self.temp / "collection.json"
        self.collection.write_text(json.dumps({"labels": ["shake", "unknown"]}))
        self.config = {**CONTRACT, "target_points": 50}
        self.config_path = self.temp / "preprocessing.json"
        self.config_path.write_text(json.dumps(self.config))
        self.manifest = {"schema_version": 1, "status": "ready", "rejected": [],
                         "raw_root": str(self.root.resolve()), "captures": self.entries,
                         "config_sha256": fingerprint(self.collection.read_bytes()),
                         "labels": ["shake", "unknown"], "group_by": "subject", "seed": 42,
                         "split": grouped_split(self.entries, ["shake", "unknown"], group_by="subject")}
        self.manifest_path = self.temp / "manifest.json"
        self.save()

    def save(self):
        self.manifest_path.write_text(json.dumps(self.manifest))

    def load(self):
        return load_manifest(self.manifest_path, self.collection)

    def test_loads_verified_snapshots_and_supports_moved_root(self):
        loaded = self.load()
        self.assertEqual(len(loaded["rows"]), 10)
        relocated = self.temp / "relocated_raw"
        self.root.rename(relocated)
        with self.assertRaises(ValueError):
            self.load()
        moved = load_manifest(self.manifest_path, self.collection, raw_root=relocated)
        self.assertEqual(loaded["rows"], moved["rows"])

    def test_even_valid_metadata_file_changes_invalidate_frozen_manifest(self):
        capture = self.root / self.entries[0]["path"] / "request.json"
        with capture.open("ab") as stream:
            stream.write(b" ")  # Semantically identical JSON, different frozen bytes.
        with self.assertRaisesRegex(ValueError, "changed since split"):
            self.load()

    def test_collection_config_is_frozen(self):
        self.collection.write_text(json.dumps({"labels": ["unknown", "shake"]}))
        with self.assertRaisesRegex(ValueError, "configuration changed"):
            self.load()

    def test_duplicate_assignment_omission_and_incorrect_counts_fail(self):
        original = copy.deepcopy(self.manifest)
        for case in ("duplicate", "omit", "counts"):
            self.manifest = copy.deepcopy(original)
            split = self.manifest["split"]
            if case == "duplicate":
                split["partitions"]["validation"][0] = split["partitions"]["train"][0]
            elif case == "omit":
                split["partitions"]["train"].pop()
            else:
                split["actual_counts"]["train"] += 1
            self.save()
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.load()

    def test_group_leakage_rejected_even_when_ids_and_labels_are_valid(self):
        partitions = self.manifest["split"]["partitions"]
        lookup = {e["capture_id"]: e for e in self.entries}
        a = next(i for i, key in enumerate(partitions["train"]) if lookup[key]["label"] == "shake")
        b = next(i for i, key in enumerate(partitions["validation"]) if lookup[key]["label"] == "shake")
        partitions["train"][a], partitions["validation"][b] = partitions["validation"][b], partitions["train"][a]
        self.save()
        with self.assertRaisesRegex(ValueError, "crosses partitions"):
            self.load()

    def test_unsafe_paths_and_blocked_manifest_rejected(self):
        original = copy.deepcopy(self.manifest)
        for case in ("blocked", "path", "duplicate_signal"):
            self.manifest = copy.deepcopy(original)
            if case == "blocked":
                self.manifest["status"] = "blocked"
            elif case == "path":
                self.manifest["captures"][0]["path"] = "../outside/id"
            else:
                self.manifest["captures"].append(self.manifest["captures"][0])
            self.save()
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.load()

    def test_scaler_fit_never_reads_holdout_statistics(self):
        loaded = self.load()
        original = copy.deepcopy(loaded)
        result = prepare_partitions(loaded, self.config)
        altered = copy.deepcopy(loaded)
        for name in ("validation", "test"):
            for identity in altered["manifest"]["split"]["partitions"][name]:
                for row in altered["rows"][identity]:
                    row[2] += 2  # Pure algorithm fixture, no real RAW edited.
        changed = prepare_partitions(altered, self.config)
        self.assertEqual(result["scaler"], changed["scaler"])
        self.assertEqual(result["partitions"]["train"], changed["partitions"]["train"])
        self.assertNotEqual(result["partitions"]["test"], changed["partitions"]["test"])
        self.assertEqual(loaded, original)
        for index, name in enumerate(FEATURE_NAMES):
            column = [row["features_standardized"][index] for row in result["partitions"]["train"]]
            self.assertAlmostEqual(statistics.fmean(column), 0, places=10)
            self.assertAlmostEqual(statistics.pstdev(column),
                                   0 if name in result["scaler"]["constant_features"] else 1, places=10)

    def test_cli_is_reproducible_and_never_overwrites_or_writes_raw(self):
        first = self.temp / "prepared1.json"
        second = self.temp / "prepared2.json"
        base = ["preprocess", "--manifest", str(self.manifest_path),
                "--collection-config", str(self.collection), "--config", str(self.config_path)]
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        for output in (first, second):
            with patch.object(sys, "argv", base + ["--output", str(output)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        for output in (first, self.root / "forbidden.json"):
            with patch.object(sys, "argv", base + ["--output", str(output)]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                main()
            self.assertEqual(exc.exception.code, 2)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
