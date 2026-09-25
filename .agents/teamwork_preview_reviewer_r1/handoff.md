# Handoff Report: Multimode and Macro Engine Review & Defect Remediation

> [!WARNING] **Skepticism Disclaimer**
> The state machine logic, prefix collision guards, 32-bit timestamp rollover handling, and mode transitions are verified by comprehensive native unit tests and compile without warnings on both host GCC and embedded Xtensa GCC; however, actual physical timing jitter under heavy FreeRTOS task loading on physical silicon remains untested in the absence of attached hardware.

## 1. What the prior attempt got wrong

### Issue 1: `CustomModeHandler::bindGesture` creates unreachable duplicate bindings and leaks capacity
- **Input:** `custom.bindGesture(Gesture::Up, 1, "FIRST"); custom.bindGesture(Gesture::Up, 2, "SECOND"); custom.handleGesture(Gesture::Up);`
- **Expected:** The binding for `Gesture::Up` is updated in place to action 2 ("SECOND"), `bindingCount_` remains 1, and `handleGesture` dispatches action 2.
- **Actual:** `bindGesture` blindly appended a second entry into `bindings_[1]` and incremented `bindingCount_` to 2. In `handleGesture`, linear search stopped at the first match (index 0). Action 1 was triggered forever, action 2 was unreachable dead code, and `kMaxCustomBindings` capacity was leaked.
- **Root cause:** `CustomModeHandler::bindGesture` did not check if the gesture was already present in `bindings_` before appending.

### Issue 2: `CustomModeHandler` lacked individual unbind and search methods
- **Input:** Caller attempting to unbind a specific custom gesture without wiping the entire binding configuration.
- **Expected:** `custom.unbindGesture(gesture)` removes that binding and decrements count.
- **Actual:** Method did not exist; caller had to call `clearBindings()` and re-register everything.
- **Root cause:** Missing `unbindGesture` and `findBindingByGesture` APIs.

### Issue 3: 32-bit unsigned `millis()` rollover broke timeout detection in `MacroEngine` and `GameModeHandler`
- **Input:** Sequence started at `lastGestureTimeMs = 0xFFFFFFFA` (-6 ms before rollover). Next check occurred at `nowMs = 0x00000070` (+112 ms after rollover). Inter-gesture timeout was 100 ms.
- **Expected:** Elapsed time is 112 - (-6) = 118 ms >= 100 ms. `update()` detects timeout and resets sequence.
- **Actual:** The code evaluated `if (currentStep_ > 0 && nowMs >= lastGestureTimeMs_ && (nowMs - lastGestureTimeMs_ > timeoutMs_))`. Because `0x00000070 >= 0xFFFFFFFA` evaluates to `false`, timeout detection was bypassed entirely, leaving the state machine stuck mid-sequence for 49.7 days.
- **Root cause:** Erroneous inequality guard `nowMs >= lastGestureTimeMs_`. In C++ unsigned 32-bit arithmetic, `(uint32_t)(nowMs - lastTime) >= timeout` naturally handles rollover correctly only if the faulty inequality guard is removed.

### Issue 4: Exact boundary timeout off-by-one (`>` vs `>=`)
- **Input:** A sequence with timeout window 500 ms at t = 1000 receives `update(1500)`.
- **Expected:** At exactly 500 ms elapsed, the timeout window has expired.
- **Actual:** The code used strict inequality `> timeoutMs_`. At t = 1500, `1500 - 1000 > 500` is `false`. The timeout did not fire until t = 1501. In `GameModeHandler`, `getTimeRemainingMs()` already reported 0 ms remaining while `update()` reported the challenge was still active.
- **Root cause:** Strict inequality `>` instead of `>=` on timeout expiration.

### Issue 5: `GameModeHandler::startChallenge` accepted non-actionable `Gesture::Unknown`
- **Input:** `game.startChallenge(Gesture::Unknown, 2000, 1000);`
- **Expected:** Call is rejected or ignored, since `Gesture::Unknown` can never be matched.
- **Actual:** Challenge became active with `currentChallenge_ = Gesture::Unknown`. `handleGesture` filters out `Unknown` as `GameEvent::Ignored` and any other gesture as `WrongGesture`. It was impossible for the player to succeed, guaranteeing a timeout and lost life.
- **Root cause:** Missing validation `if (target == Gesture::Unknown) return;` in `startChallenge`.

