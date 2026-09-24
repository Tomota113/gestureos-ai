"""Capture/check an UNLABELLED MPU6050 bench stream, never a gesture dataset."""
import argparse
import json
import math
from pathlib import Path
import statistics
import time

HEADER = "seq,timestamp_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,i2c_errors"


def parse_row(line):
    fields = line.strip().split(",")
    if len(fields) != 9:
        raise ValueError("Expected 9 columns")
    seq, timestamp = int(fields[0]), int(fields[1])
    axes = tuple(float(value) for value in fields[2:8])
    errors = int(fields[8])
    if min(seq, timestamp, errors) < 0 or not all(map(math.isfinite, axes)):
        raise ValueError("Negative counter or non-finite axis")
    return seq, timestamp, axes, errors


def analyze(lines, rate_hz=100, min_seconds=60):
    rows, issues = [], []
    started = False
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if line == HEADER:
            if started:
                issues.append(f"line {number}: repeated header / device reset")
            started = True
        elif line.startswith("#"):
            if line.startswith("# ERROR"):
                issues.append(f"line {number}: {line}")
        elif started and line:
            try:
                rows.append(parse_row(line))
            except ValueError:
                issues.append(f"line {number}: invalid data")
    if not started or len(rows) < 2:
        return {"passed": False, "samples": len(rows),
                "issues": issues + ["Missing header or fewer than two samples"]}

    intervals = [b[1] - a[1] for a, b in zip(rows, rows[1:])]
    sequence_gaps = sum(b[0] != a[0] + 1 for a, b in zip(rows, rows[1:]))
    if sequence_gaps:
        issues.append("Non-consecutive sequence numbers (loss/reset)")
    if any(value <= 0 for value in intervals):
        issues.append("Timestamps are not strictly increasing")
    duration = (rows[-1][1] - rows[0][1]) / 1e6
    measured_rate = (len(rows) - 1) / duration if duration > 0 else 0
    period = 1e6 / rate_hz
    within_tolerance = sum(abs(dt - period) <= .2 * period for dt in intervals) / len(intervals)
    i2c_errors = max(row[3] for row in rows)
    saturated_samples = sum(any(abs(v) >= limit for v, limit in
                                zip(row[2], (3.96,) * 3 + (495,) * 3)) for row in rows)
    if duration < min_seconds:
        issues.append("Capture is shorter than the required sensor-time duration")
    if abs(measured_rate - rate_hz) > .02 * rate_hz:
        issues.append("Mean sample rate outside +/-2 percent")
    if within_tolerance < .95 or max(intervals) > 2 * period:
        issues.append("Timing jitter/gaps exceed bench acceptance limits")
    if i2c_errors:
        issues.append("Firmware reported I2C errors")
    if saturated_samples:
        issues.append("Axis near configured full scale; review sensor range")
    return {
        "passed": not issues, "scope": "bench stream integrity only, not ML accuracy",
        "samples": len(rows), "duration_sensor_s": duration,
        "expected_rate_hz": rate_hz, "measured_rate_hz": measured_rate,
        "interval_us_min": min(intervals), "interval_us_max": max(intervals),
        "interval_us_median": statistics.median(intervals),
        "fraction_intervals_within_20_percent": within_tolerance,
        "sequence_discontinuities": sequence_gaps, "i2c_errors": i2c_errors,
        "near_full_scale_samples": saturated_samples,
        "axis_means": [statistics.mean(row[2][axis] for row in rows) for axis in range(6)],
        "axis_std": [statistics.pstdev(row[2][axis] for row in rows) for axis in range(6)],
        "issues": issues,
    }


def capture(port, output, seconds):
    import serial

    # Exclusive creation protects any previously collected bench data.
    with output.open("xb") as raw_file:
        with serial.Serial(port, 230400, timeout=.2, exclusive=True) as device:
            device.dtr = False
            device.rts = True
            time.sleep(.1)
            device.reset_input_buffer()
            device.rts = False
            deadline = time.monotonic() + seconds + 15
            first_timestamp = None
            header_seen = False
            while time.monotonic() < deadline:
                raw = device.readline()
                if not raw:
                    continue
                raw_file.write(raw)
                raw_file.flush()
                line = raw.decode("ascii", errors="replace").strip()
                if line == HEADER:
                    header_seen = True
                    continue
                if line.startswith("# ERROR"):
                    break
                if not header_seen or line.startswith("#"):
                    continue
                try:
                    _, stamp, _, _ = parse_row(line)
                except ValueError:
                    continue
                if first_timestamp is None:
                    first_timestamp = stamp
                if stamp - first_timestamp >= seconds * 1e6:
                    break


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--port", help="Real serial port; opening resets ESP32")
    source.add_argument("--input", type=Path, help="Existing smoke-test serial log")
    parser.add_argument("--output", type=Path, help="NEW raw log path for serial capture")
    parser.add_argument("--report", required=True, type=Path, help="NEW JSON report path")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--rate", type=int, choices=[50, 100], default=100)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("--seconds must be finite and positive")
    if args.port and not args.output:
        parser.error("--port requires --output")
    if args.report.exists() or (args.port and args.output.exists()):
        parser.error("Output already exists; choose a new name")
    try:
        if args.port:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            capture(args.port, args.output, args.seconds)
        source_path = args.output if args.port else args.input
        result = analyze(source_path.read_text(errors="replace").splitlines(),
                         args.rate, args.seconds)
        result["source"] = str(source_path)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x") as report:
            json.dump(result, report, indent=2)
            report.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Capture/check failed: {exc}\nRaw output, if created, was retained.\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
