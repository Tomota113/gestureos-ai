# Handoff Report: Multimode and Macro Engine Review & Defect Remediation (Pass 3)

> [!WARNING] **Skepticism Disclaimer**
> The state machine transitions, timeout rollovers, enum bounds guards, in-place update candidate validation, and timestamp omission handling are verified by 44 native assertions and dual-environment PlatformIO compilation; however, true FreeRTOS scheduler context switching jitter and physical actuator electrical dynamics remain unverified until physical bench testbeds are connected.

## 1. What the prior attempt got wrong

### Issue 1: `MacroEngine::registerMacro` in-place update orphaned active candidate sequence
- **Input:** Register macro `1` with `{Gesture::Left, Gesture::Right}`. Feed `feed(Gesture::Left, 1000)` (`isInSequence() == true`, `currentStep_ == 1`). Update macro `1` in-place via `registerMacro(1, "NEW", {Gesture::Up, Gesture::Down})`.
- **Expected:** State machine evaluates whether any macro still matches `buffer_` up to `currentStep_`. Finding no matching candidates starting with `Left`, resets state to idle (`isInSequence() == false`, `currentStep_ == 0`, buffer zeroed).
- **Actual:** `registerMacro` updated `macros_[i]` in-place without checking active candidate sequence validity. `currentStep_` remained 1 and `buffer_[0]` remained `Gesture::Left`, stranding the engine in an orphaned desynchronized sequence state.
- **Root cause:** Missing active candidate sequence prefix check in `MacroEngine::registerMacro` for in-place macro definition updates (unlike `unregisterMacro`).

### Issue 2: `ModeManager::dispatch` and `GameModeHandler::handleGesture` penalized player and triggered actions on out-of-range gesture enum
- **Input:** In `GAME` mode with an active challenge (target `Gesture::Right`), dispatch an out-of-range gesture enum: `manager.dispatch(GestureInput(static_cast<Gesture>(99), 1.0f, false))` or `manager.dispatch(static_cast<Gesture>(99))`.
- **Expected:** Rejected as an unknown/invalid gesture (`actionTriggered == false`, `description == "UNKNOWN_GESTURE"`). Challenge remains active, combo is preserved, lives are untouched, listener is NOT notified.
- **Actual:** `input.gesture == Gesture::Unknown` evaluated to `false` (99 != 0), bypassing the Unknown guard in `dispatch()`. Inside `GameModeHandler::handleGesture()`, it bypassed `gesture == Gesture::Unknown`, mismatched `currentChallenge_`, was treated as `GameEvent::WrongGesture`, deducted a player life (`--lives_`), reset combo to 0, terminated the challenge, set `actionTriggered = true`, and invoked `listener_->onGameAction(result.game)`.
- **Root cause:** Enum upper bound check (`static_cast<uint8_t>(g) > static_cast<uint8_t>(Gesture::Stop)`) was missing in `ModeManager::dispatch` and `GameModeHandler::handleGesture`. Corrupt or out-of-bounds enum values were processed as valid gestures, directly violating Requirement R1.

### Issue 3: `GameModeHandler::startChallenge` accepted out-of-range gesture enum
- **Input:** `game.startChallenge(static_cast<Gesture>(99), 2000, 1000);`
- **Expected:** Call rejected (`isChallengeActive() == false`, `getCurrentChallenge() == Gesture::Unknown`).
- **Actual:** Challenge became active with target gesture 99. Because gesture 99 is impossible to produce from classifier output, all subsequent player gestures resulted in penalized misses (`GameEvent::WrongGesture`).
- **Root cause:** Missing enum upper bound validation (`static_cast<uint8_t>(target) > static_cast<uint8_t>(Gesture::Stop)`) in `GameModeHandler::startChallenge`.