### Issue 6: `PresentationModeHandler` lacked slide index and capacity bounds clamping
- **Input:** `setSlideIndex(-5)`, `setSlideIndex(999)` when `maxSlides = 10`, or `setMaxSlides(0)`.
- **Expected:** Slide index clamped to [1, maxSlides] and maxSlides clamped to >= 1.
- **Actual:** Slide index was assigned verbatim, allowing negative slides and out-of-range values.
- **Root cause:** Missing bounds clamping in `setSlideIndex` and `setMaxSlides`.

### Issue 7: `MacroEngine::registerMacro` permitted duplicate IDs, duplicate sequences, and prefix collisions
- **Input:** Registering duplicate IDs, exact duplicate sequences under different IDs, or strict prefix collisions (e.g. `LEFT -> RIGHT` when `LEFT -> RIGHT -> CIRCLE` already exists).
- **Expected:** Duplicate IDs update the existing macro in place; duplicate sequences or prefix collisions return `false` because the shorter prefix would greedily fire and make the longer sequence permanently unreachable.
- **Actual:** All were accepted into the array. Shorter macros shadowed longer macros, creating dead code and invalid trigger behavior.
- **Root cause:** Missing duplicate sequence and prefix collision validation in `registerMacro`.

### Issue 8: `ModeManager::dispatch` failed to abort in-progress macro sequence on unknown/rejected gesture
- **Input:** Sequence in progress in Macro mode, followed by `dispatch(Gesture::Unknown)` or `dispatch(GestureInput(..., rejected=true))`.
- **Expected:** When `abortOnUnknown` is enabled (default), the sequence is aborted and resets to idle.
- **Actual:** `ModeManager::dispatch` intercepted unknown/rejected gestures at the top of the function and returned early without notifying `macroEngine_`, leaving `macroEngine_` frozen mid-sequence until manual `reset()` was called.
- **Root cause:** Early exit in `dispatch` bypassed `macroEngine_.abort()`.

### Issue 9: `ModeManager` lacked unified `reset()` method
- **Input:** Caller wishing to re-arm or reset all mode handlers to initial state.
- **Expected:** `manager.reset()` resets runtime state across all mode handlers.
- **Actual:** No `reset()` method existed on `ModeManager`.
- **Root cause:** Missing API declaration and implementation.

### Issue 10: `MacroEngine` exposed dirty buffer data after sequence completion or cancellation
- **Input:** Calling `getCurrentBuffer()` after a completed or cancelled sequence.
- **Expected:** Buffer zeroed (`Gesture::Unknown`).
- **Actual:** Buffer retained stale gestures from previous sequences.
- **Root cause:** Buffer zeroing was only performed in `reset()`, not upon sequence termination.

### Issue 11: `RobotModeHandler` ignored counter-clockwise circle
- **Input:** `Gesture::CircleCcw` dispatched to Robot mode.
- **Expected:** Directional motion intent (CCW spin at speed -75).
- **Actual:** Returned `RobotCommand::None` ("NO_ACTION").
- **Root cause:** Missing `Gesture::CircleCcw` handling in `RobotModeHandler::handleGesture`.

---

## 2. What I changed

- **`firmware/src/macro_engine.h` & `firmware/src/macro_engine.cpp`**:
  - Enhanced `isDirectional` to include `Gesture::CircleCcw`.
  - Added `"circle_cw"` alias to `gestureFromString`.
  - Implemented prefix collision detection and duplicate sequence rejection in `registerMacro`.
  - Implemented in-place macro definition updates when registering with an existing ID.
  - Implemented `bool unregisterMacro(uint32_t id)`.
  - Fixed 32-bit unsigned `millis()` rollover arithmetic in `feed()` and `update()`.
  - Fixed exact boundary timeout check (`elapsed >= timeoutMs_`).
  - Added array bounds protection against buffer overflow.
  - Zeroed sequence buffer on all terminal states (Completed, Cancelled, Timeout, Aborted).
- **`firmware/src/modes.h` & `firmware/src/modes.cpp`**:
  - Implemented `unbindGesture(Gesture g)` and `findBindingByGesture(Gesture g)` in `CustomModeHandler`.
  - Updated `bindGesture` to update existing bindings in place without consuming extra capacity.
  - Added slide index and max slides boundary clamping ([1, maxSlides]) in `PresentationModeHandler`.
  - Added `Gesture::CircleCcw` handling in `RobotModeHandler` (CCW spin animation at speed -75).
  - Added `Gesture::Unknown` validation in `GameModeHandler::startChallenge`.
  - Fixed 32-bit unsigned rollover and exact boundary timeout handling in `GameModeHandler`.
  - Updated `ModeManager::dispatch` to abort in-progress sequences in Macro mode on unknown or rejected gestures when `abortOnUnknown_ == true`.
  - Added `void reset()` to `ModeManager` to reset runtime state across all mode handlers.
  - Enhanced LCD `renderStatus` to indicate active alarms (`ALM!`) in SmartControl and `GAME OVER S:%u` in Game mode.
