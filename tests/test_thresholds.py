"""Hand-calculated validation examples, no classifier fitting or synthetic ML result."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from gestureos.capture import write_json
from gestureos.dataset import fingerprint
from gestureos.inference import FrozenBaseline
from gestureos.rejection import validate_policy, validation_ids_sha256
from gestureos.select_thresholds import main
from gestureos.thresholds import candidates, select_policy, summarize, validate_config
from gestureos.preprocessing import prepare_partitions
import test_preprocessing as fixtures
import test_inference as inference_fixtures


LABELS = ["shake", "circle_clockwise", "unknown"]
MODEL = "a" * 64
MANIFEST = "b" * 64


def row(number, truth, scores):
    return scored_row(number, truth, LABELS, scores, "predict_proba_uncalibrated_v1")


def scored_row(number, truth, labels, scores, kind):
    index = max(range(len(scores)), key=lambda i: scores[i])
    score = scores[index]
    return {"capture_id": f"{number:032x}", "truth_label": truth,
            "scored": {"candidate_label": labels[index], "candidate_index": index,
                       "scores": dict(zip(labels, scores)), "score": score,
                       "margin": score - max(x for i, x in enumerate(scores) if i != index),
                       "score_kind": kind}}


class SelectionTest(unittest.TestCase):
    def setUp(self):
        self.records = [row(1, "shake", [.9, .08, .02]),
                        row(2, "shake", [.65, .20, .15]),
                        row(3, "circle_clockwise", [.2, .7, .1]),
                        row(4, "shake", [.35, .55, .10]),
                        row(5, "unknown", [.6, .3, .1]),
                        row(6, "unknown", [.05, .05, .9])]
        self.ids = [r["capture_id"] for r in self.records]
        self.config = {"schema_version": 1, "max_unknown_false_accept_rate": 0,
                       "min_known_correct_accept_rate": .5, "max_candidates_per_axis": 128}

    def select(self, records=None, config=None, ids=None):
        return select_policy(records if records is not None else self.records, LABELS,
                             config if config is not None else self.config, MODEL, MANIFEST,
                             ids if ids is not None else self.ids)

    def test_constraints_pick_measured_breakpoint_and_report_denominators(self):
        result = self.select()
        self.assertEqual(result["status"], "selected")
        self.assertTrue(result["search"]["exact_observed_breakpoints"])
        self.assertFalse(result["test_evaluated"])
        self.assertFalse(result["deployment_approved"])
        self.assertFalse(result["probability_calibrated"])
        policy = result["policy"]
        validate_policy(policy)
        self.assertEqual(policy["min_score"], .65)
        self.assertAlmostEqual(policy["min_margin"], .45)
        metrics = result["metrics"]
        self.assertEqual(metrics["known_total"], 4)
        self.assertEqual(metrics["unknown_total"], 2)
        self.assertEqual(metrics["known_correct_accepted"], 3)
        self.assertEqual(metrics["known_wrong_accepted"], 0)
        self.assertEqual(metrics["known_rejected"], 1)
        self.assertEqual(metrics["unknown_false_accepted"], 0)
        self.assertEqual(metrics["unknown_rejected"], 2)
        self.assertEqual(metrics["known_correct_accept_rate"], .75)
        self.assertEqual(metrics["unknown_false_accept_rate"], 0)

    def test_impossible_tradeoff_is_blocked_without_policy(self):
        rows = copy.deepcopy(self.records)
        rows[1] = row(2, "shake", [.4, .35, .25])
        rows[4] = row(5, "unknown", [.7, .2, .1])
        config = {**self.config, "min_known_correct_accept_rate": .75}
        result = self.select(records=rows, config=config)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["policy"])
        self.assertIsNone(result["metrics"])

    def test_missing_classes_are_blocked_and_never_divide_by_zero(self):
        for subset in (self.records[:4], self.records[4:]):
            result = self.select(subset, ids=[r["capture_id"] for r in subset])
            self.assertEqual(result["status"], "blocked")
            self.assertIsNone(result["policy"])
        with self.assertRaises(ValueError):
            summarize(self.records[:4], [True] * 4)

    def test_wrong_known_acceptance_and_unknown_acceptance_are_separate(self):
        counts = summarize(self.records, [True] * len(self.records))
        self.assertEqual(counts["known_wrong_accepted"], 1)
        self.assertEqual(counts["unknown_false_accepted"], 2)
        self.assertEqual(counts["known_correct_accepted"], 3)
        self.assertEqual(counts["known_wrong_accept_rate"], .25)

    def test_config_requires_explicit_constraints_and_rejects_bad_types(self):
        for changes in ({"max_unknown_false_accept_rate": None}, {"min_known_correct_accept_rate": None},
                        {"max_unknown_false_accept_rate": True}, {"min_known_correct_accept_rate": -1},
                        {"max_unknown_false_accept_rate": float("nan")},
                        {"max_unknown_false_accept_rate": 1.1}, {"max_candidates_per_axis": 1},
                        {"max_candidates_per_axis": True}, {"schema_version": 2}, {"other": 1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_config({**self.config, **changes})

    def test_validation_ids_and_score_convention_cannot_be_swapped(self):
        for ids in (self.ids[::-1], self.ids[:-1], self.ids[:-1] + [self.ids[0]]):
            with self.assertRaises(ValueError): self.select(ids=ids)
        records = copy.deepcopy(self.records)
        records[1]["scored"]["score_kind"] = "svc_ovr_decision_v1"
        with self.assertRaises(ValueError): self.select(records=records)
        records = copy.deepcopy(self.records)
        records[1]["scored"]["scores"].pop("unknown")
        with self.assertRaises(ValueError): self.select(records=records)

    def test_candidate_cap_keeps_extremes_and_reports_approximation(self):
        values = [i / 500 for i in range(501)]
        result, exact = candidates(values, 16)
        self.assertFalse(exact)
        self.assertEqual(result[0], values[0])
        self.assertEqual(result[-1], values[-1])
        self.assertEqual(len(result), 16)
        rows = [row(i+1, "shake" if i % 2 == 0 else "unknown",
                    [0.5 + i / 2000, 0.3 - i / 3000, 0.2 - i / 6000]) for i in range(20)]
        result = self.select(rows, {**self.config, "max_candidates_per_axis": 4,
                                    "max_unknown_false_accept_rate": 1,
                                    "min_known_correct_accept_rate": 0},
                             [r["capture_id"] for r in rows])
        self.assertFalse(result["search"]["exact_observed_breakpoints"])
        self.assertLessEqual(result["search"]["candidate_pairs_evaluated"], 16)

    def test_svm_decision_scores_can_select_negative_thresholds(self):
        cases = (
            (LABELS, "svc_ovr_decision_v1", [
                scored_row(1, "shake", LABELS, [-.2, -1, -2], "svc_ovr_decision_v1"),
                scored_row(2, "circle_clockwise", LABELS, [-1, -.4, -2], "svc_ovr_decision_v1"),
                scored_row(3, "unknown", LABELS, [.1, 0, -1], "svc_ovr_decision_v1"),
                scored_row(4, "unknown", LABELS, [-1, -2, .5], "svc_ovr_decision_v1")]),
            (["shake", "unknown"], "svc_binary_signed_v1", [
                scored_row(1, "shake", ["shake", "unknown"], [-.2, -1], "svc_binary_signed_v1"),
                scored_row(2, "unknown", ["shake", "unknown"], [-.3, -.1], "svc_binary_signed_v1")]),
        )
        for labels, kind, records in cases:
            with self.subTest(kind=kind):
                config = {**self.config, "min_known_correct_accept_rate": 1}
                result = select_policy(records, labels, config, MODEL, MANIFEST,
                                       [r["capture_id"] for r in records])
                self.assertEqual(result["status"], "selected")
                self.assertEqual(result["policy"]["score_kind"], kind)
                self.assertLess(result["policy"]["min_score"], 0)
                validate_policy(result["policy"])
                self.assertEqual(result["metrics"]["known_correct_accept_rate"], 1)
                self.assertEqual(result["metrics"]["unknown_false_accept_rate"], 0)

    def test_bound_policy_rejects_other_manifest_or_validation_split(self):
        result = self.select()
        policy = result["policy"]
        validate_policy(policy)
        base = inference_fixtures.InferenceTest()
        base.setUp()
        self.addCleanup(base.doCleanups)
        prediction = base.baseline()
        policy["score_kind"] = "predict_proba_uncalibrated_v1"
        policy["source_manifest_sha256"] = "f"*64
        with self.assertRaises(ValueError): prediction.predict_rows(base.rows, policy)
        policy["source_manifest_sha256"] = prediction.contract["source_manifest_sha256"]
        with self.assertRaises(ValueError): prediction.predict_rows(base.rows, policy)
        policy["validation_ids_sha256"] = validation_ids_sha256(
            prediction.contract["source_partitions"]["validation"])
        event = prediction.predict_rows(base.rows, policy)
        self.assertEqual(event["event"], "gesture_decision")
        self.assertTrue(event["accepted"])
        self.assertEqual(event["model_sha256"], prediction.model_sha256)
        self.assertFalse(event["action_authorized"])


class SelectionCLITest(unittest.TestCase):
    def setUp(self):
        helper = fixtures.ManifestAndPipelineTest()
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        self.helper = helper
        self.temp = helper.temp
        self.prepared = prepare_partitions(helper.load(), helper.config)
        self.prepared_path = self.temp / "prepared.json"
        write_json(self.prepared_path, self.prepared)
        self.config_path = self.temp / "thresholds.json"
        self.config = {"schema_version": 1, "max_unknown_false_accept_rate": 1,
                       "min_known_correct_accept_rate": 0, "max_candidates_per_axis": 16}
        write_json(self.config_path, self.config)
        self.contract = {key: self.prepared[key] for key in ("pipeline", "labels", "feature_names", "scaler",
                         "source_captures", "source_partitions", "group_by", "source_manifest_sha256")}
        self.baseline = FrozenBaseline("random_forest", inference_fixtures.ScoreFake(), self.contract,
                         MODEL, provenance={"manifest_sha256": self.prepared["source_manifest_sha256"],
                                            "prepared_sha256": fingerprint(self.prepared_path.read_bytes())})
        self.output = self.temp / "thresholds-run"

    def arguments(self):
        return ["select_thresholds", "--prepared", str(self.prepared_path),
                "--manifest", str(self.helper.manifest_path),
                "--collection-config", str(self.helper.collection),
                "--experiment", str(self.temp / "trusted-model"),
                "--model", "random_forest", "--config", str(self.config_path),
                "--output", str(self.output)]

    def test_cli_scores_validation_only_and_writes_auditable_run(self):
        before = {p: p.read_bytes() for p in self.helper.root.rglob("*") if p.is_file()}
        with (patch.object(sys, "argv", self.arguments()),
              patch("gestureos.select_thresholds.load_baseline", return_value=self.baseline),
              contextlib.redirect_stdout(io.StringIO())):
            self.assertEqual(main(), 0)
        scores = json.loads((self.output / "validation_scores.json").read_text())["records"]
        self.assertEqual([r["capture_id"] for r in scores], sorted(self.contract["source_partitions"]["validation"]))
        self.assertEqual(len(self.baseline.estimator.calls), 2 * len(scores))
        result = json.loads((self.output / "result.json").read_text())
        self.assertFalse(result["test_evaluated"])
        self.assertEqual(result["status"], "selected")
        self.assertTrue((self.output / "policy.json").exists())
        self.assertEqual(before, {p: p.read_bytes() for p in self.helper.root.rglob("*") if p.is_file()})
        with (patch.object(sys, "argv", self.arguments()),
              contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error): main()
        self.assertEqual(error.exception.code, 2)

    def test_cli_blocks_default_null_constraints_before_loading_data_or_model(self):
        self.config_path.write_text(Path("configs/threshold_search.json").read_text())
        with (patch.object(sys, "argv", self.arguments()),
              patch("gestureos.select_thresholds.load_baseline") as loader,
              contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error): main()
        self.assertEqual(error.exception.code, 2)
        loader.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_cli_blocked_constraints_write_no_policy(self):
        self.config.update(max_unknown_false_accept_rate=0, min_known_correct_accept_rate=1)
        self.config_path.write_text(json.dumps(self.config))  # test-owned temporary fixture
        with (patch.object(sys, "argv", self.arguments()),
              patch("gestureos.select_thresholds.load_baseline", return_value=self.baseline),
              contextlib.redirect_stdout(io.StringIO())):
            self.assertEqual(main(), 1)
        self.assertEqual(json.loads((self.output / "result.json").read_text())["status"], "blocked")
        for name in ("run.json", "config.json", "validation_scores.json", "result.json"):
            self.assertTrue((self.output / name).is_file())
        self.assertFalse((self.output / "policy.json").exists())
        self.assertFalse((self.output / "validation_decisions.json").exists())

    def test_cli_rejects_mismatch_and_raw_output_before_scoring(self):
        for case in ("manifest", "prepared", "root"):
            baseline = copy.deepcopy(self.baseline)
            args = self.arguments()
            if case == "manifest": baseline.provenance["manifest_sha256"] = "f"*64
            elif case == "prepared": baseline.provenance["prepared_sha256"] = "f"*64
            else: args[-1] = str(self.helper.root / "forbidden")
            with (patch.object(sys, "argv", args),
                  patch("gestureos.select_thresholds.load_baseline", return_value=baseline),
                  contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error): main()
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(self.output.exists())
            self.assertEqual(baseline.estimator.calls, [])


if __name__ == "__main__":
    unittest.main()
