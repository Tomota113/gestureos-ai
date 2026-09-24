"""Select an experimental rejection policy from validation records only."""
import math
import re

from .dataset import require
from .protocol import IDENTIFIER, LABEL
from .rejection import (SCORE_KINDS, decide, finite_number,
                        validation_ids_sha256)


def validate_config(config):
    require(isinstance(config, dict) and set(config) == {"schema_version",
            "max_unknown_false_accept_rate", "min_known_correct_accept_rate", "max_candidates_per_axis"},
            "Invalid threshold-search configuration")
    require(type(config["schema_version"]) is int and config["schema_version"] == 1,
            "Unsupported threshold-search schema")
    for key in ("max_unknown_false_accept_rate", "min_known_correct_accept_rate"):
        value = config[key]
        require(finite_number(value) and 0 <= value <= 1,
                f"{key} must be explicitly set between 0 and 1")
    value = config["max_candidates_per_axis"]
    require(type(value) is int and 2 <= value <= 256, "max_candidates_per_axis must be 2..256")


def candidates(values, limit):
    """Deterministic observed breakpoints, including both extremes."""
    unique = sorted(set(values))
    if len(unique) <= limit:
        return unique, True
    indices = sorted({round(i * (len(unique) - 1) / (limit - 1)) for i in range(limit)})
    return [unique[i] for i in indices], False


def summarize(records, accepted):
    require(len(records) == len(accepted), "Decision count mismatch")
    known = [r["truth_label"] != "unknown" for r in records]
    known_total = sum(known)
    unknown_total = len(records) - known_total
    require(known_total and unknown_total, "Validation needs known and unknown captures")
    correct = sum(k and a and r["scored"]["candidate_label"] == r["truth_label"]
                  for r, k, a in zip(records, known, accepted))
    wrong = sum(k and a and r["scored"]["candidate_label"] != r["truth_label"]
                for r, k, a in zip(records, known, accepted))
    rejected = known_total - correct - wrong
    false_accept = sum(not k and a for k, a in zip(known, accepted))
    return {"partition": "validation", "known_total": known_total, "unknown_total": unknown_total,
            "known_correct_accepted": correct, "known_wrong_accepted": wrong,
            "known_rejected": rejected, "unknown_false_accepted": false_accept,
            "unknown_rejected": unknown_total - false_accept,
            "known_correct_accept_rate": correct / known_total,
            "known_wrong_accept_rate": wrong / known_total,
            "known_reject_rate": rejected / known_total,
            "unknown_false_accept_rate": false_accept / unknown_total,
            "unknown_reject_rate": (unknown_total - false_accept) / unknown_total}


