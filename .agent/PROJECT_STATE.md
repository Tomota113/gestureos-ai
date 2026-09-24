PROJECT: GestureOS AI
DATE: 2026-09-24
PHASE: M7-SOFTWARE complete; physical collection remains in progress.
STATUS: READY_FOR_NEXT_SOFTWARE_MILESTONE / REAL_ML_AND_HARDWARE_PENDING

COMPLETED:
M7 selects experimental UNKNOWN score/margin thresholds from frozen validation IDs only. It revalidates RAW snapshots, prepared data, manifest, trusted model and provenance, then scores only validation captures. Explicit false-accept and correct-accept constraints are required. Reports known/unknown denominators and blocks impossible or missing-class selections. Policy binds model, score convention, manifest and validation IDs; inference checks these bindings. No probability calibration, test evaluation or action authorization is implied.
M6 PC inference/rejection and earlier offline collection, preprocessing and RF/SVM/MLP training infrastructure remain in place.

TESTED:
.venv/bin/python -m unittest discover -s tests -v: 98 tests OK, including 11 M7 tests with analytical scores/fake estimators, no classifier fit on fixtures. CLI help and git diff --check OK. Evidence: reports/m7-threshold-tests.txt. No firmware build/flash or physical test in M7.

REAL DATA AND HARDWARE:
Last read-only inventory: 3 valid swipe_left captures from 2 sessions. Rescan before training; current labels/groups are insufficient. No real gesture model, ML score, rejection rate or selected threshold exists. The retained 60-second bench report reports passed:false, imu_init and zero samples; shorter valid captures do not establish long-run stability. ESP32-D0WDQ6/4 MB/CP2102 and 16-pin LCD identified. Wiring and further physical checks will be done later per user.

USER CHANGES:
Preexisting uncommitted src/gestureos/capture.py, src/gestureos/dataset.py, tests/test_dataset.py and untracked reports/hardware/ remain intact and excluded from M7 commit. RAW, pending and session notes were not overwritten.

LIMITATIONS/NEXT:
Collect balanced real known and unknown captures across disjoint groups, create verified manifest/prepared data, train a real baseline, then set explicit threshold objectives and run M7. Keep final test untouched until development is fixed. Continuous-stream false triggers, segmentation, embedded inference, LCD/actions and long physical bench remain pending. No quota reset/credit purchase.

ANTIGRAVITY:
User requested collaboration. The read-only agy review requested OAuth authorization; the supplied code 1 was rejected as malformed (invalid_grant). No advice was received, and no quota conclusion follows. Retry after successful browser login confirmation, without concurrent edits.

QUOTA:
Official Codex check near M7 completion: 42% used in 5h window (58% remaining), 71% weekly used. No reset consumed. These values may change.
