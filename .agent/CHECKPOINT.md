CHECKPOINT ID: M13-read-only-replay-software-verified
DATE: 2026-09-25

COMPLETED: Read-only replay of fully revalidated RAW capture via the M12 C++ gesture engine. All thresholds explicitly supplied; open window at capture end reported. No label/model/action, no live IMU hookup. See outputs/replay-guide.md.

TESTED: 105 Python tests OK including 3 replay tests through the native C++ engine; PlatformIO esp32dev and dataset builds SUCCESS. Existing real capture replayed read-only with illustrative thresholds (200 samples, started then unfinished_at_end). See reports/m13-replay-software-tests.md. No physical run or flash.

REAL STATE: 3 valid swipe_left captures over 2 sessions at read-only scan, 0 rejected. No real model or ML score. IMU long bench failed with imu_init; LCD untested physically.

USER DATA: Existing uncommitted capture.py/dataset.py/test_dataset.py and reports/hardware/ preserved and excluded from M12 commit. RAW/pending/notes untouched.

ANTIGRAVITY: General handoff in ANTIGRAVITY_HANDOFF.md; self-validation if Codex quota becomes unavailable, no duplicate Codex verification per latest user preference.

QUOTA: Official latest check 22% 5h used, 83% weekly used; no reset/credit consumed. Snapshot may change.

SAFE TO RESUME: YES. Next step is new real captures / hardware when supplied by user; see AGENT_STATE.md and NEXT_ACTION.md.
