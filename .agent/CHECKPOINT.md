CHECKPOINT ID: M7-software-threshold-selection-verified
DATE: 2026-09-24

COMPLETED:
Validation-only threshold selector, CLI and experimental policy binding to model/manifest/validation IDs. Explicit constraints, observed-breakpoint search, known/unknown denominators and blocked outcomes. Guide and architecture updated. No real model trained, calibrated or deployed.

VERIFICATION:
98 Python tests OK (11 new M7); .venv/bin/python -m gestureos.select_thresholds --help OK; git diff --check OK. Evidence reports/m7-threshold-tests.txt. Tests use analytical scores and fake estimators, not real ML results. Firmware/hardware unchanged this milestone.

REAL STATE:
Last read-only inventory found 3 valid real swipe_left captures from 2 sessions. No full dataset or model. Existing 60-second bench report failed imu_init with zero samples. User will wire/test hardware later. No test-final scores or real UNKNOWN false-accept rates.

GIT/USER DATA:
Base 0396d1b. Keep preexisting capture.py/dataset.py/test_dataset.py edits and untracked reports/hardware outside M7 commit. Preserve all RAW/pending/notes.

ANTIGRAVITY:
Read-only review requested, but agy timed out awaiting authentication. User says they are connecting; no review content or quota result yet. Retry only on confirmation.

QUOTA:
Official latest check: 42% 5h used, 71% weekly used; no credit/reset consumed. These values are a snapshot.

SAFE TO RESUME: YES. See NEXT_ACTION.md.
