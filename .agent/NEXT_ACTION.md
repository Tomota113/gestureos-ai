CURRENT: M9 software complete in commit 786271e; 102 Python tests OK. Read AGENT_STATE.md first on continuation.

1. Preserve existing user changes in capture.py, dataset.py, test_dataset.py and reports/hardware/.
2. Antigravity read-only review now works with `--mode plan --effort low` and `view_file`/`grep_search` only. M9 review received; see reports/m9-antigravity-review.md. Do not enable blanket auto-approval.
3. When sufficient real captures and disjoint groups exist, compare baseline vs optional train-only rotation on the same split. Do not claim an improvement before measurement. Keep final test reserved.
4. Physical pending: repeat failed 60-second IMU bench and verify LCD controller, levels and pin mapping after user wiring; no automatic flash.
5. Update PROJECT_STATE.md, NEXT_ACTION.md, CHECKPOINT.md and AGENT_STATE.md before long operations and at session end.

AGY FIXED 2026-09-24: targeted review succeeded; no global permission change. Next independent work: assess real capture sufficiency before ML comparison; keep test reserved.

6. Maintain AGENT_STATE.md after every major completed task and before stopping; keep the first unfinished action explicit.
