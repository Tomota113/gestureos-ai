"""Synthetic wire frames only; no physical sensor data or ML examples."""
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zlib

from gestureos.capture import CaptureStore, collect, receive_capture
from gestureos.protocol import CaptureParser, PROTOCOL, ProtocolError, Request

REQUEST = Request("0123456789abcdef0123456789abcdef", "swipe_left", 50)


def frame(obj):
    return json.dumps(obj, separators=(",", ":")).encode() + b"\n"


def fixture(request=REQUEST):
    begin = {"type": "begin", "protocol": PROTOCOL, "capture_id": request.capture_id,
             "label": request.label, "samples": request.samples, "rate_hz": request.rate_hz,
             "accel_unit": "g", "gyro_unit": "deg_s", "calibrated": False,
             "accel_range_g": 4, "gyro_range_dps": 500}
    rows = [f"D,{i},{1000000 + i * 10000},0.0000,0.0000,1.0000,0.0000,0.0000,0.0000,0\n".encode()
            for i in range(request.samples)]
    end = {"type": "end", "capture_id": request.capture_id, "samples": request.samples,
           "crc32": f"{zlib.crc32(b''.join(rows)):08x}"}
    return [frame(begin), *rows, frame(end)]


class FakeSerial:
    def __init__(self, lines=()):
        self.stream = io.BytesIO(b"".join(lines))
        self.commands = []
        self.is_open = False

    def readline(self, size):
        return self.stream.readline(size)

    def write(self, command):
        self.commands.append(command)
        return len(command)

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def reset_input_buffer(self):
        pass


class ParserTest(unittest.TestCase):
    def parse(self, lines):
        parser = CaptureParser(REQUEST)
        for line in lines:
            parser.feed(line)
        return parser

    def test_complete_capture_and_crc(self):
        parser = self.parse(fixture())
        self.assertTrue(parser.complete)
        self.assertEqual(parser.metrics["measured_rate_hz"], 100)

    def test_missing_duplicate_or_initial_frame(self):
        lines = fixture()
        for broken in (lines[:1] + lines[2:], lines[:4] + lines[5:],
                       lines[:5] + [lines[4]] + lines[5:]):
            with self.assertRaises(ProtocolError):
                self.parse(broken)

    def test_valid_numeric_corruption_fails_crc(self):
        lines = fixture()
        lines[3] = lines[3].replace(b"1.0000", b"1.1000")
        with self.assertRaisesRegex(ProtocolError, "CRC"):
            self.parse(lines)

    def test_wrong_identity_units_rate_and_count(self):
        for key, value in (("label", "swipe_right"), ("capture_id", "a" * 32),
                           ("accel_unit", "m_s2"), ("rate_hz", 50), ("samples", 49),
                           ("calibrated", 0)):
            lines = fixture()
            begin = json.loads(lines[0])
            begin[key] = value
            lines[0] = frame(begin)
            with self.subTest(key=key), self.assertRaises(ProtocolError):
                self.parse(lines)

    def test_reset_device_error_and_truncated_line(self):
        for bad in (frame({"type": "ready"}), frame({"type": "error", "reason": "i2c"}),
                    b"D,0,100", b"X" * 1025 + b"\n"):
            with self.assertRaises(ProtocolError):
                self.parse([fixture()[0], bad])

    def test_invalid_values(self):
        for value in ("nan", "inf", "4.0"):
            lines = fixture()
            lines[1] = lines[1].replace(b"1.0000", value.encode())
            with self.assertRaises(ProtocolError):
                self.parse(lines)

    def test_gap_even_with_correct_crc(self):
        lines = fixture()
        # Later timestamps shift; serial sequence and recomputed CRC remain valid.
        for i in range(25, 50):
            parts = lines[i + 1].split(b",")
            parts[2] = str(int(parts[2]) + 30000).encode()
            lines[i + 1] = b",".join(parts)
        end = json.loads(lines[-1])
        end["crc32"] = f"{zlib.crc32(b''.join(lines[1:-1])):08x}"
        lines[-1] = frame(end)
        with self.assertRaises(ProtocolError):
            self.parse(lines)

    def test_request_rejects_injection_and_bad_count(self):
        for label, count in (("../escape", 50), ("shake\nABORT", 50), ("shake", 501)):
            with self.assertRaises(ValueError):
                Request(REQUEST.capture_id, label, count)


class CaptureTest(unittest.TestCase):
    def setUp(self):
        Path("work").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir="work", prefix="synthetic-capture-test-")
        self.addCleanup(self.temp.cleanup)

    def store(self):
        store = CaptureStore(self.temp.name, "test_subject", "test_session", REQUEST,
                             source_kind="synthetic_test")
        self.addCleanup(store.close_raw)
        return store

    def ready_stream(self):
        return [b"ROM boot text\n", frame({"type": "ready", "protocol": PROTOCOL,
                                         "rate_hz": 100}), *fixture()]

    def test_full_host_flow_preserves_frames_and_provenance(self):
        store = self.store()
        lines = self.ready_stream()
        device = FakeSerial(lines)
        parser = receive_capture(device, REQUEST, store)
        result = store.finish(parser)
        self.assertEqual(result["status"], "complete")
        self.assertFalse(result["eligible_for_training"])
        self.assertEqual(device.commands, [REQUEST.command()])
        self.assertEqual((store.path / "serial.raw").read_bytes(), b"".join(lines))
        with (store.path / "samples.csv").open() as csv_file:
            self.assertEqual(len(list(csv.DictReader(csv_file))), 50)

    def test_existing_capture_never_overwritten(self):
        store = self.store()
        original = (store.path / "request.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.store()
        self.assertEqual((store.path / "request.json").read_bytes(), original)

    def test_disconnect_preserves_partial_and_marks_incomplete(self):
        store = self.store()
        device = FakeSerial(self.ready_stream()[:4])
        real_read = device.readline

        def disconnect(size):
            raw = real_read(size)
            if not raw:
                raise OSError("Disconnected (simulated)")
            return raw

        device.readline = disconnect
        with patch("serial.Serial", return_value=device), patch("gestureos.capture.time.sleep"):
            result = collect("FAKE", store, countdown=0)
        self.assertEqual(result["status"], "incomplete")
        self.assertFalse((store.path / "samples.csv").exists())
        self.assertTrue((store.path / "serial.raw").read_bytes())
        self.assertEqual(device.commands[-1], b"ABORT\n")

    def test_missing_ready_times_out_without_command(self):
        store = self.store()
        device = FakeSerial()
        ticks = iter(range(100))
        with self.assertRaisesRegex(ProtocolError, "READY"):
            receive_capture(device, REQUEST, store, clock=lambda: next(ticks))
        self.assertEqual(device.commands, [])

    def test_keyboard_interrupt_retains_log(self):
        store = self.store()
        device = FakeSerial()
        device.readline = lambda size: (_ for _ in ()).throw(KeyboardInterrupt())
        with patch("serial.Serial", return_value=device), patch("gestureos.capture.time.sleep"):
            result = collect("FAKE", store, countdown=0)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("interrupted", result["error"])
        self.assertTrue((store.path / "serial.raw").exists())


if __name__ == "__main__":
    unittest.main()
