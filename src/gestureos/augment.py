"""Optional, train-only sensor-frame rotation on already split IMU sequences."""
import math
import random

from .dataset import require
from .features import extract_features


def validate_config(config):
    require(isinstance(config, dict) and set(config) == {
        "schema_version", "seed", "copies_per_capture", "max_rotation_degrees"},
        "Unknown or missing augmentation setting")
    require(type(config["schema_version"]) is int and config["schema_version"] == 1,
            "Unsupported augmentation schema")
    require(type(config["seed"]) is int and 0 <= config["seed"] < 2**32,
            "Invalid augmentation seed")
    require(type(config["copies_per_capture"]) is int and 1 <= config["copies_per_capture"] <= 3,
            "copies_per_capture must be 1..3")
    angle = config["max_rotation_degrees"]
    require(type(angle) in (int, float) and math.isfinite(angle) and 0 < angle <= 5,
            "Maximum rotation must be within (0, 5] degrees")


def augment_train(prepared, config):
    """Return new fit rows and lineage; never mutate the prepared partitions.

    The same small rigid rotation is applied to acceleration (including gravity)
    and gyroscope for every time point. Duration and vector norms are unchanged.
    The original training scaler remains frozen and is used for every copy.
    """
    validate_config(config)
    originals = prepared["partitions"]["train"]
    holdout_ids = {row["capture_id"] for partition in ("validation", "test")
                   for row in prepared["partitions"][partition]}
    require(not holdout_ids.intersection(row["capture_id"] for row in originals),
            "Training and holdout capture IDs overlap")
    rng = random.Random(config["seed"])
    rows = list(originals)
    lineage = []
    mean, scale = prepared["scaler"]["mean"], prepared["scaler"]["scale"]
    for parent in originals:
        for index in range(config["copies_per_capture"]):
            angle = math.radians(rng.uniform(-config["max_rotation_degrees"],
                                             config["max_rotation_degrees"]))
            cosine, sine = math.cos(angle), math.sin(angle)
            sequence = [[cosine * row[0] - sine * row[1],
                         sine * row[0] + cosine * row[1], row[2],
                         cosine * row[3] - sine * row[4],
                         sine * row[3] + cosine * row[4], row[5]]
                        for row in parent["sequence"]]
            features = extract_features(sequence, parent["duration_s"])
            identity = f"aug:{parent['capture_id']}:{index + 1}"
            require(identity not in holdout_ids, "Augmented ID overlaps holdout")
            child = {**parent, "capture_id": identity, "parent_capture_id": parent["capture_id"],
                     "sequence": sequence, "features": features,
                     "features_standardized": [(x - m) / s for x, m, s in zip(features, mean, scale)]}
            require(len(features) == len(mean) == len(scale)
                    and all(math.isfinite(x) for x in child["features_standardized"]),
                    "Invalid augmented feature vector")
            rows.append(child)
            lineage.append({"capture_id": identity, "parent_capture_id": parent["capture_id"],
                            "rotation_degrees_z": math.degrees(angle), "partition": "train"})
    return rows, lineage
