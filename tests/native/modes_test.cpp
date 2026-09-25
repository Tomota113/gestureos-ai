#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "modes.h"

// Listener implementation to verify actuator decoupling
class TestActionListener : public modes::ModeActionListener {
public:
  int robotCount = 0;
  int smartCount = 0;
  int presentationCount = 0;
  int gameCount = 0;
  int macroCount = 0;
  int customCount = 0;

  modes::RobotAction lastRobot{};
  modes::SmartControlAction lastSmart{};
  modes::PresentationAction lastPresentation{};
  modes::GameAction lastGame{};
  macro_engine::StepResult lastMacro{};
  modes::CustomAction lastCustom{};

  void reset() {
    robotCount = smartCount = presentationCount = gameCount = macroCount = customCount = 0;
  }

  void onRobotAction(const modes::RobotAction& action) override {
    ++robotCount;
    lastRobot = action;
  }
  void onSmartControlAction(const modes::SmartControlAction& action) override {
    ++smartCount;
    lastSmart = action;
  }
  void onPresentationAction(const modes::PresentationAction& action) override {
    ++presentationCount;
    lastPresentation = action;
  }
  void onGameAction(const modes::GameAction& action) override {
    ++gameCount;
    lastGame = action;
  }
  void onMacroAction(const macro_engine::StepResult& action) override {
    ++macroCount;
    lastMacro = action;
  }
  void onCustomAction(const modes::CustomAction& action) override {
    ++customCount;
    lastCustom = action;
  }
};

static int g_customFnCalled = 0;
static void customTestFn(uint32_t actionId, const char* name, void* /*userData*/) {
  assert(actionId == 42);
  assert(strcmp(name, "FIRE_LASER") == 0);
  ++g_customFnCalled;
}

