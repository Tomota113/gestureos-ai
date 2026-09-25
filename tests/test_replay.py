"""Synthetic samples exercise the actual C++ replay bridge, not ML quality."""
import unittest

from gestureos.replay import replay_rows


class ReplayTest(unittest.TestCase):
    def test_events_and_completed_window_from_native_engine(self):
        gyro = [0, 0, 0, 100, 100, 30, 0, 0]
        rows = [[i, (i + 1) * 100, 0, 0, 1, value, 0, 0, 0]
                for i, value in enumerate(gyro)]
        events = replay_rows(rows, [0.5, 0.2, 100, 5, 8, 2, 2, 150])
        self.assertEqual([e["event"] for e in events], ["started", "completed"])
        self.assertEqual(events[1]["window_samples"], 7)
        self.assertEqual((events[1]["window_start_us"], events[1]["window_end_us"]),
                         (200, 800))

    def test_gap_and_bad_configuration_are_not_silently_accepted(self):
        rows = [[0, 100, 0, 0, 1, 0, 0, 0, 0],
                [1, 300, 0, 0, 1, 100, 0, 0, 0]]
        events = replay_rows(rows, [0.5, 0.2, 100, 5, 8, 2, 2, 150])
        self.assertEqual([e["event"] for e in events], ["invalid_sample"])
        with self.assertRaisesRegex(ValueError, "rejected configuration"):
            replay_rows(rows, [0.2, 0.5, 100, 5, 8, 2, 2, 150])

    def test_open_window_at_capture_end_is_explicit(self):
        rows = [[0, 100, 0, 0, 1, 100, 0, 0, 0],
                [1, 200, 0, 0, 1, 100, 0, 0, 0]]
        events = replay_rows(rows, [0.5, 0.2, 100, 5, 8, 2, 2, 150])
        self.assertEqual([e["event"] for e in events], ["started", "unfinished_at_end"])


if __name__ == "__main__":
    unittest.main()
