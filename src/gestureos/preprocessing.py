"""Uniform full-duration interpolation, followed by train-only feature scaling."""
import math
import statistics

from .dataset import require
from .features import FEATURE_NAMES, extract_features
from .split import PARTITIONS

PIPELINE = "imu-features-v1"
CONTRACT = {"schema_version": 1, "pipeline": PIPELINE,
            "time_normalization": "linear_full_duration", "downsampling": "reject",
            "gravity": "preserve", "calibration": "none",
            "feature_scaler": "train_standard_population"}


def validate_config(config):
    require(set(config) == set(CONTRACT) | {"target_points"}, "Unknown or missing preprocessing setting")
    require(all(type(config[k]) is type(v) and config[k] == v for k, v in CONTRACT.items()),
            "Unsupported preprocessing contract")
    require(type(config["target_points"]) is int and 2 <= config["target_points"] <= 512,
            "target_points must be 2..512")


def resample(timestamps_us, values, points):
    require(type(points) is int and 2 <= points <= 512, "Invalid output point count")
    require(len(timestamps_us) == len(values) and len(values) >= 2, "Missing timestamps or samples")
    require(points >= len(values), "Downsampling requires anti-alias filtering; increase target_points")
    require(all(type(t) is int and t >= 0 for t in timestamps_us), "Invalid device timestamps")
    require(all(b > a for a, b in zip(timestamps_us, timestamps_us[1:])), "Non-increasing timestamps")
    require(all(len(row) == 6 and all(math.isfinite(x) for x in row) for row in values),
            "Expected six finite channels")
    relative = [t - timestamps_us[0] for t in timestamps_us]
    duration = relative[-1] / 1e6
    output, left = [], 0
    for index in range(points):
        target = relative[-1] * index / (points - 1)
        while left + 1 < len(relative) - 1 and relative[left + 1] < target:
            left += 1
        weight = (target - relative[left]) / (relative[left + 1] - relative[left])
        output.append([a + weight * (b - a) for a, b in zip(values[left], values[left + 1])])
    return output, duration


def prepare_partitions(loaded, config):
    validate_config(config)
    manifest = loaded["manifest"]
    labels = manifest["labels"]
    lookup = {entry["capture_id"]: entry for entry in manifest["captures"]}
    output = {}
    for partition in PARTITIONS:
        samples = []
        for identity in sorted(manifest["split"]["partitions"][partition]):
            rows = loaded["rows"][identity]
            sequence, duration = resample([r[1] for r in rows], [r[2:8] for r in rows],
                                          config["target_points"])
            samples.append({"capture_id": identity, "label": lookup[identity]["label"],
                            "label_index": labels.index(lookup[identity]["label"]),
                            "duration_s": duration, "sequence": sequence,
                            "features": extract_features(sequence, duration)})
        require(samples, f"Cannot process empty {partition}")
        output[partition] = samples
    # The only fit operation sees the training partition. Holdout values are
    # transformed with these frozen parameters and never contribute statistics.
    train_columns = list(zip(*(row["features"] for row in output["train"])))
    mean = [statistics.fmean(column) for column in train_columns]
    std = [statistics.pstdev(column) for column in train_columns]
    scale = [value if value > 0 else 1.0 for value in std]
    scaler = {"method": "standard_population", "fit_partition": "train",
              "train_capture_ids": [row["capture_id"] for row in output["train"]],
              "feature_names": list(FEATURE_NAMES), "mean": mean, "scale": scale,
              "constant_features": [name for name, value in zip(FEATURE_NAMES, std) if value == 0]}
    for samples in output.values():
        for row in samples:
            row["features_standardized"] = [(x - m) / s for x, m, s in zip(row["features"], mean, scale)]
            require(all(math.isfinite(x) for x in row["features_standardized"]), "Invalid scaled features")
    return {"schema_version": 1, "status": "ready", "pipeline": config,
            "source_manifest_sha256": loaded["manifest_sha256"], "labels": labels,
            "feature_names": list(FEATURE_NAMES), "scaler": scaler, "partitions": output,
            "source_captures": manifest["captures"], "group_by": manifest["split"]["group_by"],
            "source_partitions": manifest["split"]["partitions"]}