def select_policy(records, labels, config, model_sha256, manifest_sha256, validation_ids):
    """Return selection and decisions; never read train/test or fit a model."""
    import numpy as np
    validate_config(config)
    require(isinstance(model_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", model_sha256)
            and isinstance(manifest_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", manifest_sha256),
            "Invalid model or manifest fingerprint")
    require(isinstance(labels, list) and len(labels) >= 2 and "unknown" in labels
            and len(set(labels)) == len(labels), "Invalid label taxonomy")
    require(isinstance(records, list) and records and isinstance(validation_ids, list)
            and len(records) == len(validation_ids), "Validation records/IDs missing")
    require(all(type(x) is str and IDENTIFIER.fullmatch(x) for x in validation_ids)
            and len(set(validation_ids)) == len(validation_ids)
            and validation_ids == sorted(validation_ids), "Invalid validation IDs")
    require([r["capture_id"] for r in records] == sorted(validation_ids),
            "Records must be exactly the sorted validation partition")
    kinds = set()
    for row in records:
        require(type(row["truth_label"]) is str and row["truth_label"] in labels, "Invalid truth label")
        scored = row["scored"]
        require(list(scored["scores"]) == labels, "Score labels/order differs from manifest")
        kinds.add(scored["score_kind"])
        # Reuse the production decision contract to validate score/index/margin.
        decide(scored, {"schema_version": 1, "status": "unconfigured", "model_sha256": None,
                "score_kind": None, "min_score": None, "min_margin": None}, model_sha256)
    require(len(kinds) == 1 and next(iter(kinds)) in SCORE_KINDS,
            "Mixed/unsupported score conventions")
    kind = next(iter(kinds))
    known = np.array([r["truth_label"] != "unknown" for r in records], dtype=bool)
    known_total, unknown_total = int(known.sum()), len(records) - int(known.sum())
    base = {"schema_version": 1, "partition": "validation", "records": len(records),
            "known_total": known_total, "unknown_total": unknown_total,
            "model_sha256": model_sha256, "source_manifest_sha256": manifest_sha256,
            "validation_ids_sha256": validation_ids_sha256(validation_ids),
            "constraints": config, "test_evaluated": False,
            "probability_calibrated": False, "deployment_approved": False}
    if not known_total or not unknown_total:
        return {**base, "status": "blocked", "reason": "Validation lacks known or unknown captures",
                "policy": None, "metrics": None, "decisions": []}
    score = np.asarray([r["scored"]["score"] for r in records], dtype=float)
    margin = np.asarray([r["scored"]["margin"] for r in records], dtype=float)
    candidate = [r["scored"]["candidate_label"] for r in records]
    active = np.asarray([label != "unknown" and m > 0 for label, m in zip(candidate, margin)])
    correct = np.asarray([label == r["truth_label"] for label, r in zip(candidate, records)])
    score_floor = 0.0 if kind == "predict_proba_uncalibrated_v1" else float(score.min())
    score_values, exact_score = candidates([score_floor, *score.tolist()], config["max_candidates_per_axis"])
    margin_values, exact_margin = candidates([0.0, *margin[margin > 0].tolist()],
                                               config["max_candidates_per_axis"])
    margin_grid = np.asarray(margin_values)[:, None]
    best, best_key = None, None
    attempts = 0
    for score_threshold in score_values:
        accepted = (active & (score >= score_threshold))[None, :] & (margin[None, :] >= margin_grid)
        valid = accepted & known[None, :]
        correct_counts = (valid & correct[None, :]).sum(axis=1)
        wrong_counts = (valid & ~correct[None, :]).sum(axis=1)
        false_counts = (accepted & ~known[None, :]).sum(axis=1)
        for j, margin_threshold in enumerate(margin_values):
            attempts += 1
            correct_count, wrong_count, false_count = (int(correct_counts[j]), int(wrong_counts[j]),
                                                       int(false_counts[j]))
            if false_count / unknown_total > config["max_unknown_false_accept_rate"] \
                    or correct_count / known_total < config["min_known_correct_accept_rate"]:
                continue
            rank = (correct_count, -wrong_count, -false_count, score_threshold, margin_threshold)
            if best_key is None or rank > best_key:
                best_key, best = rank, (float(score_threshold), float(margin_threshold))
    search = {"score_thresholds": len(score_values), "margin_thresholds": len(margin_values),
              "candidate_pairs_evaluated": attempts, "exact_observed_breakpoints": exact_score and exact_margin,
              "strategy": "observed_breakpoints_or_evenly_spaced_subset"}
    if best is None:
        return {**base, "status": "blocked", "reason": "No threshold pair meets explicit validation constraints",
                "search": search, "policy": None, "metrics": None, "decisions": []}
    policy = {"schema_version": 1, "status": "experimental", "model_sha256": model_sha256,
              "score_kind": kind, "min_score": best[0], "min_margin": best[1],
              "source_manifest_sha256": manifest_sha256,
              "validation_ids_sha256": validation_ids_sha256(validation_ids)}
    decisions = [decide(r["scored"], policy, model_sha256) for r in records]
    metrics = summarize(records, [event["accepted"] for event in decisions])
    require(metrics["unknown_false_accept_rate"] <= config["max_unknown_false_accept_rate"]
            and metrics["known_correct_accept_rate"] >= config["min_known_correct_accept_rate"],
            "Selected thresholds failed independent decision check")
    return {**base, "status": "selected", "search": search, "policy": policy,
            "metrics": metrics, "decisions": decisions}
