# Handoff Report: Multimode and Macro Engine Review & Defect Remediation (Pass 2)

> [!WARNING] **Skepticism Disclaimer**
> The state machine logic, boundary conditions, float NaN guards, memory clearing invariants, and mode dispatching are verified by 37 native test assertions and clean PlatformIO builds; however, true real-time FreeRTOS task latency and physical hardware actuator responses remain untested until physical sensors and servos are wired.

## 1. What the prior attempt got wrong

### Issue 1: `ModeManager::setMode(OperatingMode)` lacked enum bounds validation and `renderStatus()` read uninitialized stack memory
- **Input:** `manager.setMode(static_cast<OperatingMode>(99)); lcd_ui::Frame f = manager.renderStatus();`
- **Expected:** `setMode` returns `false` on out-of-range mode and preserves existing mode; `renderStatus()` and `dispatch()` have defensive `default:` handlers that safely output `"MODE UNKNOWN"` without reading uninitialized memory.
- **Actual:** `setMode` accepted any integer value unconditionally; in `renderStatus()`, `switch (mode_)` had no `default:` case, leaving `botBuf` uninitialized on the stack. `fillRow()` read arbitrary stack bytes into the LCD frame.
- **Root cause:** Missing bounds check in `setMode()` (`if (static_cast<uint8_t>(mode) > static_cast<uint8_t>(OperatingMode::Custom)) return false;`), and missing `default:` cases in `renderStatus()` and `dispatch()`.

### Issue 2: `GestureInput` confidence validation bypassed UNKNOWN/rejected guard on `NaN`
- **Input:** `GestureInput input(Gesture::Left, 0.0f / 0.0f, false); manager.dispatch(input);`
- **Expected:** Rejected as non-positive/invalid confidence (`actionTriggered = false`, `description = "REJECTED_INPUT"`).
- **Actual:** IEEE 754 comparison `input.confidence <= 0.0f` evaluated to `false` for `NaN`, allowing invalid inputs with NaN confidence to be dispatched as live actuator commands.
- **Root cause:** Guard checked `confidence <= 0.0f` instead of `!(input.confidence > 0.0f) || input.confidence > 1.0f`.

### Issue 3: `GameModeHandler::getCurrentChallenge()` leaked stale gesture after challenge completion or timeout
- **Input:** `game.startChallenge(Gesture::Right, 2000, 2000); game.handleGesture(Gesture::Right, 2500); game.getCurrentChallenge();`
- **Expected:** When `!game.isChallengeActive()`, `getCurrentChallenge()` returns `Gesture::Unknown`.
- **Actual:** `currentChallenge_` was not cleared, returning `Gesture::Right` indefinitely while the challenge was already inactive.
- **Root cause:** `currentChallenge_` was not reset to `Gesture::Unknown` upon challenge resolution, and `getCurrentChallenge()` did not check `challengeActive_`.

### Issue 4: `GameModeHandler::startChallenge` accepted `durationMs == 0`, creating non-expiring inactive challenges
- **Input:** `game.startChallenge(Gesture::Right, 0, 1000);`
- **Expected:** Rejected (`isChallengeActive() == false`).
- **Actual:** Challenge became active with `challengeDurationMs_ = 0`, but because timeout checks evaluated `if (challengeDurationMs_ > 0)`, it never expired in `update()` while `getTimeRemainingMs()` reported 0.
- **Root cause:** Missing `durationMs == 0` validation guard in `startChallenge`.

### Issue 5: `GameModeHandler::reset(0)` with 0 initial lives initialized in a non-game-over state
- **Input:** `game.reset(0);`
- **Expected:** `game.isGameOver() == true`.
- **Actual:** `gameOver_` remained `false` despite player having 0 lives.
- **Root cause:** `reset(initialLives)` unconditionally assigned `gameOver_ = false`.

### Issue 6: `MacroEngine::clearMacros()` left stale buffer and timestamp state intact
- **Input:** `engine.feed(Gesture::Left, 1000); engine.clearMacros(); engine.getCurrentBuffer()[0];`
- **Expected:** Complete wipe of macros, buffer, and timing state (`buffer_[0] == Gesture::Unknown`, `lastGestureTimeMs_ == 0`).
- **Actual:** `clearMacros()` only reset `macroCount_ = 0; currentStep_ = 0;`, leaving dirty sequence buffer and stale timestamps in memory.
- **Root cause:** Missing `memset(buffer_, 0, sizeof(buffer_));`, `lastGestureTimeMs_ = 0;`, and `memset(macros_, 0, sizeof(macros_));` in `clearMacros()`.