- **`tests/native/macro_engine_test.cpp`**:
  - Added Section 10: 32-bit unsigned rollover verification across `0xFFFFFFFAu` to `0x00000070u`.
  - Added Section 11: Exact boundary timeout verification (`elapsed == timeoutMs`).
  - Added Section 12: Duplicate sequence and prefix collision rejection verification.
  - Added Section 13: Dynamic unregistration verification.
  - Added Section 14: Buffer zeroing verification on sequence termination.
  - Added Section 15: `CircleCcw` directionality and `circle_cw` alias parsing.
- **`tests/native/modes_test.cpp`**:
  - Added Section 8: `RobotMode` CircleCcw spin execution.
  - Added Section 9: `PresentationMode` slide clamping edge cases.
  - Added Section 10: `GameMode` Unknown rejection and 32-bit rollover timeout.
  - Added Section 11: `ModeManager::reset()` state clearance verification.
  - Added Section 12: Expanded LCD UI status frame checks (Alarm active and Game Over).
  - Added verification that Unknown gesture aborts active macro sequence in `ModeManager::dispatch`.
  - Added Custom mode re-binding update and individual unbind verification.

---

## 3. Verification Record

- **Deep Verification (ran actual tests):**
  - **Native C++ Unit Tests (`-Wall -Wextra -Werror -std=c++11`):**
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/macro_engine_test.cpp firmware/src/macro_engine.cpp -o work/macro_engine_test && ./work/macro_engine_test`: Exit code 0, all 15 test suites passed.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/modes_test.cpp firmware/src/modes.cpp firmware/src/macro_engine.cpp firmware/src/lcd_ui.cpp -o work/modes_test && ./work/modes_test`: Exit code 0, all 12 mode test suites passed.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/lcd_ui_test.cpp firmware/src/lcd_ui.cpp -o work/lcd_ui_test && ./work/lcd_ui_test`: Exit code 0, LCD presentation tests passed.
    - `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/capture_protocol_test.cpp firmware/src/capture_protocol.cpp -o work/capture_protocol_test && ./work/capture_protocol_test`: Exit code 0, CRC32 and parser tests passed.
  - **Embedded PlatformIO Compilation:**
    - `pio run -d firmware -e esp32dev`: Exit code 0, SUCCESS (0 warnings, 0 errors, compiled with Xtensa GCC).
    - `pio run -d firmware -e dataset`: Exit code 0, SUCCESS (0 warnings, 0 errors).
  - **Python Test Suite Non-Regression:**
    - `.venv/bin/python -m unittest discover -s tests -v`: Ran all 102 tests in 5.661s, 100% OK.
  - **Repository & User Data Integrity:**
    - `git status` confirms no files in `data/raw/`, `data/pending/`, or `data/session_notes/` were touched.
    - Existing uncommitted user edits in `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py`, and `reports/hardware/` are completely preserved.
- **Shallow Verification (manual only):**
  - Inspection of LCD 16x2 row outputs for uppercase formatting and length invariants.
- **Unverified aspects:**
  - Real hardware execution on a physical ESP32 connected to physical servos, relays, and LCD hardware (physical device not connected).
  - Physical FreeRTOS task context switching latency under concurrent high-rate IMU I2C polling.

---

## 4. Known Issues
- `Minor Robustness Risk` — If a macro sequence is configured with a timeout window smaller than typical human gesture transition duration (<300ms), transitions will abort due to timer expiry. Default is safely configured to 2000 ms.

---

## 5. Remaining risk & next step
- **Assessment:** The feature requirements R1 (multimode state machine with 6 modes and strict UNKNOWN rejection), R2 (macro sequence engine with temporal timeouts, cancellation on invalid transitions, and safe dispatch), and R3 (preservation of uncommitted user changes and zero regressions across all 102 tests and PlatformIO builds) are fully implemented and verified.
- **Next Step:** Integrate hardware actuator drivers (LEDC PWM for servos, GPIO driver for relays) with `ModeActionListener` once hardware bench is physically wired.
