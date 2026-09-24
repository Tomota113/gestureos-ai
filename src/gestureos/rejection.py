"""Explicit, model-bound rejection policies. No calibrated thresholds are invented."""
import math
import re
import json

from .dataset import fingerprint, require
from .protocol import LABEL

SCORE_KINDS = {"predict_proba_uncalibrated_v1", "svc_binary_signed_v1", "svc_ovr_decision_v1"}
POLICY_KEYS = {"schema_version", "status", "model_sha256", "score_kind", "min_score", "min_margin"}
POLICY_BINDING_KEYS = {"source_manifest_sha256", "validation_ids_sha256"}


def validation_ids_sha256(ids):
    return fingerprint(json.dumps(sorted(ids), separators=(",", ":")).encode())


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_policy(policy):
    require(isinstance(policy, dict) and set(policy) in (POLICY_KEYS, POLICY_KEYS | POLICY_BINDING_KEYS),
            "Invalid rejection policy keys")
    require(type(policy["schema_version"]) is int and policy["schema_version"] == 1,
            "Unsupported rejection policy version")
    require(policy["status"] in ("unconfigured", "experimental"), "Unsupported policy status")
    if policy["status"] == "unconfigured":
        require(set(policy) == POLICY_KEYS
                and all(policy[key] is None for key in ("model_sha256", "score_kind", "min_score", "min_margin")),
                "An unconfigured policy must not contain thresholds")
    else:
        require(isinstance(policy["model_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", policy["model_sha256"]), "Invalid model fingerprint")
        require(policy["score_kind"] in SCORE_KINDS, "Unknown score convention")
        require(finite_number(policy["min_score"]) and finite_number(policy["min_margin"])
                and policy["min_margin"] >= 0, "Invalid rejection thresholds")
        if policy["score_kind"] == "predict_proba_uncalibrated_v1":
            require(0 <= policy["min_score"] <= 1 and policy["min_margin"] <= 1,
                    "Probability-score thresholds must be within 0..1")
        if POLICY_BINDING_KEYS <= set(policy):
            require(all(isinstance(policy[key], str) and re.fullmatch(r"[0-9a-f]{64}", policy[key])
                        for key in POLICY_BINDING_KEYS), "Invalid validation/manifest fingerprint")


def decide(scored, policy, model_sha256):
    validate_policy(policy)
    require(scored["score_kind"] in SCORE_KINDS and finite_number(scored["score"])
            and finite_number(scored["margin"]), "Invalid scored prediction")
    scores = scored["scores"]
    require(isinstance(scores, dict) and len(scores) >= 2
            and all(isinstance(label, str) and LABEL.fullmatch(label) and finite_number(value)
                    for label, value in scores.items()), "Invalid class score vector")
    labels = list(scores)
    index = scored["candidate_index"]
    require(type(index) is int and 0 <= index < len(labels)
            and labels[index] == scored["candidate_label"], "Invalid scored class index")
    require(scored["score"] == scores[labels[index]]
            and scored["margin"] == scored["score"] - max(v for k, v in scores.items() if k != labels[index]),
            "Score/margin differs from class score vector")
    if scored["score_kind"] == "predict_proba_uncalibrated_v1":
        require(all(0 <= x <= 1 for x in scores.values()) and math.isclose(sum(scores.values()), 1, abs_tol=1e-6),
                "Invalid probability score range/sum")
    reasons = []
    if policy["status"] == "unconfigured":
        reasons.append("policy_unconfigured")
    else:
        require(policy["model_sha256"] == model_sha256, "Policy belongs to a different model")
        require(policy["score_kind"] == scored["score_kind"], "Policy score convention mismatch")
        if scored["score"] < policy["min_score"]:
            reasons.append("low_score")
        if scored["margin"] < policy["min_margin"]:
            reasons.append("low_margin")
    if scored["candidate_label"] == "unknown":
        reasons.append("model_unknown")
    if scored["margin"] <= 0:
        reasons.append("tie_or_score_conflict")
    accepted = not reasons
    return {**scored, "schema_version": 1, "event": "gesture_decision",
            "label": scored["candidate_label"] if accepted else "unknown",
            "decision": "ACCEPTED" if accepted else "UNKNOWN", "accepted": accepted,
            "reasons": reasons, "policy_status": policy["status"],
            "model_sha256": model_sha256, "action_authorized": False}
