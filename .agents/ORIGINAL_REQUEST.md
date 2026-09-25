# Original User Request

## Initial Request — 2026-09-24T22:47:18Z

This is a single self-contained feature; keep it small and focused.
Implement a modular, hardware-independent C++ presentation/execution layer for GestureOS AI: the multimode engine (ROBOT, SMART CONTROL, PRESENTATION, GAME, MACRO, CUSTOM) and the gesture sequence/macro engine with temporal timeouts.

Working directory: /home/ibrahim-tomota/Documents/Codex/2026-09-24/tu
Integrity mode: development

## Requirements

### R1. Multimode State Machine (`firmware/src/modes.*`)
Implement an extensible mode manager handling the 6 operating modes defined in project specifications:
- `ROBOT`: maps directional gestures (LEFT, RIGHT, UP, DOWN, CIRCLE) to motor/servo intent.
- `SMART_CONTROL`: maps gestures to home automation actions (LED ON/OFF, RELAY ON/OFF, ALARM).
- `PRESENTATION`: maps gestures to navigation actions (NEXT, PREV, FIRST, LAST, ACTION).
- `GAME`: handles reactive challenges and score tracking with timed gestures.
- `MACRO`: routes recognized sequences to composite macros.
- `CUSTOM`: allows user-configurable bindings.
In all modes, `UNKNOWN` or rejected gestures must never trigger any action or actuator command.

### R2. Macro and Sequence Engine (`firmware/src/macro_engine.*`)
Implement a robust state machine recognizing ordered gesture sequences (e.g., `LEFT -> RIGHT -> CIRCLE` triggering `MACRO_01`):
- Configurable inter-gesture timeout window (resets if elapsed).
- Cancellation / abort handling on invalid transition or unexpected movement.
- Safe action dispatching upon full sequence completion.

### R3. Preservation and Non-Regression
- Do NOT modify any files in `data/raw/`, `data/pending/`, or `data/session_notes/`.
- Preserve existing uncommitted user changes in `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py`, and `reports/hardware/`.
- Maintain full compatibility with PlatformIO compilation for both `esp32dev` and `dataset` environments.
- Ensure all 102 existing Python unit tests continue to pass without regression.

## Verification Resources

- Existing C++ test pattern: `tests/native/lcd_ui_test.cpp` and build artifact `work/lcd_ui_test`.
- Compilation commands:
  - C++ native tests: `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src ...`
  - ESP32 builds: `pio run -d firmware -e esp32dev` and `pio run -d firmware -e dataset`
  - Python tests: `.venv/bin/python -m unittest discover -s tests -v`

## Acceptance Criteria

### C++ Native Verification
- [ ] Comprehensive unit tests in `tests/native/` test all mode dispatches, UNKNOWN rejections, sequence timeouts, and state transitions.
- [ ] The native test binary compiles cleanly with `-Wall -Wextra -Werror -std=c++11` and exits with code 0.

### Firmware Compilation
- [ ] `pio run -d firmware -e esp32dev` succeeds with zero errors.
- [ ] `pio run -d firmware -e dataset` succeeds with zero errors.

### Project & Test Suite Integrity
- [ ] `.venv/bin/python -m unittest discover -s tests` runs and reports all 102 tests passing (OK).
- [ ] `git status` confirms that no raw data files were modified and preexisting user edits remain untouched.
