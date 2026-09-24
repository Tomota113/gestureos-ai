"""Analytical scores and recording fakes only; no learned gesture model or physical data."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

from gestureos.baselines import feature_field
from gestureos.capture import write_json
from gestureos.dataset import fingerprint
from gestureos.inference import (FrozenBaseline, load_baseline, validate_contract,
                                validate_estimator, validate_layout)
from gestureos.predict import main
from gestureos.preprocessing import prepare_partitions
from gestureos.rejection import decide, validate_policy
from gestureos.train import environment, save_bundle
import test_preprocessing as fixtures

MODEL_HASH = "a" * 64


class ScoreFake:
    """Records inference inputs, never implements fitting."""
    def __init__(self, count=2, predicted=0, probabilities=None, decision=None):
        self.classes_ = np.arange(count)
        self.n_features_in_ = 64
        self.predicted = predicted
        self.probabilities = np.array([[.8, .2]] if probabilities is None else probabilities)
        self.decision = np.array([-.8] if decision is None else decision)
        self.calls = []

    def get_params(self, deep=False):
        return {"test_double": True}

    def fit(self, *_args, **_kwargs):
        raise AssertionError("Inference must never fit")

    def predict(self, x):
        self.calls.append(copy.deepcopy(x))
        return np.array([self.predicted])

    def predict_proba(self, x):
        self.calls.append(copy.deepcopy(x))
        return self.probabilities

    def decision_function(self, x):
        self.calls.append(copy.deepcopy(x))
        return self.decision


class InferenceTest(unittest.TestCase):
    def setUp(self):
        builder = fixtures.ManifestAndPipelineTest()
        builder.setUp()
        self.addCleanup(builder.doCleanups)
        self.builder, self.temp = builder, builder.temp
        self.loaded = builder.load()
        self.prepared = prepare_partitions(self.loaded, builder.config)
        self.contract = {key: self.prepared[key] for key in ("pipeline", "labels", "feature_names", "scaler",
                         "source_captures", "source_partitions", "group_by", "source_manifest_sha256")}
        self.identity = self.contract["source_partitions"]["validation"][0]
        self.rows = self.loaded["rows"][self.identity]
        self.policy = json.loads(Path("configs/rejection.json").read_text())
        self.experiment = self.temp / "fake_experiment"

    def baseline(self, name="random_forest", fake=None, contract=None):
        return FrozenBaseline(name, fake or ScoreFake(), contract or self.contract, MODEL_HASH)

    def experimental(self, kind="predict_proba_uncalibrated_v1", **changes):
        return {"schema_version": 1, "status": "experimental", "model_sha256": MODEL_HASH,
                "score_kind": kind, "min_score": .7, "min_margin": .3, **changes}

    def make_experiment(self):
        folder = self.experiment / "random_forest"
        folder.mkdir(parents=True)
        runtime = environment()
        provenance = {"manifest_sha256": self.contract["source_manifest_sha256"],
                      "prepared_sha256": "b"*64, "raw_root": str(self.builder.root.resolve())}
        self.bundle = {"schema_version": 1, "name": "random_forest", "input_field": "features",
                       "estimator": ScoreFake(), "provenance": provenance, "packages": runtime["packages"],
                       **{k: self.contract[k] for k in ("pipeline", "scaler", "feature_names", "labels")}}
        write_json(self.experiment / "run.json", {"schema_version": 1, "purpose": "real_capture_baselines",
                   "fit_partition": "train", "evaluation_partition": "validation", "test_evaluated": False,
                   "environment": runtime, "provenance": provenance})
        write_json(self.experiment / "data_contract.json", self.contract)
        write_json(folder / "parameters.json", self.bundle["estimator"].get_params())
        self.report = {"schema_version": 1, "model": "random_forest", "status": "complete",
                       "selection_eligible": True, "test_evaluated": False, "input_field": "features"}
        self.save_model()

    def save_model(self):
        folder = self.experiment / "random_forest"
        path = folder / "model.joblib"
        path.unlink(missing_ok=True)  # test-owned temporary fixture only
        self.report["artifact"] = save_bundle(path, self.bundle)
        (folder / "result.json").write_text(json.dumps(self.report))

    def test_input_features_match_training_pipeline_exactly_without_fit(self):
        before = copy.deepcopy(self.contract)
        for name in ("random_forest", "svm", "mlp"):
            fake = ScoreFake()
            baseline = self.baseline(name, fake)
            result = baseline.score_rows(self.rows)
            expected = next(r for r in self.prepared["partitions"]["validation"] if r["capture_id"] == self.identity)
            self.assertEqual(fake.calls, [[expected[feature_field(name)]]] * 2)
            self.assertEqual(result["start_timestamp_us"], self.rows[0][1])
            self.assertEqual(result["duration_s"], expected["duration_s"])
        self.assertEqual(self.contract, before)

    def test_default_policy_always_rejects_without_hardware_action(self):
        event = self.baseline().predict_rows(self.rows, self.policy)
        self.assertEqual(event["decision"], "UNKNOWN")
        self.assertFalse(event["accepted"])
        self.assertFalse(event["action_authorized"])
        self.assertFalse(event["probability_calibrated"])
        self.assertEqual(event["reasons"], ["policy_unconfigured"])

    def test_experimental_thresholds_boundaries_and_unknown_class(self):
        baseline = self.baseline()
        scored = baseline.score_rows(self.rows)
        exact = self.experimental(min_score=scored["score"], min_margin=scored["margin"])
        self.assertTrue(baseline.predict_rows(self.rows, exact)["accepted"])
        for changes, reason in (({"min_score": .9}, "low_score"), ({"min_margin": .7}, "low_margin")):
            event = baseline.predict_rows(self.rows, self.experimental(**changes))
            self.assertIn(reason, event["reasons"])
            self.assertFalse(event["accepted"])
        event = self.baseline(fake=ScoreFake(predicted=1, probabilities=[[.1, .9]])).predict_rows(self.rows, self.experimental())
        self.assertIn("model_unknown", event["reasons"])
        self.assertEqual(event["label"], "unknown")

    def test_ties_and_predict_score_conflicts_are_rejected_even_at_zero_thresholds(self):
        for probabilities in ([[.5, .5]], [[.3, .7]]):
            baseline = self.baseline(fake=ScoreFake(probabilities=probabilities))
            event = baseline.predict_rows(self.rows, self.experimental(min_score=0, min_margin=0))
            self.assertIn("tie_or_score_conflict", event["reasons"])
            self.assertFalse(event["accepted"])

    def test_binary_svm_signed_scores_follow_class_order_and_are_not_probabilities(self):
        for distance, predicted in ((-2.0, 0), (2.0, 1), (0.0, 0)):
            baseline = self.baseline("svm", ScoreFake(predicted=predicted, decision=[distance]))
            result = baseline.score_rows(self.rows)
            self.assertEqual(list(result["scores"].values()), [-distance, distance])
            self.assertEqual(result["margin"], 2 * abs(distance))
            self.assertEqual(result["score_kind"], "svc_binary_signed_v1")
            self.assertFalse(result["probability_calibrated"])

    def test_multiclass_svm_keeps_predict_and_rejects_ovr_disagreement(self):
        contract = copy.deepcopy(self.contract)
        contract["labels"].append("circle_clockwise")
        lookup = {c["capture_id"]: c for c in contract["source_captures"]}
        for i, ids in enumerate(contract["source_partitions"].values()):
            new = {**lookup[ids[0]], "label": "circle_clockwise", "capture_id": f"{100+i:032x}",
                   "content_sha256": f"{100+i:064x}"}
            contract["source_captures"].append(new)
            ids.append(new["capture_id"])
        contract["scaler"]["train_capture_ids"] = sorted(contract["source_partitions"]["train"])
        fake = ScoreFake(count=3, predicted=0, decision=[[1.1, -.2, 2.1]])
        event = self.baseline("svm", fake, contract).predict_rows(self.rows,
                self.experimental("svc_ovr_decision_v1", min_score=-10, min_margin=0))
        self.assertEqual(event["candidate_label"], "shake")
        self.assertEqual(event["margin"], -1.0)
        self.assertFalse(event["accepted"])

    def test_bad_scores_predictions_and_shapes_never_produce_event(self):
        for probabilities in ([[float("nan"), .2]], [[.8, float("inf")]], [[.8, .8]],
                              [[-.1, 1.1]], [[True, False]], [[".8", ".2"]], [.8, .2], [[1]]):
            with self.subTest(probabilities=probabilities), self.assertRaises((ValueError, TypeError)):
                self.baseline(fake=ScoreFake(probabilities=probabilities)).score_rows(self.rows)
        for prediction in (False, 2, -1, .5):
            with self.assertRaises(ValueError):
                self.baseline(fake=ScoreFake(predicted=prediction)).score_rows(self.rows)
        for decision in ([[1]], [float("nan")], [True], ["1"]):
            with self.assertRaises(ValueError):
                self.baseline("svm", ScoreFake(decision=decision)).score_rows(self.rows)

    def test_bad_sensor_rows_are_rejected_before_estimator_call(self):
        for case in ("length", "seq", "error", "nan", "clipping", "time", "downsample"):
            rows = copy.deepcopy(self.rows)
            if case == "length": rows.pop()
            elif case == "seq": rows[1][0] = 10
            elif case == "error": rows[2][8] = 1
            elif case == "nan": rows[2][2] = float("nan")
            elif case == "clipping": rows[2][2] = 3.96
            elif case == "time": rows[2][1] = rows[1][1]
            else: rows.append([50, rows[-1][1]+10000, *rows[-1][2:]])
            fake = ScoreFake()
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.baseline(fake=fake).score_rows(rows)
            self.assertEqual(fake.calls, [])

    def test_invalid_policy_or_mismatched_model_cannot_accept(self):
        for changes in ({"status": "calibrated"}, {"min_score": float("nan")}, {"min_margin": -1},
                        {"min_score": True}, {"extra": 1}, {"schema_version": True}):
            with self.assertRaises(ValueError):
                validate_policy(self.experimental(**changes))
        for policy in (self.experimental(model_sha256="b"*64), self.experimental("svc_binary_signed_v1")):
            with self.assertRaises(ValueError):
                self.baseline().predict_rows(self.rows, policy)
        scored = self.baseline().score_rows(self.rows)
        for changes in ({"score": 1}, {"margin": 1}, {"candidate_index": 1}):
            with self.assertRaises(ValueError):
                decide({**scored, **changes}, self.experimental(), MODEL_HASH)

    def test_contract_and_layout_mismatches_are_refused(self):
        for case in ("features", "scale", "mean", "fit", "ids", "groups", "labels", "duplicate",
                     "source", "manifest_missing", "manifest_bad"):
            contract = copy.deepcopy(self.contract)
            if case == "features": contract["feature_names"].reverse()
            elif case == "scale": contract["scaler"]["scale"][0] = 0
            elif case == "mean": contract["scaler"]["mean"][0] = float("nan")
            elif case == "fit": contract["scaler"]["fit_partition"] = "test"
            elif case == "ids": contract["scaler"]["train_capture_ids"].pop()
            elif case == "groups":
                for capture in contract["source_captures"]: capture["subject_id"] = "same"
            elif case == "labels": contract["labels"] = ["shake", "shake"]
            elif case == "duplicate": contract["source_captures"][0]["content_sha256"] = contract["source_captures"][1]["content_sha256"]
            elif case == "source": contract["source_captures"][0]["source_kind"] = "synthetic_test"
            elif case == "manifest_missing": contract.pop("source_manifest_sha256")
            else: contract["source_manifest_sha256"] = "not-a-sha256"
            with self.subTest(case=case), self.assertRaises(ValueError): validate_contract(contract)
        for classes in ([1, 0], [0, 2], [0., 1.], [False, True]):
            fake = ScoreFake()
            fake.classes_ = classes
            with self.assertRaises(ValueError): validate_layout(fake, self.contract["labels"])
        fake = ScoreFake()
        fake.n_features_in_ = 63
        with self.assertRaises(ValueError): self.baseline(fake=fake)

    def test_real_unfitted_and_wrong_estimator_types_are_rejected(self):
        from sklearn.ensemble import RandomForestClassifier
        with self.assertRaises(ValueError):
            validate_estimator("random_forest", RandomForestClassifier(), self.contract["labels"])
        with self.assertRaises(ValueError):
            validate_estimator("random_forest", ScoreFake(), self.contract["labels"])

    def test_loader_checks_saved_contract_and_uses_verified_bytes(self):
        self.make_experiment()
        with patch("gestureos.inference.validate_estimator") as check:
            model = load_baseline(self.experiment, "random_forest")
        check.assert_called_once()
        self.assertEqual(model.contract, self.contract)
        self.assertEqual(model.model_sha256, self.report["artifact"]["sha256"])
        self.assertEqual(model.predict_rows(self.rows, self.policy)["decision"], "UNKNOWN")

    def test_loader_refuses_changed_versions_code_and_incomplete_reports_before_unpickling(self):
        self.make_experiment()
        run_path = self.experiment / "run.json"
        report_path = self.experiment / "random_forest/result.json"
        original = run_path.read_text()
        for case in ("python", "package", "code", "test", "review", "incomplete"):
            run = json.loads(original)
            report = copy.deepcopy(self.report)
            if case == "python": run["environment"]["python"] = "0.0.0"
            elif case == "package": run["environment"]["packages"]["numpy"] = "0.0.0"
            elif case == "code": run["environment"]["source_sha256"]["features.py"] = "0"*64
            elif case == "test": run["test_evaluated"] = True
            elif case == "review": report["status"] = "needs_review"
            else: report["selection_eligible"] = False
            run_path.write_text(json.dumps(run))
            report_path.write_text(json.dumps(report))
            with self.subTest(case=case), patch("joblib.load") as unpickle, self.assertRaises(ValueError):
                load_baseline(self.experiment, "random_forest")
            unpickle.assert_not_called()

    def test_checksum_and_bundle_metadata_tampering_fail(self):
        self.make_experiment()
        model_path = self.experiment / "random_forest/model.joblib"
        with model_path.open("ab") as stream: stream.write(b"changed")
        with patch("joblib.load") as unpickle, self.assertRaisesRegex(ValueError, "checksum"):
            load_baseline(self.experiment, "random_forest")
        unpickle.assert_not_called()
        self.bundle["scaler"] = copy.deepcopy(self.bundle["scaler"])
        self.bundle["scaler"]["mean"][0] += 1
        self.save_model()
        with self.assertRaisesRegex(ValueError, "scaler mismatch"):
            load_baseline(self.experiment, "random_forest")

    def test_final_test_ids_copies_and_reserved_groups_are_blocked(self):
        baseline = self.baseline()
        test_id = self.contract["source_partitions"]["test"][0]
        capture = next(c for c in self.contract["source_captures"] if c["capture_id"] == test_id)
        for changed in ({**capture, "content_sha256": "f"*64, "subject_id": "new_person"},
                        {**capture, "capture_id": "f"*32, "subject_id": "new_person"},
                        {**capture, "capture_id": "f"*32, "content_sha256": "f"*64}):
            with self.assertRaisesRegex(ValueError, "Final test"):
                baseline.guard_final_test(changed)
        validation = next(c for c in self.contract["source_captures"] if c["capture_id"] == self.identity)
        baseline.guard_final_test(validation)
        # A new session of a held-out subject stays protected with subject grouping;
        # session grouping permits it only when both identity and signal are new.
        new_session = {**capture, "capture_id": "f"*32, "content_sha256": "f"*64, "session_id": "new_day"}
        with self.assertRaises(ValueError): baseline.guard_final_test(new_session)
        contract = {**self.contract, "group_by": "session"}
        self.baseline(contract=contract).guard_final_test(new_session)

    def test_loader_checks_parameters_and_bundle_versions_even_with_matching_file_hash(self):
        self.make_experiment()
        original = copy.deepcopy(self.bundle)
        for case in ("packages", "provenance", "input", "labels", "parameters"):
            self.bundle = copy.deepcopy(original)
            parameters = {"test_double": True}
            if case == "packages": self.bundle["packages"]["numpy"] = "0.0.0"
            elif case == "provenance": self.bundle["provenance"]["manifest_sha256"] = "f"*64
            elif case == "input": self.bundle["input_field"] = "features_standardized"
            elif case == "labels": self.bundle["labels"].reverse()
            else: parameters = {"test_double": False}
            self.save_model()
            (self.experiment / "random_forest/parameters.json").write_text(json.dumps(parameters))
            with patch("gestureos.inference.validate_estimator"), self.subTest(case=case), self.assertRaises(ValueError):
                load_baseline(self.experiment, "random_forest")

    def test_cli_revalidates_capture_preserves_files_and_refuses_test_before_scoring(self):
        baseline = self.baseline()
        validation = next(c for c in self.contract["source_captures"] if c["capture_id"] == self.identity)
        output = self.temp / "event.json"
        raw = self.builder.root
        before = {p: p.read_bytes() for p in raw.rglob("*") if p.is_file()}
        base = ["predict", "--experiment", str(self.experiment), "--model", "random_forest",
                "--raw-root", str(raw)]
        argv = base + ["--capture", str(raw / validation["path"]), "--output", str(output)]
        with patch.object(sys, "argv", argv), patch("gestureos.predict.load_baseline", return_value=baseline), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(), 0)
        event = json.loads(output.read_text())
        self.assertEqual(event["capture_id"], self.identity)
        self.assertEqual(event["label"], "unknown")
        for path in (output, raw / "forbidden.json", self.experiment / "forbidden.json"):
            with (patch.object(sys, "argv", argv[:-1] + [str(path)]),
                  contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc): main()
            self.assertEqual(exc.exception.code, 2)
        test_id = self.contract["source_partitions"]["test"][0]
        capture = next(c for c in self.contract["source_captures"] if c["capture_id"] == test_id)
        with (patch.object(sys, "argv", base + ["--capture", str(raw / capture["path"]), "--output", str(self.temp/"test.json")]),
              patch("gestureos.predict.load_baseline", return_value=baseline),
              patch.object(baseline, "score_rows") as score,
              contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit)): main()
        score.assert_not_called()
        self.assertEqual(before, {p: p.read_bytes() for p in raw.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
