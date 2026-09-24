"""Diagnose one verified real capture with a trusted local PC model; no actions."""
import argparse
from pathlib import Path

from .capture import write_json
from .dataset import fingerprint, load_capture, read_object, require
from .inference import load_baseline
from .rejection import validate_policy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True, type=Path, help="Trusted local experiment directory")
    parser.add_argument("--model", required=True, choices=("random_forest", "svm", "mlp"))
    parser.add_argument("--raw-root", required=True, type=Path)
    parser.add_argument("--capture", required=True, type=Path, help="Capture directory inside RAW root")
    parser.add_argument("--policy", type=Path, default=Path("configs/rejection.json"))
    parser.add_argument("--output", required=True, type=Path, help="New diagnostic event JSON")
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "Output already exists")
        root, experiment = args.raw_root.resolve(), args.experiment.resolve()
        require(not args.output.resolve().is_relative_to(root)
                and not args.output.resolve().is_relative_to(experiment),
                "Output must be outside RAW and experiment directories")
        policy_bytes = args.policy.read_bytes()
        policy = read_object(policy_bytes)
        validate_policy(policy)
        baseline = load_baseline(experiment, args.model)
        # Absolute path without resolving child symlinks: load_capture must detect them.
        entry, rows = load_capture(args.capture.absolute(), root, baseline.contract["labels"], include_rows=True)
        baseline.guard_final_test(entry)
        event = baseline.predict_rows(rows, policy)
        event.update({"purpose": "pc_diagnostic", "capture_id": entry["capture_id"],
                      "source_kind": entry["source_kind"], "capture_file_sha256": entry["file_sha256"],
                      "policy": policy, "policy_sha256": fingerprint(policy_bytes), "model": args.model})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, event)
        print(f"{event['decision']}: {event['label']} -> {args.output}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, OverflowError, ImportError, AttributeError) as exc:
        parser.exit(2, f"Inference refused: {exc}\nNo hardware action was sent.\n")


if __name__ == "__main__":
    raise SystemExit(main())
