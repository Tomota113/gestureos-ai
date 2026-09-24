"""Validate RAW captures and save a grouped split without modifying RAW files."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from .capture import write_json
from .dataset import fingerprint, read_object, scan
from .split import grouped_split


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--config", type=Path, default=Path("configs/collection.json"))
    parser.add_argument("--output", required=True, type=Path, help="New JSON manifest path")
    parser.add_argument("--group-by", choices=("session", "subject"), default="session")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Manifest already exists; choose a new path")
        if args.output.resolve().is_relative_to(args.root.resolve()):
            raise ValueError("Manifest must be outside RAW directory")
        config_bytes = args.config.read_bytes()
        labels = read_object(config_bytes)["labels"]
        if (not isinstance(labels, list) or not labels or not all(isinstance(x, str) for x in labels)
                or len(set(labels)) != len(labels)):
            raise ValueError("Taxonomy must contain unique string labels")
        entries, rejected = scan(args.root, labels)
        result = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
                  "raw_root": str(args.root.resolve()), "config_sha256": fingerprint(config_bytes),
                  "labels": labels, "captures": entries, "rejected": rejected,
                  "split": None, "status": "blocked", "group_by": args.group_by, "seed": args.seed}
        try:
            if rejected:
                raise ValueError(f"{len(rejected)} invalid or duplicate captures; review before splitting")
            result["split"] = grouped_split(entries, labels, group_by=args.group_by, seed=args.seed)
            result["status"] = "ready"
        except ValueError as exc:
            result["reason"] = str(exc)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, result)
        print(json.dumps({"manifest": str(args.output), "status": result["status"],
                          "captures": len(entries), "rejected": len(rejected),
                          "reason": result.get("reason")}, indent=2))
        return 0 if result["status"] == "ready" else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Preparation failed: {exc}\nRAW files were not modified.\n")


if __name__ == "__main__":
    raise SystemExit(main())
