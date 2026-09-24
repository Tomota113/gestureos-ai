CURRENT: M8 LCD1602 presentation software complete and compiled. See .agent/PROJECT_STATE.md and reports/m8-lcd-software-tests.txt.

1. On resume, read the four .agent files, inspect git status and the five latest commits. Preserve preexisting capture.py/dataset.py/test_dataset.py edits and reports/hardware/.
2. Do not call Antigravity for now; user explicitly requested work without it.
3. With quota available, inspect M5 train path and project augmentation requirements. Next bounded software candidate: safe train-only augmentation with capture lineage, after split, with physically justified transformations. No real ML comparison until dataset is adequate. Document precise scope before implementation; do not alter RAW or test/validation.
4. Before any real training or threshold selection, rescan real RAW and verify enough labels and disjoint groups. Keep final test untouched. No synthetic fixture is a performance result.
5. Physical pending: repeat the failed 60-second bench, characterize IMU, then verify 16-pin LCD controller/levels/pin mapping and implement its hardware adapter. User will connect later; do not ask again during software work or flash automatically.
6. Update PROJECT_STATE.md, NEXT_ACTION.md and CHECKPOINT.md before long operations, after significant tests and before session end. No quota guessing or paid credits/account changes.
