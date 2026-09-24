"""CLI: verify a frozen manifest, interpolate IMU sequences and prepare features."""
import argparse
import json
from pathlib import Path

from .capture import write_json
from .dataset import read_object, require
from .manifest import load_manifest
from .preprocessing import prepare_partitions, validate_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--collection-config", type=Path, default=Path("configs/collection.json"))
    parser.add_argument("--config", type=Path, default=Path("configs/preprocessing.json"))
    parser.add_argument("--raw-root", type=Path, help="Relocated RAW root; hashes are still verified")
    parser.add_argument("--output", required=True, type=Path, help="New prepared dataset JSON")
    args = parser.parse_args()
    try:
        require(not args.output.exists(), "Output already exists; choose a new path")
        config = read_object(args.config.read_bytes())
        validate_config(config)
        loaded = load_manifest(args.manifest, args.collection_config, raw_root=args.raw_root)
        require(not args.output.resolve().is_relative_to(Path(loaded["raw_root"])),
                "Output must be outside RAW root")
        result = prepare_partitions(loaded, config)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, result)
        print(json.dumps({"output": str(args.output), "features": len(result["feature_names"]),
                          "points": config["target_points"],
                          "captures": {k: len(v) for k, v in result["partitions"].items()}}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        parser.exit(2, f"Preprocessing failed: {exc}\nRAW files were not modified.\n")


if __name__ == "__main__":
    raise SystemExit(main())
