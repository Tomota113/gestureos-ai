"""Artificial protocol fixtures only: these are NOT collected sensor data."""
import unittest
from scripts.check_stream import HEADER, analyze


def fixture(count=101):
    return [HEADER] + [f"{i},{i * 10000},0,0,1,0,0,0,0" for i in range(count)]


class StreamTest(unittest.TestCase):
    def test_regular_stream(self):
        result = analyze(fixture(), min_seconds=1)
        self.assertTrue(result["passed"])
        self.assertEqual(result["measured_rate_hz"], 100)

    def test_dropped_serial_frame(self):
        lines = fixture()
        del lines[50]
        self.assertFalse(analyze(lines, min_seconds=1)["passed"])

    def test_missing_startup_frames_even_with_full_duration(self):
        lines = [HEADER] + [f"{i},{i * 10000},0,0,1,0,0,0,0" for i in range(1, 102)]
        result = analyze(lines, min_seconds=1)
        self.assertEqual(result["duration_sensor_s"], 1)
        self.assertEqual(result["first_sequence"], 1)
        self.assertFalse(result["passed"])

    def test_sensor_gap_despite_contiguous_serial_sequence(self):
        lines = [HEADER] + [f"{i},{i * 10000 + (30000 if i >= 50 else 0)},0,0,1,0,0,0,0"
                            for i in range(101)]
        self.assertFalse(analyze(lines, min_seconds=1)["passed"])

    def test_reboot(self):
        self.assertFalse(analyze(fixture() + fixture(), min_seconds=1)["passed"])

    def test_corruption_nonfinite_short_and_missing_header(self):
        for invalid in [fixture() + ["garbage"],
                        fixture() + ["101,1010000,nan,0,1,0,0,0,0"],
                        fixture(10), fixture()[1:]]:
            with self.subTest(invalid=invalid[-1]):
                self.assertFalse(analyze(invalid, min_seconds=1)["passed"])

    def test_i2c_errors_and_clipping(self):
        for row in ["101,1010000,0,0,1,0,0,0,1", "101,1010000,4,0,1,0,0,0,0",
                    "# ERROR imu_not_ready"]:
            self.assertFalse(analyze(fixture() + [row], min_seconds=1)["passed"])


if __name__ == "__main__":
    unittest.main()
