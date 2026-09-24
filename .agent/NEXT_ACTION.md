CURRENT: M7 software and Antigravity review follow-up are complete; 100 tests pass. See .agent/PROJECT_STATE.md and reports/m7-threshold-tests.txt.

1. At resumption, read .agent/PROJECT_STATE.md, NEXT_ACTION.md, CHECKPOINT.md, decisions.md; inspect git status and last five commits. Preserve the existing user collection edits and hardware reports.
2. Review report: reports/m7-antigravity-review.md. Four findings were handled and the full Python suite passed. Do not repeat this completed provider review automatically.
3. Keep Antigravity read-only for any future bounded review and never permit concurrent edits. Stop provider calls if its quota is actually exhausted.
4. Continue real collection offline as the user chooses. Rescan the actual RAW and preserve pending/original captures. Do not run a real baseline/threshold selection until the labels and disjoint groups support it. Explicitly set acceptable validation constraints; leave the final test reserved.
5. Hardware validations remain separate: repeat 60-second bench, characterize axes/bias/fixation, then LCD16/actuators. No automatic flash or repeated wiring questions during software work.
6. Update all three checkpoint files before long operations, after significant tests, and before session end. No invented ML performance or quotas; no paid credits/account changes.
