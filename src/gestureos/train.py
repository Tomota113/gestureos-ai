"""Run RF/SVM/MLP experiments on verified captures, leaving final test unscored."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time
import warnings

from .baselines import (MODEL_NAMES, feature_field, load_prepared, make_estimator,
                        matrix, validate_config, validation_metrics)
from .capture import write_json
from .dataset import fingerprint, read_object, require


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def environment():
    package_root = Path(__file__).resolve().parent
    def git(*args):
        try:
            return subprocess.check_output(["git", *args], cwd=package_root,
                                           stderr=subprocess.DEVNULL, timeout=5).decode().strip()
        except (OSError, subprocess.SubprocessError):
            return None
    return {"python": platform.python_version(), "platform": platform.platform(),
            "machine": platform.machine(), "git_head": git("rev-parse", "HEAD"),
            "git_status": git("status", "--porcelain"),
            "packages": {name: version(name) for name in ("gestureos", "scikit-learn", "numpy",
                         "scipy", "joblib", "threadpoolctl", "narwhals", "cloudpickle")},
            "source_sha256": {p.name: fingerprint(p.read_bytes()) for p in sorted(package_root.glob("*.py"))}}


def save_bundle(path, bundle):
    """Publish only complete joblib files, without overwriting previous artifacts."""
    import joblib
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("xb") as stream:
        joblib.dump(bundle, stream, compress=3)
        stream.flush()
        os.fsync(stream.fileno())
    os.link(temporary, path)  # fails if destination already exists
    temporary.unlink()
    return {"path": path.name, "bytes": path.stat().st_size,
            "sha256": fingerprint(path.read_bytes()), "format": "joblib", "compression": 3}


def pc_latency(estimator, values):
    estimator.predict(values[:1])  # one untimed warmup
    timings = []
    for value in values[:100]:
        batch = [value]
        started = time.perf_counter_ns()
        estimator.predict(batch)
        timings.append((time.perf_counter_ns() - started) / 1e6)
    return {"device": "PC", "unit": "ms", "batch_size": 1, "warmup_calls": 1,
            "samples": len(timings), "repeats_per_sample": 1,
            "partition": "validation", "includes_preprocessing": False,
            "median": statistics.median(timings),
            "p95_nearest_rank": sorted(timings)[math.ceil(.95 * len(timings)) - 1]}


def run_experiment(prepared, provenance, config, output):
    """Internal runner: prepared/provenance must come from load_prepared."""
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_limits
    validate_config(config)
    require(not output.resolve().is_relative_to(Path(provenance["raw_root"])),
            "Experiment output must be outside RAW root")
    runtime = environment()  # missing ML dependencies fail before allocating output
    output.mkdir(parents=True, exist_ok=False)
    try:
        write_json(output / "run.json", {"schema_version": 1, "status": "started",
                   "started_utc": utc_now(), "purpose": "real_capture_baselines",
                   "provenance": provenance, "environment": runtime,
                   "fit_partition": "train", "evaluation_partition": "validation",
                   "test_evaluated": False, "cpu_thread_limit": 1,
                   "rejection": "not_implemented"})
        write_json(output / "config.json", config)
        contract = {key: prepared[key] for key in ("pipeline", "labels", "feature_names", "scaler",
                   "source_captures", "source_partitions", "group_by", "source_manifest_sha256")}
        write_json(output / "data_contract.json", contract)
        reports = {}
        # Only these two partitions can reach a model. The test partition was read
        # for integrity/preprocessing verification, never fit, scored or selected on.
        train_rows = prepared["partitions"]["train"]
        validation_rows = prepared["partitions"]["validation"]
        for name in MODEL_NAMES:
            folder = output / name
            folder.mkdir()
            estimator = make_estimator(name, config)
            write_json(folder / "parameters.json", estimator.get_params(deep=False))
            train_x, train_y = matrix(train_rows, name)
            val_x, val_y = matrix(validation_rows, name)
            with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                started = time.perf_counter()
                estimator.fit(train_x, train_y)
                fit_seconds = time.perf_counter() - started
                predicted = estimator.predict(val_x)
                metrics = validation_metrics(val_y, predicted, prepared["labels"])
                latency = pc_latency(estimator, val_x)
            needs_review = any(issubclass(w.category, ConvergenceWarning) for w in caught)
            saved = save_bundle(folder / "model.joblib", {
                "schema_version": 1, "name": name, "estimator": estimator,
                "input_field": feature_field(name), "labels": prepared["labels"],
                "feature_names": prepared["feature_names"], "pipeline": prepared["pipeline"],
                "scaler": prepared["scaler"], "provenance": provenance,
                "packages": runtime["packages"], "rejection": "not_implemented"})
            report = {"schema_version": 1, "model": name,
                      "status": "needs_review" if needs_review else "complete",
                      "selection_eligible": not needs_review, "fit_seconds_pc": fit_seconds,
                      "input_field": feature_field(name), "validation": metrics,
                      "pc_inference": latency, "artifact": saved,
                      "warnings": [{"category": w.category.__name__, "message": str(w.message)}
                                   for w in caught], "test_evaluated": False}
            write_json(folder / "validation_predictions.json", {"partition": "validation",
                       "rows": [{"capture_id": row["capture_id"], "true_index": row["label_index"],
                                 "predicted_index": int(prediction)}
                                for row, prediction in zip(validation_rows, predicted)]})
            write_json(folder / "result.json", report)
            reports[name] = report
        eligible = [name for name in MODEL_NAMES if reports[name]["selection_eligible"]]
        scores = {name: reports[name]["validation"]["classification_report"]["macro avg"]["f1-score"]
                  for name in MODEL_NAMES}
        # Stable ties use fixed MODEL_NAMES order, not runtime or final test scores.
        ranked = sorted(eligible, key=lambda name: -scores[name])
        comparison = {"criterion": "validation_macro_f1", "scores": scores,
                      "eligible_ranking": ranked, "tie_break_order": list(MODEL_NAMES),
                      "candidate": ranked[0] if ranked else None,
                      "test_evaluated": False, "deployment_approved": False}
        write_json(output / "comparison.json", comparison)
        result = {"schema_version": 1, "status": "needs_review" if any(
                  r["status"] == "needs_review" for r in reports.values()) else "complete",
                  "finished_utc": utc_now(), "models_completed": list(reports),
                  "candidate": comparison["candidate"], "test_evaluated": False}
        write_json(output / "result.json", result)
        return result
    except BaseException as exc:
        # Preserve completed model results and partial files. No automatic retraining.
        try:
            write_json(output / "failure.json", {"status": "interrupted" if isinstance(exc, KeyboardInterrupt)
                       else "failed", "finished_utc": utc_now(), "error_type": type(exc).__name__,
                       "error": str(exc), "test_evaluated": False})
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--collection-config", type=Path, default=Path("configs/collection.json"))
    parser.add_argument("--config", type=Path, default=Path("configs/baselines.json"))
    parser.add_argument("--raw-root", type=Path, help="Relocated RAW root, still reverified")
    parser.add_argument("--output", required=True, type=Path, help="New experiment directory")
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "Experiment already exists; choose a new directory")
        config = read_object(args.config.read_bytes())
        validate_config(config)
        prepared, provenance = load_prepared(args.prepared, args.manifest, args.collection_config,
                                            raw_root=args.raw_root)
        result = run_experiment(prepared, provenance, config, args.output)
        print(json.dumps({"output": str(args.output), **result}, indent=2))
        return 0
    except KeyboardInterrupt:
        parser.exit(130, "Training interrupted. Existing artifacts were preserved.\n")
    except ImportError as exc:
        parser.exit(2, f"ML dependency unavailable: {exc}\nInstall requirements-ml.txt in .venv.\n")
    except (OSError, ValueError, KeyError, TypeError, OverflowError, RuntimeError) as exc:
        parser.exit(2, f"Training failed: {exc}\nExisting RAW and experiments were not overwritten.\n")


if __name__ == "__main__":
    raise SystemExit(main())
