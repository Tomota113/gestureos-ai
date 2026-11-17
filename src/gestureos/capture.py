"""Collect bounded labelled IMU sequences without overwriting earlier captures."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

from . import __version__
from .protocol import CaptureParser, PATH_COMPONENT, PROTOCOL, ProtocolError, Request, message


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


class CaptureStore:
    def __init__(self, root, subject, session, request, *, source_kind="hardware"):
        if not all(PATH_COMPONENT.fullmatch(x) for x in (subject, session)):
            raise ValueError("Subject/session IDs must be 1..64 letters, digits, underscores or hyphens")
        if source_kind not in ("hardware", "synthetic_test"):
            raise ValueError("Unknown data provenance")
        self.request = request
        self.source_kind = source_kind
        self.path = Path(root) / subject / session / request.capture_id
        self.path.mkdir(parents=True, exist_ok=False)
        self.raw = None
        write_json(self.path / "request.json", {
            "schema_version": 1, "tool_version": __version__, "created_utc": utc_now(),
            "capture_id": request.capture_id, "label": request.label,
            "subject_id": subject, "session_id": session,
            "requested_samples": request.samples, "sample_rate_hz": request.rate_hz,
            "source_kind": source_kind, "protocol": PROTOCOL,
            "preprocessing": "none", "calibration": "none",
        })
        self.raw = (self.path / "serial.raw").open("xb")
        self.digest = hashlib.sha256()

    def record(self, raw):
        self.raw.write(raw)
        self.raw.flush()
        self.digest.update(raw)

    def close_raw(self):
        if self.raw and not self.raw.closed:
            self.raw.flush()
            os.fsync(self.raw.fileno())
            self.raw.close()

    def finish(self, parser, error=None):
        self.close_raw()
        success = error is None and parser is not None and parser.complete
        result = {"schema_version": 1, "finished_utc": utc_now(),
                  "status": "complete" if success else "incomplete",
                  "eligible_for_training": success and self.source_kind == "hardware",
                  "source_kind": self.source_kind, "error": error,
                  "raw_sha256": self.digest.hexdigest()}
        if success:
            staging = self.path / "samples.csv.partial"
            with staging.open("x", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["seq", "timestamp_us", "ax_g", "ay_g", "az_g",
                                 "gx_dps", "gy_dps", "gz_dps", "i2c_errors"])
                writer.writerows(parser.rows)
                csv_file.flush()
                os.fsync(csv_file.fileno())
            # Hard-link creation is atomic and fails if the destination exists.
            os.link(staging, self.path / "samples.csv")
            staging.unlink()
            result["metrics"] = parser.metrics
            result["device_begin"] = parser.begin
        write_json(self.path / "result.json", result)
        return result


def read_record(device, store):
    raw = device.readline(1025)
    if raw:
        store.record(raw)
        if len(raw) > 1024:
            raise ProtocolError("Oversized serial frame")
    return raw


def receive_capture(device, request, store, *, countdown=0, clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + 10
    while clock() < deadline:
        raw = read_record(device, store)
        idx = raw.find(b"{")
        if idx == -1:
            continue  # Preserve ROM boot text; only READY opens the protocol.
        obj = message(raw[idx:])
        if obj.get("type") == "error":
            raise ProtocolError(f"Device initialization failed: {obj.get('reason')}")
        if obj.get("type") == "ready":
            if obj.get("protocol") != PROTOCOL or obj.get("rate_hz") != request.rate_hz:
                raise ProtocolError("Wrong firmware protocol/sample rate")
            break
    else:
        raise ProtocolError("No dataset-firmware READY within 10 seconds")

    for remaining in range(countdown, 0, -1):
        print(f"{request.label}: {remaining}...", file=sys.stderr, flush=True)
        sleep(1)
    command = request.command()
    if device.write(command) != len(command):
        raise ProtocolError("Capture command was not fully written")
    print(f"GO: {request.label}", file=sys.stderr, flush=True)
    parser = CaptureParser(request)
    deadline = clock() + request.samples / request.rate_hz + 5
    while clock() < deadline:
        raw = read_record(device, store)
        if not raw:
            continue
        parser.feed(raw)
        if parser.complete:
            return parser
    raise ProtocolError("Capture end missing before timeout")


def collect(port, store, *, countdown=3):
    import serial

    device = serial.Serial(port=None, baudrate=230400, timeout=.2, write_timeout=2, exclusive=True)
    device.port = port
    device.dtr = False
    device.rts = False
    parser = None
    problem = None
    try:
        device.open()
        device.rts = True
        time.sleep(.1)
        device.reset_input_buffer()
        device.rts = False
        parser = receive_capture(device, store.request, store, countdown=countdown)
    except (OSError, ValueError, KeyboardInterrupt) as exc:
        problem = "User interrupted capture" if isinstance(exc, KeyboardInterrupt) else str(exc)
        if device.is_open:
            try:
                device.write(b"ABORT\n")
            except (OSError, ValueError):
                pass
    finally:
        device.close()
        store.close_raw()
    return store.finish(parser, problem)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--subject", required=True, help="Pseudonymous participant ID")
    parser.add_argument("--session", required=True, help="New ID for each recording session")
    parser.add_argument("--label", required=True)
    parser.add_argument("--config", type=Path, default=Path("configs/collection.json"))
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--samples", type=int)
    parser.add_argument("--countdown", type=int)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text())
        if config["protocol"] != PROTOCOL or config["baudrate"] != 230400:
            raise ValueError("Unsupported protocol or baudrate in config")
        if args.label not in config["labels"]:
            raise ValueError("Label is not in the approved collection taxonomy")
        count = args.samples if args.samples is not None else config["samples_per_capture"]
        countdown = args.countdown if args.countdown is not None else config["countdown_seconds"]
        if type(countdown) is not int or not 0 <= countdown <= 10:
            raise ValueError("Countdown must be 0..10 seconds")
        request = Request(uuid.uuid4().hex, args.label, count, config["sample_rate_hz"])
        store = CaptureStore(args.root, args.subject, args.session, request)
        result = collect(args.port, store, countdown=countdown)
        print(json.dumps({"directory": str(store.path), **result}, indent=2))
        return 0 if result["status"] == "complete" else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Capture failed: {exc}\nExisting files were not overwritten.\n")


if __name__ == "__main__":
    raise SystemExit(main())
