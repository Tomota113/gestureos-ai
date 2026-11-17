"""Read-only validation of original captures. No preprocessing or augmentation."""
import csv
import hashlib
import io
import json
from pathlib import Path

from .protocol import CaptureParser, PATH_COMPONENT, PROTOCOL, Request, message

COLUMNS = ["seq", "timestamp_us", "ax_g", "ay_g", "az_g",
           "gx_dps", "gy_dps", "gz_dps", "i2c_errors"]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def read_object(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    obj = json.loads(data, object_pairs_hook=unique,
                     parse_constant=lambda value: require(False, f"Invalid JSON number: {value}"))
    require(isinstance(obj, dict), "Expected JSON object")
    return obj


def load_capture(directory, root, labels, *, include_rows=False):
    directory, root = Path(directory), Path(root)
    relative = directory.relative_to(root)
    require(len(relative.parts) == 3, "Expected subject/session/capture_id layout")
    for path in (directory, directory.parent, directory.parent.parent):
        require(not path.is_symlink(), "Symlinked capture path")
    files = {}
    for name in ("request.json", "result.json", "serial.raw", "samples.csv"):
        path = directory / name
        require(not path.is_symlink() and path.is_file(), f"Missing or symlinked {name}")
        require(path.stat().st_size <= 1024 * 1024, f"Oversized {name}")
        files[name] = path.read_bytes()
    req, result = read_object(files["request.json"]), read_object(files["result.json"])
    for obj in (req, result):
        require(type(obj.get("schema_version")) is int and obj["schema_version"] == 1,
                "Unsupported schema version")
        require(obj.get("source_kind") == "hardware", "Synthetic or unknown provenance")
    require(result.get("status") == "complete" and result.get("eligible_for_training") is True
            and result.get("error") is None, "Incomplete or ineligible capture")
    require(req.get("preprocessing") == "none" and req.get("calibration") == "none"
            and req.get("protocol") == PROTOCOL, "Unsupported preprocessing/calibration/protocol")
    require(not any(k in req for k in ("parent_capture_id", "augmentation", "augmented_from")),
            "Derived samples must not be split as independent RAW captures")
    require((req.get("subject_id"), req.get("session_id"), req.get("capture_id")) == relative.parts,
            "Directory identity differs from metadata")
    require(all(PATH_COMPONENT.fullmatch(x) for x in relative.parts[:2]), "Invalid subject/session")
    require(req.get("label") in labels, "Label outside collection taxonomy")
    request = Request(req["capture_id"], req["label"], req["requested_samples"], req["sample_rate_hz"])
    raw = files["serial.raw"]
    require(result.get("raw_sha256") == fingerprint(raw), "RAW SHA256 mismatch")
    parser = CaptureParser(request)
    ready = False
    for line in raw.splitlines(keepends=True):
        if not ready:
            idx = line.find(b"{")
            if idx == -1:
                continue  # Retain the logger's ROM boot text allowance.
            obj = message(line[idx:])
            require(obj.get("type") == "ready" and obj.get("protocol") == PROTOCOL
                    and obj.get("rate_hz") == request.rate_hz, "Missing or inconsistent READY")
            ready = True
        else:
            parser.feed(line)
    require(parser.complete, "RAW capture has no valid end")
    require(result.get("device_begin") == parser.begin and result.get("metrics") == parser.metrics,
            "Stored result differs from revalidated RAW")
    rows = list(csv.reader(io.StringIO(files["samples.csv"].decode("utf-8"))))
    require(rows and rows[0] == COLUMNS and len(rows) == len(parser.rows) + 1,
            "CSV header or sample count mismatch")
    for actual, expected in zip(rows[1:], parser.rows):
        require(len(actual) == len(COLUMNS), "CSV column count mismatch")
        parsed = [int(actual[0]), int(actual[1]), *map(float, actual[2:8]), int(actual[8])]
        require(parsed == expected, "CSV values differ from RAW")
    # Ignore absolute device time and IDs so renamed copies still collide.
    origin = parser.rows[0][1]
    content = [[r[1] - origin, *r[2:8]] for r in parser.rows]
    entry = {"capture_id": request.capture_id, "label": request.label,
            "subject_id": req["subject_id"], "session_id": req["session_id"],
            "path": relative.as_posix(), "samples": request.samples,
            "rate_hz": request.rate_hz, "source_kind": "hardware",
            "file_sha256": {name: fingerprint(data) for name, data in files.items()},
            "content_sha256": fingerprint(json.dumps(content, separators=(",", ":")).encode())}
    # Return the exact validated snapshot, without rereading mutable CSV files.
    return (entry, parser.rows) if include_rows else entry


def scan(root, labels):
    root = Path(root)
    require(root.is_dir(), f"Dataset directory does not exist: {root}")
    entries, rejected = [], []
    for directory in sorted(root.glob("*/*/*")):
        if not directory.is_dir() and not directory.is_symlink():
            continue
        try:
            entries.append(load_capture(directory, root, labels))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            rejected.append({"path": directory.relative_to(root).as_posix(), "reason": str(exc)})
    duplicate_paths = set()
    for key in ("capture_id", "content_sha256"):
        groups = {}
        for entry in entries:
            groups.setdefault(entry[key], []).append(entry["path"])
        for paths in groups.values():
            if len(paths) > 1:
                duplicate_paths.update(paths)
    for path in sorted(duplicate_paths):
        rejected.append({"path": path, "reason": "Duplicate capture ID or signal content"})
    return [e for e in entries if e["path"] not in duplicate_paths], rejected