### Issue 4: `MacroEngine::feed` cancelled sequence on out-of-range gesture enum even when `abortOnUnknown_ == false`
- **Input:** `engine.setAbortOnUnknown(false); engine.feed(Gesture::Left, 1000); engine.feed(static_cast<Gesture>(99), 1200);`
- **Expected:** Out-of-range gesture treated as Unknown; with `abortOnUnknown_ == false`, it is ignored (`StepStatus::Ignored`, `actionTriggered == false`) and sequence progress is preserved (`isInSequence() == true`).
- **Actual:** Because `99 != Gesture::Unknown`, `feed()` entered the candidate matcher, found 0 matches, and triggered an invalid transition cancellation (`StepStatus::Cancelled`, `message = "INVALID_TRANSITION"`), destroying the in-progress sequence despite `abortOnUnknown_ == false`. At step 0, it reported `"NO_MATCHING_MACRO"` instead of `"UNKNOWN_IGNORED"`.
- **Root cause:** `MacroEngine::feed` checked `gesture == Gesture::Unknown` without checking `static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)`.

### Issue 5: `GameModeHandler::handleGesture` and `getTimeRemainingMs` underflowed on default `nowMs = 0`
- **Input:** `game.startChallenge(Gesture::Right, 2000, 5000); manager.dispatch(Gesture::Right);` (omitted `nowMs`, default 0).
- **Expected:** Successful challenge hit (`GameEvent::Success`, `scoreDelta = 100`, lives intact).
- **Actual:** `uint32_t elapsed = nowMs - challengeStartMs_` computed `0 - 5000 = 4294962296 >= 2000`, causing a false `GameEvent::TimeoutMiss` and life loss. In `getTimeRemainingMs(0)`, underflowed to elapsed > duration, returning 0 remaining time.
- **Root cause:** `GameModeHandler::handleGesture` and `getTimeRemainingMs` lacked fallback for omitted timestamps (`if (nowMs == 0 && challengeStartMs_ > 0) nowMs = challengeStartMs_;`).

### Issue 6: Mode handlers (`Robot`, `SmartControl`, `Presentation`, `Custom`) lacked defensive upper bound checks on gesture enums
- **Input:** `robot.handleGesture(static_cast<Gesture>(99))`, `smart.handleGesture(static_cast<Gesture>(99))`, `presentation.handleGesture(static_cast<Gesture>(99))`, `custom.handleGesture(static_cast<Gesture>(99))`.
- **Expected:** All return `"UNKNOWN_IGNORED"` with no action triggered.
- **Actual:** Returned `"NO_ACTION"` or `"NO_CUSTOM_BINDING"`.
- **Root cause:** Checked only `gesture == Gesture::Unknown` instead of also checking `static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)`.

### Issue 7: `ModeManager::renderStatus()` stack buffer margin
- Sized `char botBuf[32]` had narrow 1-byte margin for max `uint32_t` score/combo formatted strings. Expanded to 48 bytes for `topBuf` and `botBuf`.

---

## 2. What I changed

- **`firmware/src/macro_engine.cpp`**:
  - Added candidate prefix validation in `registerMacro` for in-place macro definition updates (`macros_[i].id == id`), cleaning up orphaned in-progress sequences if the updated definition alters matching prefixes.
  - Added gesture enum bounds guard in `feed` (`if (gesture == Gesture::Unknown || static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop))`), ensuring out-of-range gestures respect `abortOnUnknown_` configuration and return `"UNKNOWN_IGNORED"` when idle.
- **`firmware/src/modes.cpp`**:
  - Added enum bounds guard in `ModeManager::dispatch` (`static_cast<uint8_t>(input.gesture) > static_cast<uint8_t>(Gesture::Stop)`), blocking out-of-range gesture inputs from triggering actions or penalties.
  - Added enum bounds guard in `GameModeHandler::startChallenge` (`static_cast<uint8_t>(target) > static_cast<uint8_t>(Gesture::Stop)`).
  - Added enum bounds guard and omitted timestamp fallback (`if (nowMs == 0 && challengeStartMs_ > 0) nowMs = challengeStartMs_;`) in `GameModeHandler::handleGesture` and `GameModeHandler::getTimeRemainingMs`.
  - Added enum bounds guards in `RobotModeHandler::handleGesture`, `SmartControlModeHandler::handleGesture`, `PresentationModeHandler::handleGesture`, and `CustomModeHandler::handleGesture` returning `"UNKNOWN_IGNORED"`.
  - Expanded `topBuf` and `botBuf` in `ModeManager::renderStatus` to 48 bytes.
