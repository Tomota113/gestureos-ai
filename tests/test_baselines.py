"""Artificial fixtures and recording fakes only: no gesture classifier is trained."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import warnings

from gestureos.baselines import (MODEL_NAMES, feature_field, load_prepared, make_estimator,
                                validate_config, validation_metrics)
from gestureos.capture import write_json
from gestureos.dataset import fingerprint
from gestureos.preprocessing import prepare_partitions
from gestureos.train import main, run_experiment, save_bundle
import test_preprocessing as fixtures


class RecordingEstimator:
    """No learning: records calls and always returns class zero."""
    def __init__(self, warning=False):
        self.warning = warning
        self.fit_calls = []
        self.predict_calls = []

    def get_params(self, deep=False):
        return {"test_double": True}

    def fit(self, x, y):
        self.fit_calls.append(copy.deepcopy((x, y)))
        if self.warning:
            from sklearn.exceptions import ConvergenceWarning
            warnings.warn("Artificial convergence warning", ConvergenceWarning)
        return self

    def predict(self, x):
        self.predict_calls.append(copy.deepcopy(x))
        return [0] * len(x)


class BaselinesTest(unittest.TestCase):
    def setUp(self):
        builder = fixtures.ManifestAndPipelineTest()
        builder.setUp()
        self.addCleanup(builder.doCleanups)
        self.builder = builder
        self.temp = builder.temp
        self.prepared = prepare_partitions(builder.load(), builder.config)
        self.path = self.temp / "prepared.json"
        write_json(self.path, self.prepared)
        self.config = json.loads(Path("configs/baselines.json").read_text())
        self.provenance = {"prepared_sha256": fingerprint(self.path.read_bytes()),
                           "manifest_sha256": self.prepared["source_manifest_sha256"],
                           "raw_root": str(builder.root.resolve())}
        self.output = self.temp / "fake_experiment"

    def load(self):
        return load_prepared(self.path, self.builder.manifest_path, self.builder.collection)

    def raw_snapshot(self):
        return {p.relative_to(self.builder.root): p.read_bytes()
                for p in self.builder.root.rglob("*") if p.is_file()}

    def test_prepared_is_recomputed_from_verified_raw(self):
        result, provenance = self.load()
        self.assertEqual(result, self.prepared)
        self.assertEqual(provenance, self.provenance)
        self.assertEqual(result["scaler"]["fit_partition"], "train")

    def test_tampered_features_scaler_labels_partitions_and_version_fail(self):
        for case in ("feature", "scaled", "scaler", "labels", "partition", "version", "bool"):
            data = copy.deepcopy(self.prepared)
            if case == "feature":
                data["partitions"]["train"][0]["features"][0] += 1
            elif case == "scaled":
                data["partitions"]["validation"][0]["features_standardized"][0] += 1
            elif case == "scaler":
                data["scaler"]["mean"][0] += 1
            elif case == "labels":
                data["labels"].reverse()
            elif case == "partition":
                data["partitions"]["test"].pop()
            elif case == "bool":
                data["schema_version"] = True
            else:
                data["pipeline"]["pipeline"] = "future-pipeline"
            self.path.write_text(json.dumps(data))
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.load()

    def test_changed_raw_is_rejected_again_before_training(self):
        raw = self.builder.root / self.builder.entries[0]["path"] / "request.json"
        with raw.open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ValueError, "changed since split"):
            self.load()

    def test_actual_estimator_constructors_disable_internal_holdout_and_calibration(self):
        # Instantiate real classes; never call fit on them with fixtures.
        validate_config(self.config)
        rf = make_estimator("random_forest", self.config)
        svm = make_estimator("svm", self.config)
        mlp = make_estimator("mlp", self.config)
        self.assertEqual(rf.n_jobs, 1)
        self.assertFalse(svm.probability)
        self.assertFalse(mlp.early_stopping)
        for model in (rf, svm, mlp):
            self.assertEqual(model.random_state, 42)
            model._validate_params()  # installed sklearn parameter constraints

    def test_invalid_configs_fail_before_start(self):
        for key, value in (("seed", True), ("seed", -1), ("selection_metric", "test_accuracy"),
                           ("schema_version", 2), ("unexpected", 1)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_config({**self.config, key: value})
        for model, key, value in (("mlp", "early_stopping", True), ("svm", "probability", True),
                                  ("svm", "C", float("nan")), ("svm", "gamma", 0),
                                  ("mlp", "hidden_layer_sizes", [True]),
                                  ("random_forest", "n_estimators", 0)):
            data = copy.deepcopy(self.config)
            data["models"][model][key] = value
            with self.subTest(model=model, key=key), self.assertRaises(ValueError):
                validate_config(data)

    def test_metrics_match_hand_calculation_and_never_hide_missing_predictions(self):
        report = validation_metrics([0, 0, 1, 1], [0, 0, 0, 0], ["shake", "unknown"])
        self.assertEqual(report["accuracy"], .5)
        self.assertEqual(report["confusion_matrix"]["counts"], [[2, 0], [2, 0]])
        self.assertAlmostEqual(report["classification_report"]["macro avg"]["f1-score"], 1/3)
        self.assertEqual(report["classification_report"]["unknown"]["recall"], 0)
        for bad in ([0], [0, 2], [0, .9], [False, 1]):
            with self.assertRaises(ValueError):
                validation_metrics([0, 1], bad, ["shake", "unknown"])

    def test_runner_routes_train_and_validation_only_and_saves_full_contract(self):
        from joblib import load
        before = self.raw_snapshot()
        fakes = {name: RecordingEstimator() for name in MODEL_NAMES}
        prepared = copy.deepcopy(self.prepared)
        # A sentinel that is not even iterable: any use by model routing fails.
        prepared["partitions"]["test"] = object()
        with patch("gestureos.train.make_estimator", side_effect=lambda name, _: fakes[name]):
            result = run_experiment(prepared, self.provenance, self.config, self.output)
        self.assertEqual(result["status"], "complete")
        self.assertFalse(result["test_evaluated"])
        self.assertEqual(result["candidate"], "random_forest")  # fixed tie rule
        self.assertEqual(before, self.raw_snapshot())
        for name, fake in fakes.items():
            field = feature_field(name)
            train = self.prepared["partitions"]["train"]
            val = self.prepared["partitions"]["validation"]
            self.assertEqual(fake.fit_calls, [([r[field] for r in train], [r["label_index"] for r in train])])
            self.assertEqual(fake.predict_calls[0], [r[field] for r in val])
            self.assertTrue(all(row in [r[field] for r in val]
                                for batch in fake.predict_calls for row in batch))
            folder = self.output / name
            # Only load our own locally created fake bundle; never external pickle files.
            saved = load(folder / "model.joblib")
            self.assertEqual(saved["scaler"], self.prepared["scaler"])
            self.assertEqual(saved["labels"], self.prepared["labels"])
            self.assertEqual(saved["feature_names"], self.prepared["feature_names"])
            report = json.loads((folder / "result.json").read_text())
            self.assertEqual(report["artifact"]["sha256"], fingerprint((folder / "model.joblib").read_bytes()))
            self.assertEqual(report["pc_inference"]["device"], "PC")
            self.assertFalse(report["pc_inference"]["includes_preprocessing"])
        snapshots = {p.relative_to(self.output): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        with self.assertRaises(FileExistsError):
            run_experiment(self.prepared, self.provenance, self.config, self.output)
        self.assertEqual(snapshots, {p.relative_to(self.output): p.read_bytes()
                                    for p in self.output.rglob("*") if p.is_file()})

    def test_convergence_warning_excludes_model_from_selection(self):
        with patch("gestureos.train.make_estimator", side_effect=lambda name, _: RecordingEstimator(name == "random_forest")):
            result = run_experiment(self.prepared, self.provenance, self.config, self.output)
        comparison = json.loads((self.output / "comparison.json").read_text())
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["candidate"], "svm")
        self.assertNotIn("random_forest", comparison["eligible_ranking"])
        report = json.loads((self.output / "random_forest/result.json").read_text())
        self.assertEqual(report["warnings"][0]["category"], "ConvergenceWarning")

    def test_all_unconverged_models_give_no_candidate(self):
        with patch("gestureos.train.make_estimator", side_effect=lambda *_: RecordingEstimator(True)):
            result = run_experiment(self.prepared, self.provenance, self.config, self.output)
        self.assertIsNone(result["candidate"])

    def test_interrupted_run_keeps_completed_artifacts(self):
        for error in (KeyboardInterrupt(), RuntimeError("artificial failure")):
            output = self.temp / type(error).__name__
            with patch("gestureos.train.make_estimator", side_effect=[RecordingEstimator(), error]), self.assertRaises(type(error)):
                run_experiment(self.prepared, self.provenance, self.config, output)
            self.assertTrue((output / "random_forest/result.json").is_file())
            self.assertFalse((output / "result.json").exists())
            self.assertFalse((output / "comparison.json").exists())
            failure = json.loads((output / "failure.json").read_text())
            self.assertEqual(failure["error_type"], type(error).__name__)

    def test_outputs_inside_raw_are_refused(self):
        before = self.raw_snapshot()
        with self.assertRaisesRegex(ValueError, "outside RAW"):
            run_experiment(self.prepared, self.provenance, self.config, self.builder.root / "experiment")
        self.assertEqual(before, self.raw_snapshot())

    def test_partial_serialization_does_not_publish_or_overwrite_bundle(self):
        path = self.temp / "model.joblib"
        path.write_bytes(b"existing artifact")
        with self.assertRaises(FileExistsError):
            save_bundle(path, {"test_double": True})
        self.assertEqual(path.read_bytes(), b"existing artifact")
        self.assertTrue(path.with_suffix(".joblib.partial").exists())
        incomplete = self.temp / "incomplete.joblib"
        with patch("joblib.dump", side_effect=OSError("artificial disk failure")), self.assertRaises(OSError):
            save_bundle(incomplete, {"test_double": True})
        self.assertFalse(incomplete.exists())

    def test_cli_checks_integrity_before_any_estimator_or_output_creation(self):
        self.path.write_text('{}')
        argv = ["train", "--prepared", str(self.path), "--manifest", str(self.builder.manifest_path),
                "--collection-config", str(self.builder.collection), "--output", str(self.output)]
        with (patch.object(sys, "argv", argv), patch("gestureos.train.make_estimator") as factory,
              contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc):
            main()
        self.assertEqual(exc.exception.code, 2)
        factory.assert_not_called()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
