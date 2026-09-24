CHECKPOINT ID: M9-train-only-rotation-software-verified
DATE: 2026-09-24

COMPLETED: Optional post-split train-only sensor-frame Z rotation, bounded to at most 5 degrees and disabled by default. Both acceleration including gravity and gyroscope rotate consistently. Child records carry parent capture IDs; frozen scaler remains fit on original train captures. Validation, test and RAW are unchanged. Configuration and lineage saved per experiment.

TESTED: .venv/bin/python -m unittest discover -s tests : 102 tests OK. git diff --check : clean. Test estimators are fakes; no real model was fit.

ANTIGRAVITY: Read-only M9 review attempted with agy --mode plan. Headless command permission auto-denied; no review output. Not a quota finding. No blanket auto-approval used.

REAL STATE: Last read-only inventory had three swipe_left captures over two sessions. No real gesture model or ML score. Long IMU bench remains failed (imu_init). LCD 16-pin untested physically; wiring later per user.

USER DATA: Preserve preexisting uncommitted src/gestureos/capture.py, src/gestureos/dataset.py, tests/test_dataset.py and untracked reports/hardware/; none belongs to M9. RAW/pending/notes untouched.

QUOTA: Official latest check during M9: 84% 5h used, 78% weekly used; no reset or credit consumed. Snapshot may change.

SAFE TO RESUME: YES. Read AGENT_STATE.md and NEXT_ACTION.md.