### Issue 7: `MacroEngine::unregisterMacro()` left orphaned in-progress sequences
- **Input:** Register macro `Left -> Right`. Feed `Left`. Call `unregisterMacro(id)`.
- **Expected:** State machine resets to idle (`isInSequence() == false`) since no remaining macro matches the active candidate sequence.
- **Actual:** `currentStep_` remained 1 and `buffer_[0]` remained `Left`, leaving the engine stuck waiting for an unregistered macro.
- **Root cause:** `unregisterMacro` did not verify whether any remaining macro still matched `buffer_` up to `currentStep_`.

### Issue 8: `MacroEngine::registerMacro` and `CustomModeHandler::bindGesture` accepted out-of-range gesture enum values
- **Input:** Register sequence with `static_cast<Gesture>(99)` or bind `static_cast<Gesture>(99)`.
- **Expected:** Call rejected (`false`).
- **Actual:** Accepted into tables without validation.
- **Root cause:** Checks only validated `g != Gesture::Unknown` without checking upper bound `static_cast<uint8_t>(g) <= static_cast<uint8_t>(Gesture::Stop)`.

### Issue 9: `MacroEngine::update()` reported `expectedTotal = 0` during active sequence progress
- **Input:** Active candidate sequence in progress polled via `update(nowMs)`.
- **Expected:** `res.status == StepStatus::Progress` and `res.expectedTotal` reports minimum target length.
- **Actual:** Hardcoded `res.expectedTotal = 0`.
- **Root cause:** Missing `minExpected` computation in `update()`.

### Issue 10: `MacroEngine::feed()` underflowed on default `nowMs = 0` after an initial timed step
- **Input:** `feed(Gesture::Left, 1000); feed(Gesture::Right);` (omitted `nowMs`).
- **Expected:** Sequence progresses smoothly.
- **Actual:** `0 - 1000` underflowed to `4294966296 >= timeoutMs_`, causing a false timeout reset.
- **Root cause:** Missing check `if (nowMs == 0 && lastGestureTimeMs_ > 0) nowMs = lastGestureTimeMs_;`.

### Issue 11: `SmartControlModeHandler` lacked dedicated alarm silencing gesture without killing LED and Relay
- **Input:** Alarm triggered (`Gesture::Shake`), followed by `Gesture::Push`.
- **Expected:** Alarm is silenced (`SmartDevice::Alarm, DeviceState::Off`) while preserving LED and Relay states.
- **Actual:** `Gesture::Push` was ignored (`NO_ACTION`); only `Gesture::Stop` could silence alarm, but forced all other devices off.
- **Root cause:** Missing `Gesture::Push` handler for alarm reset in `SmartControlModeHandler`.

### Issue 12: `CustomModeHandler::clearBindings()` left stale pointers in memory
- **Input:** `custom.clearBindings();`
- **Expected:** Array memory zeroed to prevent dangling callbacks/userData pointers.
- **Actual:** Only reset `bindingCount_ = 0`.
- **Root cause:** Missing `memset(bindings_, 0, sizeof(bindings_));`.

---

## 2. What I changed

- **`firmware/src/macro_engine.cpp`**:
  - Added enum bounds check in `registerMacro` (`static_cast<uint8_t>(sequence[i]) <= static_cast<uint8_t>(Gesture::Stop)`).
  - Added active candidate prefix verification in `unregisterMacro` to automatically clear orphaned in-progress sequences.
  - Added complete buffer, timing, and macro definition memory zeroing in `clearMacros`.
  - Added omitted timestamp protection in `feed` (`if (nowMs == 0 && lastGestureTimeMs_ > 0) nowMs = lastGestureTimeMs_;`).
  - Added `minExpected` candidate calculation in `update` so `res.expectedTotal` accurately reflects the in-progress sequence target length.