- **`tests/native/macro_engine_test.cpp`**:
  - Added Section 21: `registerMacro` in-place update candidate sequence orphan cleanup verification (Subcases A & B).
  - Added Section 22: Out-of-range gesture enum feeding verification across idle, `abortOnUnknown==false`, and `abortOnUnknown==true` modes.
- **`tests/native/modes_test.cpp`**:
  - Added Section 18: In-progress GameMode challenge with default `nowMs = 0` (omitted) verification against underflow.
  - Added Section 19: `GameModeHandler::startChallenge` out-of-range target rejection verification.
  - Added Section 20: Out-of-range gesture enum dispatching rejection in `GAME` mode (no penalty, lives unchanged, combo preserved, no actuator actions).
  - Added Section 21: Out-of-range gesture handling across Robot, SmartControl, Presentation, and Custom handlers.
  - Added Section 22: `getTimeRemainingMs(0)` underflow protection verification.

---

## 3. Verification Record

- **Deep Verification (ran actual tests):**
  - **Native C++ Unit Tests (`-Wall -Wextra -Werror -std=c++11`):**
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/macro_engine_test.cpp firmware/src/macro_engine.cpp -o work/macro_engine_test && ./work/macro_engine_test`: Exit code 0, all 22 test sections passed cleanly.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/modes_test.cpp firmware/src/modes.cpp firmware/src/macro_engine.cpp firmware/src/lcd_ui.cpp -o work/modes_test && ./work/modes_test`: Exit code 0, all 22 test sections passed cleanly.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/lcd_ui_test.cpp firmware/src/lcd_ui.cpp -o work/lcd_ui_test && ./work/lcd_ui_test`: Exit code 0, LCD presentation tests passed.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/capture_protocol_test.cpp firmware/src/capture_protocol.cpp -o work/capture_protocol_test && ./work/capture_protocol_test`: Exit code 0, parser and CRC tests passed.
  - **Embedded PlatformIO Compilation:**
    - `pio run -d firmware -e esp32dev`: Exit code 0, SUCCESS (0 warnings, 0 errors, Xtensa GCC release build).
    - `pio run -d firmware -e dataset`: Exit code 0, SUCCESS (0 warnings, 0 errors).
  - **Python Test Suite Non-Regression:**
    - `.venv/bin/python -m unittest discover -s tests -v`: Ran all 102 tests in 5.219s, 100% OK.
  - **Repository & User Data Integrity:**
    - `git status` confirms no files in `data/raw/`, `data/pending/`, or `data/session_notes/` were touched.
    - Existing uncommitted user edits in `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py`, and `reports/hardware/` are completely preserved.
- **Shallow Verification (manual only):**
  - None; all logic changes have corresponding automated assertions.
- **Unverified aspects:**
  - Real hardware execution on a physical ESP32 connected to physical servos, relays, and LCD hardware (physical device not connected).
  - FreeRTOS tick jitter or preemption latency under concurrent high-rate IMU I2C polling.

---

## 4. Known Issues
- `Minor Robustness Risk` — If a macro sequence is configured with an inter-gesture timeout window smaller than typical human gesture transition duration (<300ms), transitions will abort due to timer expiry. Default is safely configured to 2000 ms.

---

## 5. Remaining risk & next step
- **Assessment:** Requirements R1, R2, and R3 are satisfied with airtight defense against invalid gesture enum corruptions, NaN/out-of-bounds confidences, in-place sequence desynchronization, 32-bit unsigned timestamp underflows, and buffer overruns.
- **Next Step:** Ready for physical actuator driver wiring (`ModeActionListener` -> ESP32 LEDC PWM and GPIO drivers) once physical hardware bench is connected by the user.