int main() {
  using namespace modes;

  ModeManager manager;
  TestActionListener listener;
  manager.setActionListener(&listener);

  // 1. Mode string parsing and switching
  OperatingMode parsedMode;
  assert(modeFromString("robot", parsedMode) && parsedMode == OperatingMode::Robot);
  assert(modeFromString("smart_control", parsedMode) && parsedMode == OperatingMode::SmartControl);
  assert(modeFromString("SMART CONTROL", parsedMode) && parsedMode == OperatingMode::SmartControl);
  assert(modeFromString("presentation", parsedMode) && parsedMode == OperatingMode::Presentation);
  assert(modeFromString("game", parsedMode) && parsedMode == OperatingMode::Game);
  assert(modeFromString("macro", parsedMode) && parsedMode == OperatingMode::Macro);
  assert(modeFromString("custom", parsedMode) && parsedMode == OperatingMode::Custom);
  assert(!modeFromString("nonexistent_mode", parsedMode));

  assert(manager.getMode() == OperatingMode::Robot);
  assert(strcmp(manager.getModeName(), "ROBOT") == 0);

  // 2. ROBOT MODE TESTS
  listener.reset();
  DispatchResult res;

  // Left -> MoveLeft, servo 45, speed -50
  res = manager.dispatch(Gesture::Left);
  assert(res.actionTriggered);
  assert(res.robot.command == RobotCommand::MoveLeft);
  assert(res.robot.servoAngle == 45);
  assert(res.robot.speed == -50);
  assert(listener.robotCount == 1);
  assert(listener.lastRobot.command == RobotCommand::MoveLeft);

  // Right -> MoveRight, servo 135, speed +50
  res = manager.dispatch(Gesture::Right);
  assert(res.actionTriggered);
  assert(res.robot.command == RobotCommand::MoveRight);
  assert(res.robot.servoAngle == 135);
  assert(res.robot.speed == 50);
  assert(listener.robotCount == 2);

  // Up -> MoveUp, servo 90, speed 100
  res = manager.dispatch(Gesture::Up);
  assert(res.actionTriggered);
  assert(res.robot.command == RobotCommand::MoveUp);
  assert(res.robot.servoAngle == 90);
  assert(res.robot.speed == 100);
  assert(listener.robotCount == 3);

  // Down -> MoveDown, servo 0, speed -100
  res = manager.dispatch(Gesture::Down);
  assert(res.actionTriggered);
  assert(res.robot.command == RobotCommand::MoveDown);
  assert(res.robot.servoAngle == 0);
  assert(res.robot.speed == -100);
  assert(listener.robotCount == 4);

  // Circle -> CircleSpin animation
  res = manager.dispatch(Gesture::Circle);
  assert(res.actionTriggered);
  assert(res.robot.command == RobotCommand::CircleSpin);
  assert(res.robot.speed == 75);
  assert(listener.robotCount == 5);

  // Stop -> Stop, speed 0
  res = manager.dispatch(Gesture::Stop);
  assert(res.actionTriggered);
  assert(res.robot.command == RobotCommand::Stop);
  assert(res.robot.speed == 0);
  assert(listener.robotCount == 6);

  // UNKNOWN or rejected in ROBOT: NEVER triggers any action
  res = manager.dispatch(Gesture::Unknown);
  assert(!res.actionTriggered);
  assert(listener.robotCount == 6); // count unchanged
  assert(manager.robot().getLastCommand() == RobotCommand::Stop); // state unchanged

  GestureInput rejInput(Gesture::Left, 0.3f, true);
  res = manager.dispatch(rejInput);
  assert(!res.actionTriggered);
  assert(listener.robotCount == 6); // count unchanged

  // 3. SMART CONTROL MODE TESTS
  assert(manager.setModeByName("SMART_CONTROL"));
  assert(manager.getMode() == OperatingMode::SmartControl);
  listener.reset();

  assert(!manager.smartControl().isLedOn());
  assert(!manager.smartControl().isRelayOn());
  assert(!manager.smartControl().isAlarmActive());

  // Up -> LED ON
  res = manager.dispatch(Gesture::Up);
  assert(res.actionTriggered);
  assert(res.smartControl.device == SmartDevice::Led);
  assert(res.smartControl.state == DeviceState::On);
  assert(manager.smartControl().isLedOn());
  assert(listener.smartCount == 1);

  // Circle -> RELAY ON
  res = manager.dispatch(Gesture::Circle);
  assert(res.actionTriggered);
  assert(res.smartControl.device == SmartDevice::Relay);
  assert(res.smartControl.state == DeviceState::On);
  assert(manager.smartControl().isRelayOn());
  assert(listener.smartCount == 2);

  // Shake -> ALARM TRIGGERED
  res = manager.dispatch(Gesture::Shake);
  assert(res.actionTriggered);
  assert(res.smartControl.device == SmartDevice::Alarm);
  assert(res.smartControl.state == DeviceState::Triggered);
  assert(manager.smartControl().isAlarmActive());
  assert(listener.smartCount == 3);

  // Down -> LED OFF
  res = manager.dispatch(Gesture::Down);
  assert(res.actionTriggered);
  assert(res.smartControl.device == SmartDevice::Led);
  assert(res.smartControl.state == DeviceState::Off);
  assert(!manager.smartControl().isLedOn());
  assert(manager.smartControl().isRelayOn()); // relay remains on
  assert(listener.smartCount == 4);

  // CircleCcw -> RELAY OFF
  res = manager.dispatch(Gesture::CircleCcw);
  assert(res.actionTriggered);
  assert(res.smartControl.device == SmartDevice::Relay);
  assert(res.smartControl.state == DeviceState::Off);
  assert(!manager.smartControl().isRelayOn());
  assert(listener.smartCount == 5);

  // Stop -> ALL OFF
  manager.smartControl().handleGesture(Gesture::Up); // Turn LED on first
  assert(manager.smartControl().isLedOn());
  res = manager.dispatch(Gesture::Stop);
  assert(res.actionTriggered);
  assert(res.smartControl.device == SmartDevice::All);
  assert(res.smartControl.state == DeviceState::Off);
  assert(!manager.smartControl().isLedOn());
  assert(!manager.smartControl().isRelayOn());
  assert(!manager.smartControl().isAlarmActive());

  // UNKNOWN or rejected in SMART CONTROL: NO action, state untouched
  res = manager.dispatch(Gesture::Unknown);
  assert(!res.actionTriggered);
  res = manager.dispatch(GestureInput(Gesture::Up, 0.4f, true));
  assert(!res.actionTriggered);
  assert(!manager.smartControl().isLedOn()); // did NOT turn on

  // 4. PRESENTATION MODE TESTS
  assert(manager.setMode(OperatingMode::Presentation));
  assert(manager.getMode() == OperatingMode::Presentation);
  listener.reset();

  manager.presentation().setMaxSlides(20);
  assert(manager.presentation().getSlideIndex() == 1);

  // Right -> Next slide (2)
  res = manager.dispatch(Gesture::Right);
  assert(res.actionTriggered);
  assert(res.presentation.nav == PresentationNav::Next);
  assert(res.presentation.slideIndex == 2);
  assert(listener.presentationCount == 1);

  // Left -> Prev slide (1)
  res = manager.dispatch(Gesture::Left);
  assert(res.actionTriggered);
  assert(res.presentation.nav == PresentationNav::Prev);
  assert(res.presentation.slideIndex == 1);
  assert(listener.presentationCount == 2);

  // Left at slide 1 remains 1
  res = manager.dispatch(Gesture::Left);
  assert(res.actionTriggered);
  assert(res.presentation.slideIndex == 1);

  // Down -> Last slide (20)
  res = manager.dispatch(Gesture::Down);
  assert(res.actionTriggered);
  assert(res.presentation.nav == PresentationNav::Last);
  assert(res.presentation.slideIndex == 20);

  // Up -> First slide (1)
  res = manager.dispatch(Gesture::Up);
  assert(res.actionTriggered);
  assert(res.presentation.nav == PresentationNav::First);
  assert(res.presentation.slideIndex == 1);

  // Push -> Action
  res = manager.dispatch(Gesture::Push);
  assert(res.actionTriggered);
  assert(res.presentation.nav == PresentationNav::Action);
  assert(res.presentation.slideIndex == 1);

  // Stop -> Exit
  res = manager.dispatch(Gesture::Stop);
  assert(res.actionTriggered);
  assert(res.presentation.nav == PresentationNav::Exit);

  // UNKNOWN or rejected in PRESENTATION: NO action
  res = manager.dispatch(Gesture::Unknown);
  assert(!res.actionTriggered);
  res = manager.dispatch(GestureInput(Gesture::Right, 0.1f, true));
  assert(!res.actionTriggered);
  assert(manager.presentation().getSlideIndex() == 1);

  // 5. GAME MODE TESTS
  assert(manager.setMode(OperatingMode::Game));
  assert(manager.getMode() == OperatingMode::Game);
  listener.reset();

  manager.game().reset(3);
  assert(manager.game().getLives() == 3);
  assert(manager.game().getScore() == 0);
  assert(manager.game().getCombo() == 0);
  assert(!manager.game().isGameOver());

  // Challenge 1: CIRCLE, 3.0s window
  manager.game().startChallenge(Gesture::Circle, 3000, 1000);
  assert(manager.game().isChallengeActive());
  assert(manager.game().getCurrentChallenge() == Gesture::Circle);
  assert(manager.game().getTimeRemainingMs(2000) == 2000);

  // UNKNOWN during challenge: ignored, no life lost, no score
  res = manager.dispatch(Gesture::Unknown, 1500);
  assert(!res.actionTriggered);
  assert(manager.game().getLives() == 3);
  assert(manager.game().getScore() == 0);
  assert(manager.game().isChallengeActive());

  // Successful hit: CIRCLE at t = 2000 (within 3000 ms window)
  res = manager.dispatch(Gesture::Circle, 2000);
  assert(res.actionTriggered);
  assert(res.game.event == GameEvent::Success);
  assert(res.game.scoreDelta == 100);
  assert(manager.game().getScore() == 100);
  assert(manager.game().getCombo() == 1);
  assert(!manager.game().isChallengeActive());
  assert(listener.gameCount == 1);

  // Challenge 2: UP, 2.0s window, test combo bonus
  manager.game().startChallenge(Gesture::Up, 2000, 3000);
  res = manager.dispatch(Gesture::Up, 3500);
  assert(res.actionTriggered);
  assert(res.game.event == GameEvent::Success);
  assert(res.game.scoreDelta == 120); // 100 + 1 * 20
  assert(manager.game().getScore() == 220);
  assert(manager.game().getCombo() == 2);

  // Challenge 3: DOWN, test wrong gesture penalty
  manager.game().startChallenge(Gesture::Down, 2000, 5000);
  res = manager.dispatch(Gesture::Left, 5500); // Mismatched gesture
  assert(res.actionTriggered);
  assert(res.game.event == GameEvent::WrongGesture);
  assert(manager.game().getLives() == 2);
  assert(manager.game().getCombo() == 0); // combo broken
  assert(!manager.game().isChallengeActive());

  // Challenge 4: test timeout expiration via manager.update()
  manager.game().startChallenge(Gesture::Right, 1000, 7000);
  assert(manager.game().isChallengeActive());

  // Tick before timeout
  DispatchResult tickOk = manager.update(7500);
  assert(!tickOk.actionTriggered);
  assert(manager.game().isChallengeActive());

  // Tick after timeout
  DispatchResult tickMiss = manager.update(8200); // elapsed 1200 > 1000
  assert(tickMiss.actionTriggered);
  assert(tickMiss.game.event == GameEvent::TimeoutMiss);
  assert(manager.game().getLives() == 1);
  assert(!manager.game().isChallengeActive());

  // Challenge 5: final life lost -> GameOver
  manager.game().startChallenge(Gesture::Shake, 1000, 9000);
  res = manager.dispatch(Gesture::Stop, 9500);
  assert(res.actionTriggered);
  assert(manager.game().getLives() == 0);
  assert(manager.game().isGameOver());

  // 6. MACRO MODE TESTS
  assert(manager.setMode(OperatingMode::Macro));
  assert(manager.getMode() == OperatingMode::Macro);
  listener.reset();

  // Pre-registered MACRO_01: LEFT -> RIGHT -> CIRCLE
  // Step 1: Left
  res = manager.dispatch(Gesture::Left, 1000);
  assert(!res.actionTriggered);
  assert(res.macro.status == StepStatus::Progress);
  assert(listener.macroCount == 0);

  // UNKNOWN during macro sequence: rejected, does not dispatch, aborts sequence
  res = manager.dispatch(Gesture::Unknown, 1200);
  assert(!res.actionTriggered);
  assert(!manager.macroEngine().isInSequence());

  // Reset and full sequence: LEFT -> RIGHT -> CIRCLE
  manager.macroEngine().reset();
  res = manager.dispatch(Gesture::Left, 2000);
  assert(!res.actionTriggered);
  res = manager.dispatch(Gesture::Right, 2500);
  assert(!res.actionTriggered);
  res = manager.dispatch(Gesture::Circle, 3000);
  assert(res.actionTriggered);
  assert(res.macro.status == StepStatus::Completed);
  assert(res.macro.macroId == 1);
  assert(strcmp(res.macro.macroName, "MACRO_01") == 0);
  assert(listener.macroCount == 1);

  // 7. CUSTOM MODE TESTS
  assert(manager.setMode(OperatingMode::Custom));
  assert(manager.getMode() == OperatingMode::Custom);
  listener.reset();
  g_customFnCalled = 0;

  manager.custom().clearBindings();
  assert(manager.custom().bindGesture(Gesture::Push, 42, "FIRE_LASER", customTestFn));
  assert(manager.custom().bindGesture(Gesture::Shake, 99, "EMERGENCY_STOP"));
  assert(manager.custom().getBindingCount() == 2);

  // Dispatch bound gesture: Push
  res = manager.dispatch(Gesture::Push);
  assert(res.actionTriggered);
  assert(res.custom.triggered);
  assert(res.custom.actionId == 42);
  assert(strcmp(res.custom.actionName, "FIRE_LASER") == 0);
  assert(g_customFnCalled == 1);
  assert(listener.customCount == 1);

  // Test re-binding an existing gesture updates in-place without leaking capacity
  assert(manager.custom().bindGesture(Gesture::Push, 84, "DOUBLE_LASER"));
  assert(manager.custom().getBindingCount() == 2);
  const CustomBinding* bPush = manager.custom().findBindingByGesture(Gesture::Push);
  assert(bPush != nullptr);
  assert(bPush->actionId == 84);
  assert(strcmp(bPush->name, "DOUBLE_LASER") == 0);

  res = manager.dispatch(Gesture::Push);
  assert(res.actionTriggered);
  assert(res.custom.actionId == 84);
  assert(strcmp(res.custom.actionName, "DOUBLE_LASER") == 0);

  // Test unbinding a gesture
  assert(manager.custom().unbindGesture(Gesture::Push));
  assert(manager.custom().getBindingCount() == 1);
  assert(manager.custom().findBindingByGesture(Gesture::Push) == nullptr);
  res = manager.dispatch(Gesture::Push);
  assert(!res.actionTriggered);
  assert(!res.custom.triggered);

  // Dispatch unbound gesture: Left
  res = manager.dispatch(Gesture::Left);
  assert(!res.actionTriggered);
  assert(!res.custom.triggered);

  // Dispatch UNKNOWN in CUSTOM: rejected, callback NOT called
  res = manager.dispatch(Gesture::Unknown);
  assert(!res.actionTriggered);

  // Negative confidence rejection test
  GestureInput badConf(Gesture::Shake, -0.5f, false);
  res = manager.dispatch(badConf);
  assert(!res.actionTriggered);

  // 8. ROBOT MODE CircleCcw and reset tests
  assert(manager.setMode(OperatingMode::Robot));
  res = manager.dispatch(Gesture::CircleCcw);
  assert(res.actionTriggered);
  assert(res.robot.command == RobotCommand::CircleSpin);
  assert(res.robot.speed == -75);

  // 9. PRESENTATION bounds clamping tests
  assert(manager.setMode(OperatingMode::Presentation));
  manager.presentation().setMaxSlides(10);
  manager.presentation().setSlideIndex(-5);
  assert(manager.presentation().getSlideIndex() == 1);
  manager.presentation().setSlideIndex(999);
  assert(manager.presentation().getSlideIndex() == 10);
  manager.presentation().setMaxSlides(0);
  assert(manager.presentation().getMaxSlides() == 1);
  assert(manager.presentation().getSlideIndex() == 1);

  // 10. GAME MODE Unknown rejection and rollover tests
  assert(manager.setMode(OperatingMode::Game));
  manager.game().reset(3);
  manager.game().startChallenge(Gesture::Unknown, 2000, 1000);
  assert(!manager.game().isChallengeActive()); // Rejected!

  // Game rollover test
  manager.game().startChallenge(Gesture::Right, 100, 0xFFFFFFFAu);
  assert(manager.game().isChallengeActive());
  DispatchResult rollGameTick = manager.update(0x00000070u); // Elapsed = 118 >= 100
  assert(rollGameTick.actionTriggered);
  assert(rollGameTick.game.event == GameEvent::TimeoutMiss);

  // 11. ModeManager::reset() test
  manager.smartControl().handleGesture(Gesture::Up);
  assert(manager.smartControl().isLedOn());
  manager.reset();
  assert(!manager.smartControl().isLedOn());
  assert(!manager.smartControl().isRelayOn());
  assert(!manager.smartControl().isAlarmActive());
  assert(manager.robot().getSpeed() == 0);
  assert(manager.robot().getServoAngle() == 90);
  assert(!manager.macroEngine().isInSequence());

  // 12. LCD UI PRESENTATION HELPER TESTS
  const OperatingMode allModes[] = {
    OperatingMode::Robot,
    OperatingMode::SmartControl,
    OperatingMode::Presentation,
    OperatingMode::Game,
    OperatingMode::Macro,
    OperatingMode::Custom
  };

  for (OperatingMode m : allModes) {
    manager.setMode(m);
    lcd_ui::Frame f1 = manager.renderStatus();
    assert(strlen(f1.top) == lcd_ui::kColumns);
    assert(strlen(f1.bottom) == lcd_ui::kColumns);
    assert(f1.top[lcd_ui::kColumns] == '\0');
    assert(f1.bottom[lcd_ui::kColumns] == '\0');
    assert(strncmp(f1.top, "MODE: ", 6) == 0);

    // Custom extra label
    lcd_ui::Frame f2 = manager.renderStatus("CUSTOM_STATUS_OK");
    assert(strlen(f2.top) == lcd_ui::kColumns);
    assert(strlen(f2.bottom) == lcd_ui::kColumns);
    assert(strcmp(f2.bottom, "CUSTOM_STATUS_OK") == 0);
  }

  // LCD SmartControl with Alarm
  manager.setMode(OperatingMode::SmartControl);
  manager.dispatch(Gesture::Shake);
  lcd_ui::Frame fSmartAlm = manager.renderStatus();
  assert(strstr(fSmartAlm.bottom, "ALM!") != nullptr);

  // LCD Game with Game Over
  manager.setMode(OperatingMode::Game);
  manager.game().reset(1);
  manager.game().startChallenge(Gesture::Up, 1000, 100);
  manager.dispatch(Gesture::Down, 200); // Wrong gesture -> game over
  assert(manager.game().isGameOver());
  lcd_ui::Frame fGameOver = manager.renderStatus();
  assert(strstr(fGameOver.bottom, "GAME OVER") != nullptr);

  // 13. Invalid mode rejection in setMode
  assert(!manager.setMode(static_cast<OperatingMode>(99)));
  assert(manager.getMode() == OperatingMode::Game); // Mode remains unchanged

  // 14. Floating point NaN and out-of-range confidence rejection
  listener.reset();
  float nanVal = 0.0f / 0.0f;
  GestureInput nanInput(Gesture::Up, nanVal, false);
  DispatchResult resNan = manager.dispatch(nanInput);
  assert(!resNan.actionTriggered);
  assert(listener.gameCount == 0);

  GestureInput highConfInput(Gesture::Up, 1.5f, false);
  DispatchResult resHighConf = manager.dispatch(highConfInput);
  assert(!resHighConf.actionTriggered);
  assert(listener.gameCount == 0);

  // 15. GameMode durationMs=0 rejection, challenge clearing, and reset(0)
  manager.game().reset(3);
  manager.game().startChallenge(Gesture::Right, 0, 1000); // 0 duration rejected
  assert(!manager.game().isChallengeActive());
  assert(manager.game().getCurrentChallenge() == Gesture::Unknown);

  // Active challenge reports target; upon completion reports Unknown
  manager.game().startChallenge(Gesture::Right, 2000, 2000);
  assert(manager.game().isChallengeActive());
  assert(manager.game().getCurrentChallenge() == Gesture::Right);
  manager.dispatch(Gesture::Right, 2500); // Hit
  assert(!manager.game().isChallengeActive());
  assert(manager.game().getCurrentChallenge() == Gesture::Unknown);

  // Reset with 0 lives initializes in game over state
  manager.game().reset(0);
  assert(manager.game().isGameOver());
  assert(manager.game().getLives() == 0);

  // 16. SmartControl alarm silencing with Gesture::Push
  manager.setMode(OperatingMode::SmartControl);
  manager.smartControl().reset();
  manager.dispatch(Gesture::Shake); // Trigger alarm
  assert(manager.smartControl().isAlarmActive());
  DispatchResult resSilence = manager.dispatch(Gesture::Push); // Silence alarm
  assert(resSilence.actionTriggered);
  assert(resSilence.smartControl.device == SmartDevice::Alarm);
  assert(resSilence.smartControl.state == DeviceState::Off);
  assert(!manager.smartControl().isAlarmActive());
  // Repeating Push when alarm is already off triggers no action
  DispatchResult resPushIdle = manager.dispatch(Gesture::Push);
  assert(!resPushIdle.actionTriggered);

  // 17. CustomMode out-of-range gesture rejection and clearBindings wipe
  manager.setMode(OperatingMode::Custom);
  manager.custom().clearBindings();
  assert(!manager.custom().bindGesture(static_cast<Gesture>(99), 1, "BAD_GESTURE"));
  assert(manager.custom().bindGesture(Gesture::Push, 10, "PUSH_ACTION"));
  assert(manager.custom().getBindingCount() == 1);
  manager.custom().clearBindings();
  assert(manager.custom().getBindingCount() == 0);
  assert(manager.custom().getBinding(0) == nullptr);
  assert(manager.custom().findBindingByGesture(Gesture::Push) == nullptr);

  // 18. GameMode with default nowMs=0 (omitted) does not underflow into false TimeoutMiss
  manager.setMode(OperatingMode::Game);
  manager.game().reset(3);
  manager.game().startChallenge(Gesture::Right, 2000, 5000);
  assert(manager.game().isChallengeActive());
  listener.reset();
  // Dispatch with default nowMs=0
  res = manager.dispatch(Gesture::Right);
  assert(res.actionTriggered);
  assert(res.game.event == GameEvent::Success);
  assert(res.game.scoreDelta == 100);
  assert(manager.game().getLives() == 3);
  assert(!manager.game().isChallengeActive());
  assert(listener.gameCount == 1);

  // 19. GameMode startChallenge rejects out-of-range target gesture
  manager.game().reset(3);
  manager.game().startChallenge(static_cast<Gesture>(99), 2000, 1000);
  assert(!manager.game().isChallengeActive());
  assert(manager.game().getCurrentChallenge() == Gesture::Unknown);

  // 20. Out-of-range gesture enum dispatched in GAME mode with active challenge:
  // MUST NOT penalize player, break combo, deduct life, or trigger actuator action!
  manager.game().reset(3);
  manager.game().startChallenge(Gesture::Left, 3000, 1000);
  assert(manager.game().isChallengeActive());
  listener.reset();
  DispatchResult resBadGame = manager.dispatch(static_cast<Gesture>(99));
  assert(!resBadGame.actionTriggered);
  assert(strcmp(resBadGame.description, "UNKNOWN_GESTURE") == 0);
  assert(manager.game().getLives() == 3);
  assert(manager.game().getCombo() == 0);
  assert(manager.game().isChallengeActive());
  assert(listener.gameCount == 0); // No actuator action triggered

  // Also via explicit GestureInput
  GestureInput badEnumInput(static_cast<Gesture>(123), 0.9f, false, 1500);
  DispatchResult resBadInput = manager.dispatch(badEnumInput);
  assert(!resBadInput.actionTriggered);
  assert(strcmp(resBadInput.description, "UNKNOWN_GESTURE") == 0);
  assert(manager.game().getLives() == 3);
  assert(manager.game().isChallengeActive());
  assert(listener.gameCount == 0);

  // Complete challenge normally after ignored bad enum
  res = manager.dispatch(Gesture::Left, 2000);
  assert(res.actionTriggered);
  assert(res.game.event == GameEvent::Success);
  assert(manager.game().getLives() == 3);
  assert(listener.gameCount == 1);

  // 21. Out-of-range gesture enum handled defensively across all modes
  // Robot
  manager.setMode(OperatingMode::Robot);
  RobotAction robBad = manager.robot().handleGesture(static_cast<Gesture>(99));
  assert(robBad.command == RobotCommand::None);
  assert(strcmp(robBad.description, "UNKNOWN_IGNORED") == 0);
  DispatchResult resRobBad = manager.dispatch(static_cast<Gesture>(99));
  assert(!resRobBad.actionTriggered);

  // SmartControl
  manager.setMode(OperatingMode::SmartControl);
  SmartControlAction smartBad = manager.smartControl().handleGesture(static_cast<Gesture>(99));
  assert(smartBad.device == SmartDevice::None);
  assert(strcmp(smartBad.description, "UNKNOWN_IGNORED") == 0);
  DispatchResult resSmartBad = manager.dispatch(static_cast<Gesture>(99));
  assert(!resSmartBad.actionTriggered);

  // Presentation
  manager.setMode(OperatingMode::Presentation);
  PresentationAction presBad = manager.presentation().handleGesture(static_cast<Gesture>(99));
  assert(presBad.nav == PresentationNav::None);
  assert(strcmp(presBad.description, "UNKNOWN_IGNORED") == 0);
  DispatchResult resPresBad = manager.dispatch(static_cast<Gesture>(99));
  assert(!resPresBad.actionTriggered);

  // Custom
  manager.setMode(OperatingMode::Custom);
  CustomAction custBad = manager.custom().handleGesture(static_cast<Gesture>(99));
  assert(!custBad.triggered);
  assert(strcmp(custBad.description, "UNKNOWN_IGNORED") == 0);
  DispatchResult resCustBad = manager.dispatch(static_cast<Gesture>(99));
  assert(!resCustBad.actionTriggered);

  // 22. getTimeRemainingMs(0) does not underflow when challenge started at t > 0
  manager.setMode(OperatingMode::Game);
  manager.game().reset(3);
  manager.game().startChallenge(Gesture::Up, 2000, 6000);
  assert(manager.game().getTimeRemainingMs(0) == 2000);
  assert(manager.game().getTimeRemainingMs(6500) == 1500);
  assert(manager.game().getTimeRemainingMs(8500) == 0);

  puts("Multimode engine native tests passed cleanly.");
  return 0;
}
