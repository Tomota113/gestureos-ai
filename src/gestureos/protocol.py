"""Strict parsing of one bounded capture, including CRC of transmitted frames."""
from dataclasses import dataclass
import json
import math
import re
import statistics
import zlib

PROTOCOL = "gestureos-capture-v1"
LABEL = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
IDENTIFIER = re.compile(r"[0-9a-f]{32}\Z")
PATH_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Request:
    capture_id: str
    label: str
    samples: int = 200
    rate_hz: int = 100

    def __post_init__(self):
        if not IDENTIFIER.fullmatch(self.capture_id):
            raise ValueError("capture_id must be 32 lowercase hexadecimal characters")
        if not LABEL.fullmatch(self.label):
            raise ValueError("Invalid gesture label")
        if type(self.samples) is not int or not 50 <= self.samples <= 500:
            raise ValueError("Capture length must be 50..500 samples")
        if self.rate_hz not in (50, 100):
            raise ValueError("Supported sample rates: 50 or 100 Hz")

    def command(self):
        return f"CAPTURE {self.capture_id} {self.label} {self.samples}\n".encode("ascii")


def message(raw):
    try:
        result = json.loads(raw.decode("ascii"))
    except (ValueError, UnicodeError) as exc:
        raise ProtocolError("Invalid JSON/ASCII message") from exc
    if not isinstance(result, dict):
        raise ProtocolError("Expected a JSON object")
    return result


class CaptureParser:
    def __init__(self, request):
        self.request = request
        self.begin = None
        self.rows = []
        self.crc = 0
        self.complete = False
        self.metrics = None

    def feed(self, raw):
        if self.complete:
            raise ProtocolError("Unexpected data after capture end")
        if len(raw) > 1024 or not raw.endswith(b"\n"):
            raise ProtocolError("Oversized or incomplete frame")
        if raw.startswith(b"D,"):
            self._sample(raw)
            return
        obj = message(raw)
        kind = obj.get("type")
        if kind == "error":
            raise ProtocolError(f"Device error: {obj.get('reason', 'unspecified')}")
        if kind == "begin" and self.begin is None:
            self._begin(obj)
        elif kind == "end" and self.begin is not None:
            self._end(obj)
        else:
            raise ProtocolError(f"Unexpected {kind!r} message (possible reset)")

    def _begin(self, obj):
        expected = {"protocol": PROTOCOL, "capture_id": self.request.capture_id,
                    "label": self.request.label, "samples": self.request.samples,
                    "rate_hz": self.request.rate_hz, "accel_unit": "g",
                    "gyro_unit": "deg_s", "calibrated": False,
                    "accel_range_g": 4, "gyro_range_dps": 500}
        if any(type(obj.get(k)) is not type(v) or obj.get(k) != v for k, v in expected.items()):
            raise ProtocolError("Capture identity, units or sensor configuration mismatch")
        self.begin = obj

    def _sample(self, raw):
        if self.begin is None:
            raise ProtocolError("Sample before begin")
        try:
            parts = raw.decode("ascii").strip().split(",")
            if len(parts) != 10:
                raise ValueError("Expected 10 columns")
            seq, timestamp = int(parts[1]), int(parts[2])
            axes = [float(x) for x in parts[3:9]]
            errors = int(parts[9])
        except (ValueError, UnicodeError) as exc:
            raise ProtocolError("Malformed sample") from exc
        if seq != len(self.rows) or seq >= self.request.samples:
            raise ProtocolError("Missing, duplicate or excess sample")
        if timestamp < 0 or (self.rows and timestamp <= self.rows[-1][1]):
            raise ProtocolError("Non-increasing device timestamp")
        if errors != 0:
            raise ProtocolError("I2C error reported")
        if not all(math.isfinite(x) for x in axes):
            raise ProtocolError("Non-finite axis")
        if any(abs(x) >= limit for x, limit in zip(axes, (3.96,) * 3 + (495,) * 3)):
            raise ProtocolError("Sensor near full scale; review physical range")
        self.rows.append([seq, timestamp, *axes, errors])
        self.crc = zlib.crc32(raw, self.crc)

    def _end(self, obj):
        if obj.get("capture_id") != self.request.capture_id:
            raise ProtocolError("Wrong capture ID at end")
        if (type(obj.get("samples")) is not int or obj["samples"] != self.request.samples
                or len(self.rows) != self.request.samples):
            raise ProtocolError("Incomplete capture")
        if obj.get("crc32") != f"{self.crc:08x}":
            raise ProtocolError("Serial frame CRC mismatch")
        dt = [b[1] - a[1] for a, b in zip(self.rows, self.rows[1:])]
        rate = (len(self.rows) - 1) * 1e6 / (self.rows[-1][1] - self.rows[0][1])
        period = 1e6 / self.request.rate_hz
        within = sum(abs(x - period) <= .2 * period for x in dt) / len(dt)
        if abs(rate - self.request.rate_hz) > .02 * self.request.rate_hz:
            raise ProtocolError("Capture sample rate outside +/-2 percent")
        if within < .95 or max(dt) > 2 * period:
            raise ProtocolError("Capture timing gaps/jitter exceed limits")
        self.metrics = {"samples": len(self.rows), "measured_rate_hz": rate,
                        "duration_sensor_s": (self.rows[-1][1] - self.rows[0][1]) / 1e6,
                        "interval_us_median": statistics.median(dt),
                        "interval_us_max": max(dt), "crc32": f"{self.crc:08x}"}
        self.complete = True
