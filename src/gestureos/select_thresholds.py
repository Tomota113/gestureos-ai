"""Choose diagnostic UNKNOWN thresholds from a frozen validation partition only."""
import argparse
from pathlib import Path
import json

from .baselines import canonical, load_prepared
from .capture import write_json
from .dataset import read_object, require
from .inference import load_baseline
from .thresholds import select_policy, validate_config


def load_validation(prepared_path, manifest, collection_config, raw_root, experiment, name, output):
    prepared, provenance, rows = load_prepared(prepared_path, manifest, collection_config,
                                               raw_root=raw_root, include_rows=True)
    raw = Path(provenance["raw_root"])
    require(not output.resolve().is_relative_to(raw)
            and not output.resolve().is_relative_to(experiment.resolve()),
            "Selection output must be outside RAW and model experiment")
    baseline = load_baseline(experiment, name)
    require(baseline.contract["source_manifest_sha256"] == provenance["manifest_sha256"],
            "Model and verified manifest differ")
    require(baseline.provenance is not None
            and baseline.provenance["prepared_sha256"] == provenance["prepared_sha256"]
            and baseline.provenance["manifest_sha256"] == provenance["manifest_sha256"],
            "Model and verified prepared/manifest hashes differ")
    require(baseline.contract["source_partitions"] == prepared["source_partitions"]
            and baseline.contract["source_captures"] == prepared["source_captures"]
            and baseline.contract["group_by"] == prepared["group_by"]
            and baseline.contract["labels"] == prepared["labels"]
            and baseline.contract["feature_names"] == prepared["feature_names"]
            and canonical(baseline.contract["pipeline"]) == canonical(prepared["pipeline"])
            and canonical(baseline.contract["scaler"]) == canonical(prepared["scaler"]),
            "Model and verified prepared data differ")
    validation_ids = sorted(prepared["source_partitions"]["validation"])
    lookup = {item["capture_id"]: item for item in prepared["source_captures"]}
    records = [{"capture_id": identity, "truth_label": lookup[identity]["label"],
                "scored": baseline.score_rows(rows[identity])} for identity in validation_ids]
    return records, baseline, provenance, validation_ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--experiment", required=True, type=Path, help="Trusted local model experiment")
    parser.add_argument("--model", required=True, choices=("random_forest", "svm", "mlp"))
    parser.add_argument("--collection-config", type=Path, default=Path("configs/collection.json"))
    parser.add_argument("--raw-root", type=Path, help="Relocated RAW root")
    parser.add_argument("--config", type=Path, default=Path("configs/threshold_search.json"))
    parser.add_argument("--output", required=True, type=Path, help="New selection run directory")
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "Selection run already exists")
        config = read_object(args.config.read_bytes())
        validate_config(config)  # requires explicit objectives; no invented defaults
        records, baseline, provenance, validation_ids = load_validation(
            args.prepared, args.manifest, args.collection_config, args.raw_root,
            args.experiment, args.model, args.output)
        result = select_policy(records, baseline.contract["labels"], config,
                               baseline.model_sha256, provenance["manifest_sha256"], validation_ids)
        output = args.output
        output.mkdir(parents=True, exist_ok=False)
        write_json(output / "run.json", {"schema_version": 1, "purpose": "validation_threshold_selection",
                   "model_name": args.model, "model_sha256": baseline.model_sha256,
                   "prepared_sha256": provenance["prepared_sha256"],
                   "source_manifest_sha256": provenance["manifest_sha256"],
                   "fit_performed": False, "evaluation_partition": "validation", "test_evaluated": False})
        write_json(output / "config.json", config)
        write_json(output / "validation_scores.json", {"partition": "validation", "records": records})
        if result["status"] == "selected":
            write_json(output / "policy.json", result["policy"])
            write_json(output / "validation_decisions.json", {"partition": "validation",
                       "records": [{"capture_id": record["capture_id"],
                                    "truth_label": record["truth_label"], "decision": decision}
                                   for record, decision in zip(records, result["decisions"]) ]})
        write_json(output / "result.json", {key: value for key, value in result.items() if key != "decisions"})
        print(json.dumps({"output": str(output), "status": result["status"],
                          "reason": result.get("reason"), "test_evaluated": False}, indent=2))
        return 0 if result["status"] == "selected" else 1
    except (OSError, ValueError, KeyError, TypeError, OverflowError, ImportError, AttributeError) as exc:
        parser.exit(2, f"Threshold selection failed: {exc}\nRAW and previous experiments were preserved.\n")


if __name__ == "__main__":
    raise SystemExit(main())
