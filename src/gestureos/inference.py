"""Frozen PC inference from trusted local experiments. No fitting or hardware actions."""
import copy
from importlib.metadata import version
import io
import math
from numbers import Integral
from pathlib import Path
import platform
import pickle
import re

from .baselines import MODEL_NAMES, canonical, feature_field
from .dataset import fingerprint, read_object, require
from .features import FEATURE_NAMES, extract_features
from .preprocessing import resample, validate_config
from .protocol import IDENTIFIER, LABEL
from .rejection import decide, finite_number, validate_policy, validation_ids_sha256
from .split import PARTITIONS, group_key


def validate_contract(contract):
    require(isinstance(contract, dict), "Expected inference contract object")
    require(isinstance(contract.get("source_manifest_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", contract["source_manifest_sha256"]),
            "Invalid contract source manifest fingerprint")
    validate_config(contract["pipeline"])
    labels = contract["labels"]
    require(isinstance(labels, list) and len(labels) >= 2 and "unknown" in labels
            and all(isinstance(x, str) and LABEL.fullmatch(x) for x in labels)
            and len(set(labels)) == len(labels), "Invalid inference label taxonomy")
    require(contract["feature_names"] == list(FEATURE_NAMES), "Feature order/version mismatch")
    scaler = contract["scaler"]
    require(scaler["method"] == "standard_population" and scaler["fit_partition"] == "train"
            and scaler["feature_names"] == list(FEATURE_NAMES), "Invalid frozen scaler contract")
    for key in ("mean", "scale"):
        values = scaler[key]
        require(isinstance(values, list) and len(values) == len(FEATURE_NAMES)
                and all(finite_number(x) for x in values), "Invalid scaler dimensions/values")
    require(all(x > 0 for x in scaler["scale"]), "Non-positive scaler scale")
    constants = scaler["constant_features"]
    require(isinstance(constants, list) and all(isinstance(x, str) for x in constants)
            and len(set(constants)) == len(constants) and set(constants) <= set(FEATURE_NAMES),
            "Invalid constant feature list")
    require(all(scaler["scale"][FEATURE_NAMES.index(x)] == 1 for x in constants),
            "Constant feature scale must be one")
    partitions = contract["source_partitions"]
    require(isinstance(partitions, dict) and set(partitions) == set(PARTITIONS), "Invalid source partitions")
    seen = set()
    for name in PARTITIONS:
        ids = partitions[name]
        require(isinstance(ids, list) and ids and all(isinstance(x, str) and IDENTIFIER.fullmatch(x) for x in ids),
                "Invalid source capture IDs")
        require(len(set(ids)) == len(ids) and seen.isdisjoint(ids), "Source partitions overlap")
        seen.update(ids)
    require(scaler["train_capture_ids"] == sorted(partitions["train"]), "Scaler train IDs mismatch")
    require(contract["group_by"] in ("subject", "session"), "Invalid source grouping")
    captures = contract["source_captures"]
    require(isinstance(captures, list) and len(captures) == len(seen)
            and {c["capture_id"] for c in captures} == seen, "Incomplete source capture contract")
    require(all(c["source_kind"] == "hardware" and c["label"] in labels
                and isinstance(c["content_sha256"], str)
                and re.fullmatch(r"[0-9a-f]{64}", c["content_sha256"])
                for c in captures), "Invalid source capture provenance")
    require(len({c["content_sha256"] for c in captures}) == len(captures), "Duplicate source signal")
    lookup = {c["capture_id"]: c for c in captures}
    groups = set()
    for ids in partitions.values():
        current = {group_key(lookup[i], contract["group_by"]) for i in ids}
        require(groups.isdisjoint(current), "Source groups overlap")
        require({lookup[i]["label"] for i in ids} == set(labels), "Incomplete source label coverage")
        groups.update(current)


def validate_layout(estimator, labels):
    classes = list(estimator.classes_)
    require(all(isinstance(x, Integral) and not isinstance(x, bool) for x in classes)
            and classes == list(range(len(labels))), "Estimator class order differs from labels")
    require(isinstance(estimator.n_features_in_, Integral)
            and estimator.n_features_in_ == len(FEATURE_NAMES), "Estimator input dimension mismatch")


def validate_estimator(name, estimator, labels):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.svm import SVC
    from sklearn.utils.validation import check_is_fitted
    expected = dict(zip(MODEL_NAMES, (RandomForestClassifier, SVC, MLPClassifier)))
    require(type(estimator) is expected[name], "Estimator type differs from model name")
    check_is_fitted(estimator)
    validate_layout(estimator, labels)
    if name == "svm":
        require(estimator.decision_function_shape == "ovr", "Only OVR SVC scores are supported")
        require(estimator.fit_status_ == 0, "SVM did not converge")


def load_baseline(experiment, name):
    """Only pass an experiment you trust. Hashes detect corruption, not malicious pickle."""
    import joblib
    require(name in MODEL_NAMES, "Unknown model")
    experiment = Path(experiment).resolve()
    folder = experiment / name
    run = read_object((experiment / "run.json").read_bytes())
    report = read_object((folder / "result.json").read_bytes())
    contract = read_object((experiment / "data_contract.json").read_bytes())
    require(type(run["schema_version"]) is int and run["schema_version"] == 1
            and run["purpose"] == "real_capture_baselines", "Invalid experiment schema")
    require(run["fit_partition"] == "train" and run["evaluation_partition"] == "validation"
            and run["test_evaluated"] is False, "Unsupported experiment partition usage")
    require(type(report["schema_version"]) is int and report["schema_version"] == 1
            and report["model"] == name and report["status"] == "complete"
            and report["selection_eligible"] is True and report["test_evaluated"] is False
            and report["input_field"] == feature_field(name), "Model is incomplete or needs review")
    packages = run["environment"]["packages"]
    required = {"gestureos", "scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl", "narwhals", "cloudpickle"}
    require(set(packages) == required, "Missing or unsupported runtime package contract")
    require(run["environment"]["python"] == platform.python_version(), "Python version mismatch")
    require(all(version(key) == value for key, value in packages.items()), "Runtime package version mismatch")
    for module in ("features.py", "preprocessing.py"):
        require(run["environment"]["source_sha256"][module]
                == fingerprint(Path(__file__).with_name(module).read_bytes()),
                "Preprocessing implementation changed since training")
    validate_contract(contract)
    require(contract["source_manifest_sha256"] == run["provenance"]["manifest_sha256"],
            "Source manifest differs from experiment")
    artifact = report["artifact"]
    require(artifact["path"] == "model.joblib" and artifact["format"] == "joblib", "Unsupported model artifact")
    data = (folder / "model.joblib").read_bytes()
    require(len(data) == artifact["bytes"] and fingerprint(data) == artifact["sha256"],
            "Model artifact checksum/size mismatch")
    # Deserialize the very bytes whose hash was checked, without a second file read.
    try:
        bundle = joblib.load(io.BytesIO(data))
    except (pickle.UnpicklingError, EOFError, IndexError) as exc:
        raise ValueError("Unreadable local model artifact") from exc
    require(isinstance(bundle, dict), "Expected model bundle object")
    require(type(bundle["schema_version"]) is int and bundle["schema_version"] == 1
            and bundle["name"] == name and bundle["input_field"] == feature_field(name),
            "Invalid model bundle schema/input")
    for key in ("pipeline", "scaler", "feature_names", "labels"):
        require(canonical(bundle[key]) == canonical(contract[key]), f"Bundle {key} mismatch")
    require(bundle["packages"] == packages and bundle["provenance"] == run["provenance"],
            "Bundle environment/provenance mismatch")
    validate_estimator(name, bundle["estimator"], contract["labels"])
    parameters = read_object((folder / "parameters.json").read_bytes())
    require(canonical(bundle["estimator"].get_params(deep=False)) == canonical(parameters),
            "Estimator parameters differ from experiment")
    return FrozenBaseline(name, bundle["estimator"], contract, artifact["sha256"],
                          provenance=bundle["provenance"])


def numeric_output(raw, shape):
    import numpy as np
    values = np.asarray(raw)
    require(values.shape == shape and values.dtype.kind in "iuf" and np.isfinite(values).all(),
            "Invalid numeric model score shape/type/values")
    return values.astype(float).tolist()


class FrozenBaseline:
    """Low-level score_rows requires capture rows already verified by load_capture/manifest."""
    def __init__(self, name, estimator, contract, model_sha256, *, provenance=None):
        require(name in MODEL_NAMES, "Unknown model")
        validate_contract(contract)
        validate_layout(estimator, contract["labels"])
        require(isinstance(model_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", model_sha256),
                "Invalid model fingerprint")
        self.name, self.estimator = name, estimator
        self.contract = copy.deepcopy(contract)
        self.model_sha256 = model_sha256
        self.provenance = copy.deepcopy(provenance)

    def score_rows(self, rows):
        require(50 <= len(rows) <= 500 and all(len(row) == 9 and type(row[0]) is int
                and row[0] == i and type(row[8]) is int and row[8] == 0 for i, row in enumerate(rows)),
                "Expected complete IMU rows without I2C errors")
        axes = [row[2:8] for row in rows]
        require(all(all(finite_number(x) and abs(x) < limit
                        for x, limit in zip(row, (3.96,) * 3 + (495,) * 3)) for row in axes),
                "Invalid or saturated sensor axes")
        sequence, duration = resample([row[1] for row in rows], axes, self.contract["pipeline"]["target_points"])
        features = extract_features(sequence, duration)
        if self.name != "random_forest":
            scaler = self.contract["scaler"]
            features = [(x - mean) / scale for x, mean, scale in zip(features, scaler["mean"], scaler["scale"])]
        require(all(math.isfinite(x) for x in features), "Non-finite model input")
        labels = self.contract["labels"]
        prediction = list(self.estimator.predict([features]))
        require(len(prediction) == 1 and isinstance(prediction[0], Integral)
                and not isinstance(prediction[0], bool) and 0 <= prediction[0] < len(labels), "Invalid prediction")
        index = int(prediction[0])
        if self.name == "svm":
            raw = self.estimator.decision_function([features])
            if len(labels) == 2:
                distance = numeric_output(raw, (1,))[0]
                scores, kind = [-distance, distance], "svc_binary_signed_v1"
            else:
                scores, kind = numeric_output(raw, (1, len(labels)))[0], "svc_ovr_decision_v1"
        else:
            raw = self.estimator.predict_proba([features])
            scores, kind = numeric_output(raw, (1, len(labels)))[0], "predict_proba_uncalibrated_v1"
            require(all(0 <= x <= 1 for x in scores) and math.isclose(sum(scores), 1, abs_tol=1e-6),
                    "Invalid probability score range/sum")
        require(all(math.isfinite(x) for x in scores), "Non-finite model scores")
        score = scores[index]
        margin = score - max(value for i, value in enumerate(scores) if i != index)
        require(math.isfinite(margin), "Non-finite model margin")
        return {"candidate_label": labels[index], "candidate_index": index,
                "score_kind": kind, "score": score, "margin": margin,
                "scores": dict(zip(labels, scores)), "probability_calibrated": False,
                "start_timestamp_us": rows[0][1], "end_timestamp_us": rows[-1][1],
                "duration_s": duration}

    def predict_rows(self, rows, policy):
        validate_policy(policy)
        if "source_manifest_sha256" in policy:
            require(policy["source_manifest_sha256"] == self.contract["source_manifest_sha256"],
                    "Policy source manifest differs from model")
            require(policy["validation_ids_sha256"] == validation_ids_sha256(
                self.contract["source_partitions"]["validation"]), "Policy validation split differs from model")
        return decide(self.score_rows(rows), policy, self.model_sha256)

    def guard_final_test(self, capture):
        test_ids = set(self.contract["source_partitions"]["test"])
        test_captures = [c for c in self.contract["source_captures"] if c["capture_id"] in test_ids]
        require(capture["capture_id"] not in test_ids
                and capture["content_sha256"] not in {c["content_sha256"] for c in test_captures}
                and group_key(capture, self.contract["group_by"]) not in {
                    group_key(c, self.contract["group_by"]) for c in test_captures},
                "Final test capture, duplicate signal or reserved group: diagnostic inference refused")