- **`firmware/src/modes.cpp`**:
  - Added enum bounds check in `ModeManager::setMode`.
  - Added `default:` defensive fallbacks in `ModeManager::dispatch` and `ModeManager::renderStatus` (preventing uninitialized stack memory reads).
  - Enhanced `ModeManager::dispatch` input validation to guard against `NaN` and `confidence > 1.0f` (`!(input.confidence > 0.0f) || input.confidence > 1.0f`).
  - Added `Gesture::Push` alarm silencing handler in `SmartControlModeHandler`.
  - Added `durationMs == 0` rejection in `GameModeHandler::startChallenge`.
  - Added challenge clearing (`currentChallenge_ = Gesture::Unknown`) upon challenge resolution in `GameModeHandler`.
  - Updated `GameModeHandler::getCurrentChallenge()` to return `Gesture::Unknown` when challenge is inactive.
  - Updated `GameModeHandler::reset(initialLives)` to set `gameOver_ = (initialLives == 0)`.
  - Added gesture enum bounds validation in `CustomModeHandler::bindGesture`.
  - Added `memset(bindings_, 0, sizeof(bindings_));` in `CustomModeHandler::clearBindings`.
- **`tests/native/macro_engine_test.cpp`**:
  - Added Section 16: Out-of-range gesture enum registration rejection.
  - Added Section 17: Unregister macro orphaned sequence cleanup verification.
  - Added Section 18: `clearMacros()` complete state and memory wipe verification.
  - Added Section 19: Subsequent `feed()` with default `nowMs=0` underflow protection.
  - Added Section 20: `update()` valid `expectedTotal` reporting during active progress.
- **`tests/native/modes_test.cpp`**:
  - Added Section 13: Invalid mode rejection in `setMode`.
  - Added Section 14: Floating-point `NaN` and out-of-range confidence rejection.
  - Added Section 15: `GameMode` durationMs=0 rejection, challenge clearing, and `reset(0)`.
  - Added Section 16: `SmartControl` alarm silencing via `Gesture::Push`.
  - Added Section 17: `CustomMode` out-of-range gesture rejection and `clearBindings` wipe.

---

## 3. Verification Record

- **Deep Verification (ran actual tests):**
  - **Native C++ Unit Tests (`-Wall -Wextra -Werror -std=c++11`):**
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/macro_engine_test.cpp firmware/src/macro_engine.cpp -o work/macro_engine_test && ./work/macro_engine_test`: Exit code 0, all 20 test sections passed.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/modes_test.cpp firmware/src/modes.cpp firmware/src/macro_engine.cpp firmware/src/lcd_ui.cpp -o work/modes_test && ./work/modes_test`: Exit code 0, all 17 test sections passed.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/lcd_ui_test.cpp firmware/src/lcd_ui.cpp -o work/lcd_ui_test && ./work/lcd_ui_test`: Exit code 0, LCD presentation tests passed.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/capture_protocol_test.cpp firmware/src/capture_protocol.cpp -o work/capture_protocol_test && ./work/capture_protocol_test`: Exit code 0, CRC32 and parser tests passed.
  - **Embedded PlatformIO Compilation:**
    - `pio run -d firmware -e esp32dev`: Exit code 0, SUCCESS (0 warnings, 0 errors, compiled with Xtensa GCC).
    - `pio run -d firmware -e dataset`: Exit code 0, SUCCESS (0 warnings, 0 errors).
  - **Python Test Suite Non-Regression:**
    - `.venv/bin/python -m unittest discover -s tests -v`: Ran all 102 tests in 5.507s, 100% OK.
  - **Repository & User Data Integrity:**
    - `git status` confirms no files in `data/raw/`, `data/pending/`, or `data/session_notes/` were touched.
    - Existing uncommitted user edits in `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py`, and `reports/hardware/` are completely preserved.
- **Shallow Verification (manual only):**
  - Formatted LCD row visual inspection for width constraints and null terminators.
- **Unverified aspects:**
  - Real hardware execution on a physical ESP32 connected to physical servos, relays, and LCD hardware (physical device not connected).
  - Physical FreeRTOS task context switching latency under concurrent high-rate IMU I2C polling.

---

## 4. Known Issues
- `Minor Robustness Risk` — If a macro sequence is configured with an inter-gesture timeout window smaller than typical human gesture transition duration (<300ms), transitions will abort due to timer expiry. Default is safely configured to 2000 ms.

---

## 5. Remaining risk & next step
- **Assessment:** All requirements R1, R2, and R3 are satisfied with exhaustive defensive programming against floating point anomalies (NaN), buffer overflows, memory leakage, uninitialized reads, orphaned sequences, and invalid enum values.
- **Next Step:** Ready for hardware actuator integration (`ModeActionListener` -> ESP32 LEDC PWM and GPIO drivers) once physical testing bench is wired by the user.
