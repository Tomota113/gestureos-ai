"""Read-only replay of a validated RAW capture through the native C++ engine."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from .dataset import load_capture, read_object

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def replay_rows(rows, config):
    compiler = shutil.which("g++")
    if compiler is None:
        raise ValueError("g++ is required for the native C++ replay")
    source = PROJECT_ROOT / "scripts/replay_engine.cpp"
    engine = PROJECT_ROOT / "firmware/src/gesture_engine.cpp"
    include = PROJECT_ROOT / "firmware/src"
    with tempfile.TemporaryDirectory(prefix="gestureos-replay-") as directory:
        executable = Path(directory) / "replay_engine"
        build = subprocess.run(
            [compiler, "-std=c++11", "-O2", "-Wall", "-Wextra", "-Werror",
             "-I", str(include), str(source), str(engine), "-o", str(executable)],
            capture_output=True, text=True, timeout=60, check=False)
        if build.returncode:
            raise ValueError(f"Native replay build failed: {build.stderr.strip()}")
        stream = "".join(" ".join(map(str, row[1:8])) + "\n" for row in rows)
        result = subprocess.run(
            [str(executable), *map(str, config)], input=stream,
            capture_output=True, text=True, timeout=30, check=False)
        if result.returncode:
            raise ValueError(f"Native replay failed: {result.stderr.strip()}")
        return [json.loads(line) for line in result.stdout.splitlines()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--config", type=Path, default=Path("configs/collection.json"))
    parser.add_argument("--capture", type=Path, required=True,
                        help="Capture directory under --root, or path relative to --root")
    for flag in ("start-energy", "stop-energy", "gyro-scale-dps"):
        parser.add_argument(f"--{flag}", type=float, required=True)
    for flag in ("min-samples", "max-samples", "quiet-samples",
                 "pre-roll-samples", "max-gap-us"):
        parser.add_argument(f"--{flag}", type=int, required=True)
    args = parser.parse_args()
    try:
        labels = read_object(args.config.read_bytes())["labels"]
        capture = args.capture if args.capture.is_absolute() else args.root / args.capture
        entry, rows = load_capture(capture, args.root, labels, include_rows=True)
        settings = [args.start_energy, args.stop_energy, args.gyro_scale_dps,
                    args.min_samples, args.max_samples, args.quiet_samples,
                    args.pre_roll_samples, args.max_gap_us]
        events = replay_rows(rows, settings)
        print(json.dumps({"status": "experimental_replay", "source_kind": "hardware",
                          "capture": entry["path"], "capture_id": entry["capture_id"],
                          "raw_sha256": entry["file_sha256"]["serial.raw"],
                          "config": dict(zip(("start_energy", "stop_energy", "gyro_scale_dps",
                                               "min_samples", "max_samples", "quiet_samples",
                                               "pre_roll_samples", "max_gap_us"), settings)),
                          "input_samples": len(rows), "events": events}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"Replay failed: {exc}\nCapture files were not modified.\n")


if __name__ == "__main__":
    raise SystemExit(main())
