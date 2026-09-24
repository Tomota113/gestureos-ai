"""PC baselines: frozen preprocessing, training-only fit, validation-only comparison."""
import math
from numbers import Integral

from .dataset import fingerprint, read_object, require
from .manifest import load_manifest
from .preprocessing import prepare_partitions

MODEL_NAMES = ("random_forest", "svm", "mlp")


def canonical(value):
    import json
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def load_prepared(path, manifest_path, collection_config, *, raw_root=None):
    """Recompute from verified RAW snapshots; never trust editable feature/scaler JSON."""
    data = path.read_bytes()
    saved = read_object(data)
    loaded = load_manifest(manifest_path, collection_config, raw_root=raw_root)
    expected = prepare_partitions(loaded, saved["pipeline"])
    require(canonical(saved) == canonical(expected),
            "Prepared dataset differs from verified RAW/preprocessing; regenerate it")
    require(len(expected["labels"]) >= 2, "Classification requires at least two labels")
    return expected, {"prepared_sha256": fingerprint(data),
                      "manifest_sha256": loaded["manifest_sha256"],
                      "raw_root": loaded["raw_root"]}


def validate_config(config):
    require(set(config) == {"schema_version", "seed", "selection_metric", "models"},
            "Unknown or missing baseline setting")
    require(type(config["schema_version"]) is int and config["schema_version"] == 1,
            "Unsupported baseline schema")
    require(type(config["seed"]) is int and 0 <= config["seed"] < 2**32, "Invalid seed")
    require(config["selection_metric"] == "validation_macro_f1", "Unsupported selection metric")
    models = config["models"]
    require(isinstance(models, dict) and set(models) == set(MODEL_NAMES), "Expected RF, SVM and MLP")
    keys = {"random_forest": {"n_estimators", "max_depth", "min_samples_leaf"},
            "svm": {"C", "gamma", "max_iter"}, "mlp": {"hidden_layer_sizes", "alpha", "max_iter"}}
    for name in MODEL_NAMES:
        require(isinstance(models[name], dict) and set(models[name]) == keys[name],
                f"Unknown or missing {name} setting")
    rf, svm, mlp = (models[name] for name in MODEL_NAMES)
    for value, upper in ((rf["n_estimators"], 2000), (rf["max_depth"], 100),
                         (rf["min_samples_leaf"], 10000), (svm["max_iter"], 1000000),
                         (mlp["max_iter"], 10000)):
        require(type(value) is int and 1 <= value <= upper, "Invalid integer hyperparameter")
    for value in (svm["C"], mlp["alpha"]):
        require(type(value) in (int, float) and math.isfinite(value) and value > 0,
                "C and alpha must be finite and positive")
    require(svm["gamma"] == "scale" or (type(svm["gamma"]) in (int, float)
            and math.isfinite(svm["gamma"]) and svm["gamma"] > 0), "Invalid SVM gamma")
    layers = mlp["hidden_layer_sizes"]
    require(isinstance(layers, list) and 1 <= len(layers) <= 3
            and all(type(x) is int and 1 <= x <= 512 for x in layers), "Invalid MLP layers")


def make_estimator(name, config):
    # Imports remain optional for acquisition/preprocessing installations.
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.svm import SVC
    params = config["models"][name]
    common = {"random_state": config["seed"]}
    if name == "random_forest":
        return RandomForestClassifier(**params, **common, class_weight="balanced", n_jobs=1)
    if name == "svm":
        # No implicit random-fold probability calibration across sessions.
        return SVC(**params, **common, kernel="rbf", class_weight="balanced", probability=False)
    require(name == "mlp", "Unknown model")
    # No internal random validation split: external grouped validation stays fixed.
    return MLPClassifier(**{**params, "hidden_layer_sizes": tuple(params["hidden_layer_sizes"])},
                         **common, solver="adam", early_stopping=False, shuffle=True)


def feature_field(name):
    require(name in MODEL_NAMES, "Unknown model")
    return "features" if name == "random_forest" else "features_standardized"


def matrix(rows, name):
    field = feature_field(name)
    return [row[field] for row in rows], [row["label_index"] for row in rows]


def validation_metrics(truth, predicted, labels):
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    ids = list(range(len(labels)))
    predicted = list(predicted)
    require(all(isinstance(x, Integral) and not isinstance(x, bool) for x in predicted),
            "Predictions must be integer class indices")
    predicted = [int(x) for x in predicted]
    require(len(predicted) == len(truth) and set(predicted) <= set(ids), "Invalid model predictions")
    return {"partition": "validation", "accuracy": float(accuracy_score(truth, predicted)),
            "classification_report": classification_report(truth, predicted, labels=ids,
                target_names=labels, output_dict=True, zero_division=0),
            "confusion_matrix": {"rows": "true", "columns": "predicted", "labels": labels,
                                 "counts": confusion_matrix(truth, predicted, labels=ids).tolist()},
            "zero_division": 0}
