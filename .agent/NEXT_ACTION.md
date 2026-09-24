CURRENT: M7 software is implemented and 98 tests pass. See .agent/PROJECT_STATE.md and reports/m7-threshold-tests.txt.

1. At resumption, read .agent/PROJECT_STATE.md, NEXT_ACTION.md, CHECKPOINT.md, decisions.md; inspect git status and last five commits. Preserve the existing user collection edits and hardware reports.
2. After the user confirms successful browser OAuth login, request one bounded independent read-only Antigravity review of M7 using only verified CLI options. Do not allow concurrent repository edits. A network/auth/config error is not evidence of quota exhaustion. Stop provider calls if its quota is actually exhausted.
3. Incorporate actionable review findings and re-run relevant checks. Otherwise report the unavailable review plainly; never invent its advice.
4. Continue real collection offline as the user chooses. Rescan the actual RAW and preserve pending/original captures. Do not run a real baseline/threshold selection until the labels and disjoint groups support it. Explicitly set acceptable validation constraints; leave the final test reserved.
5. Hardware validations remain separate: repeat 60-second bench, characterize axes/bias/fixation, then LCD16/actuators. No automatic flash or repeated wiring questions during software work.
6. Update all three checkpoint files before long operations, after significant tests, and before session end. No invented ML performance or quotas; no paid credits/account changes.
