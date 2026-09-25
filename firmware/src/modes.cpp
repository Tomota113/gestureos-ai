#include "modes.h"
#include <stdio.h>
#include <string.h>

namespace modes {

namespace {
bool strCaseEqual(const char* a, const char* b) {
  if (!a || !b) return false;
  while (*a && *b) {
    char ca = *a;
    char cb = *b;
    if (ca >= 'A' && ca <= 'Z') ca = static_cast<char>(ca - 'A' + 'a');
    if (cb >= 'A' && cb <= 'Z') cb = static_cast<char>(cb - 'A' + 'a');
    if (ca != cb) return false;
    ++a;
    ++b;
  }
  return (*a == '\0' && *b == '\0');
}

void fillRow(char (&target)[lcd_ui::kColumns + 1], const char* source) {
  for (size_t i = 0; i < lcd_ui::kColumns; ++i) target[i] = ' ';
  target[lcd_ui::kColumns] = '\0';
  if (!source) return;
  for (size_t i = 0; i < lcd_ui::kColumns && source[i]; ++i) {
    unsigned char c = static_cast<unsigned char>(source[i]);
    if (c < 32 || c > 126) c = '?';
    if (c >= 'a' && c <= 'z') c = static_cast<unsigned char>(c - 'a' + 'A');
    target[i] = static_cast<char>(c);
  }
}
}  // namespace

const char* modeToString(OperatingMode mode) {
  switch (mode) {
    case OperatingMode::Robot:
      return "ROBOT";
    case OperatingMode::SmartControl:
      return "SMART_CONTROL";
    case OperatingMode::Presentation:
      return "PRESENTATION";
    case OperatingMode::Game:
      return "GAME";
    case OperatingMode::Macro:
      return "MACRO";
    case OperatingMode::Custom:
      return "CUSTOM";
    default:
      return "UNKNOWN";
  }
}

bool modeFromString(const char* str, OperatingMode& outMode) {
  if (!str) return false;
  if (strCaseEqual(str, "robot")) {
    outMode = OperatingMode::Robot;
    return true;
  }
  if (strCaseEqual(str, "smart_control") || strCaseEqual(str, "smart control") || strCaseEqual(str, "smartcontrol")) {
    outMode = OperatingMode::SmartControl;
    return true;
  }
  if (strCaseEqual(str, "presentation")) {
    outMode = OperatingMode::Presentation;
    return true;
  }
  if (strCaseEqual(str, "game")) {
    outMode = OperatingMode::Game;
    return true;
  }
  if (strCaseEqual(str, "macro")) {
    outMode = OperatingMode::Macro;
    return true;
  }
  if (strCaseEqual(str, "custom")) {
    outMode = OperatingMode::Custom;
    return true;
  }
  return false;
}

// ---------------- ROBOT MODE ----------------
RobotModeHandler::RobotModeHandler()
    : servoAngle_(90), speed_(0), lastCommand_(RobotCommand::None) {}

void RobotModeHandler::reset() {
  servoAngle_ = 90;
  speed_ = 0;
  lastCommand_ = RobotCommand::None;
}

RobotAction RobotModeHandler::handleGesture(Gesture gesture) {
  RobotAction action{};
  action.servoAngle = servoAngle_;
  action.speed = speed_;

  // UNKNOWN or rejected gestures must never trigger any action or actuator command
  if (gesture == Gesture::Unknown ||
      static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)) {
    action.command = RobotCommand::None;
    action.description = "UNKNOWN_IGNORED";
    return action;
  }

  switch (gesture) {
    case Gesture::Left:
      servoAngle_ = 45;
      speed_ = -50;
      lastCommand_ = RobotCommand::MoveLeft;
      action.command = RobotCommand::MoveLeft;
      action.servoAngle = servoAngle_;
      action.speed = speed_;
      action.description = "SERVO LEFT 45";
      break;
    case Gesture::Right:
      servoAngle_ = 135;
      speed_ = 50;
      lastCommand_ = RobotCommand::MoveRight;
      action.command = RobotCommand::MoveRight;
      action.servoAngle = servoAngle_;
      action.speed = speed_;
      action.description = "SERVO RIGHT 135";
      break;
    case Gesture::Up:
      servoAngle_ = 90;
      speed_ = 100;
      lastCommand_ = RobotCommand::MoveUp;
      action.command = RobotCommand::MoveUp;
      action.servoAngle = servoAngle_;
      action.speed = speed_;
      action.description = "SERVO UP 90";
      break;
    case Gesture::Down:
      servoAngle_ = 0;
      speed_ = -100;
      lastCommand_ = RobotCommand::MoveDown;
      action.command = RobotCommand::MoveDown;
      action.servoAngle = servoAngle_;
      action.speed = speed_;
      action.description = "SERVO DOWN 0";
      break;
    case Gesture::Circle:
      speed_ = 75;
      lastCommand_ = RobotCommand::CircleSpin;
      action.command = RobotCommand::CircleSpin;
      action.servoAngle = servoAngle_;
      action.speed = speed_;
      action.description = "CIRCLE ANIMATION";
      break;
    case Gesture::CircleCcw:
      speed_ = -75;
      lastCommand_ = RobotCommand::CircleSpin;
      action.command = RobotCommand::CircleSpin;
      action.servoAngle = servoAngle_;
      action.speed = speed_;
      action.description = "CIRCLE CCW ANIMATION";
      break;
    case Gesture::Stop:
      speed_ = 0;
      lastCommand_ = RobotCommand::Stop;
      action.command = RobotCommand::Stop;
      action.servoAngle = servoAngle_;
      action.speed = 0;
      action.description = "ROBOT STOP";
      break;
    default:
      action.command = RobotCommand::None;
      action.description = "NO_ACTION";
      break;
  }
  return action;
}

int16_t RobotModeHandler::getServoAngle() const {
  return servoAngle_;
}

int8_t RobotModeHandler::getSpeed() const {
  return speed_;
}

RobotCommand RobotModeHandler::getLastCommand() const {
  return lastCommand_;
}

// ---------------- SMART CONTROL MODE ----------------
SmartControlModeHandler::SmartControlModeHandler()
    : ledOn_(false), relayOn_(false), alarmActive_(false) {}

void SmartControlModeHandler::reset() {
  ledOn_ = false;
  relayOn_ = false;
  alarmActive_ = false;
}

SmartControlAction SmartControlModeHandler::handleGesture(Gesture gesture) {
  SmartControlAction action{};
  action.device = SmartDevice::None;
  action.state = DeviceState::Off;

  // UNKNOWN or rejected gestures must never trigger any action or actuator command
  if (gesture == Gesture::Unknown ||
      static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)) {
    action.description = "UNKNOWN_IGNORED";
    return action;
  }

  switch (gesture) {
    case Gesture::Up:
      ledOn_ = true;
      action.device = SmartDevice::Led;
      action.state = DeviceState::On;
      action.description = "LED ON";
      break;
    case Gesture::Down:
      ledOn_ = false;
      action.device = SmartDevice::Led;
      action.state = DeviceState::Off;
      action.description = "LED OFF";
      break;
    case Gesture::Circle:
      relayOn_ = true;
      action.device = SmartDevice::Relay;
      action.state = DeviceState::On;
      action.description = "RELAY ON";
      break;
    case Gesture::CircleCcw:
    case Gesture::Left:
      relayOn_ = false;
      action.device = SmartDevice::Relay;
      action.state = DeviceState::Off;
      action.description = "RELAY OFF";
      break;
    case Gesture::Shake:
      alarmActive_ = true;
      action.device = SmartDevice::Alarm;
      action.state = DeviceState::Triggered;
      action.description = "ALARM TRIGGERED";
      break;
    case Gesture::Push:
      if (alarmActive_) {
        alarmActive_ = false;
        action.device = SmartDevice::Alarm;
        action.state = DeviceState::Off;
        action.description = "ALARM OFF";
      } else {
        action.description = "NO_ACTION";
      }
      break;
    case Gesture::Stop:
      ledOn_ = false;
      relayOn_ = false;
      alarmActive_ = false;
      action.device = SmartDevice::All;
      action.state = DeviceState::Off;
      action.description = "ALL OFF";
      break;
    default:
      action.description = "NO_ACTION";
      break;
  }
  return action;
}

bool SmartControlModeHandler::isLedOn() const {
  return ledOn_;
}

bool SmartControlModeHandler::isRelayOn() const {
  return relayOn_;
}

bool SmartControlModeHandler::isAlarmActive() const {
  return alarmActive_;
}

// ---------------- PRESENTATION MODE ----------------
PresentationModeHandler::PresentationModeHandler()
    : slideIndex_(1), maxSlides_(999) {}

void PresentationModeHandler::reset() {
  slideIndex_ = 1;
}

PresentationAction PresentationModeHandler::handleGesture(Gesture gesture) {
  PresentationAction action{};
  action.nav = PresentationNav::None;
  action.slideIndex = slideIndex_;

  // UNKNOWN or rejected gestures must never trigger any action or actuator command
  if (gesture == Gesture::Unknown ||
      static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)) {
    action.description = "UNKNOWN_IGNORED";
    return action;
  }

  switch (gesture) {
    case Gesture::Right:
      if (slideIndex_ < maxSlides_) ++slideIndex_;
      action.nav = PresentationNav::Next;
      action.slideIndex = slideIndex_;
      action.description = "SLIDE NEXT";
      break;
    case Gesture::Left:
      if (slideIndex_ > 1) --slideIndex_;
      action.nav = PresentationNav::Prev;
      action.slideIndex = slideIndex_;
      action.description = "SLIDE PREV";
      break;
    case Gesture::Up:
      slideIndex_ = 1;
      action.nav = PresentationNav::First;
      action.slideIndex = slideIndex_;
      action.description = "SLIDE FIRST";
      break;
    case Gesture::Down:
      slideIndex_ = maxSlides_;
      action.nav = PresentationNav::Last;
      action.slideIndex = slideIndex_;
      action.description = "SLIDE LAST";
      break;
    case Gesture::Push:
    case Gesture::Circle:
      action.nav = PresentationNav::Action;
      action.slideIndex = slideIndex_;
      action.description = "ACTION EXECUTE";
      break;
    case Gesture::Stop:
      action.nav = PresentationNav::Exit;
      action.slideIndex = slideIndex_;
      action.description = "PRESENTATION EXIT";
      break;
    default:
      action.description = "NO_ACTION";
      break;
  }
  return action;
}

int32_t PresentationModeHandler::getSlideIndex() const {
  return slideIndex_;
}

void PresentationModeHandler::setSlideIndex(int32_t index) {
  if (index < 1) index = 1;
  if (index > maxSlides_) index = maxSlides_;
  slideIndex_ = index;
}

void PresentationModeHandler::setMaxSlides(int32_t maxSlides) {
  if (maxSlides < 1) maxSlides = 1;
  maxSlides_ = maxSlides;
  if (slideIndex_ > maxSlides_) {
    slideIndex_ = maxSlides_;
  }
}

int32_t PresentationModeHandler::getMaxSlides() const {
  return maxSlides_;
}

// ---------------- GAME MODE ----------------
GameModeHandler::GameModeHandler()
    : score_(0),
      lives_(3),
      combo_(0),
      maxCombo_(0),
      currentChallenge_(Gesture::Unknown),
      challengeStartMs_(0),
      challengeDurationMs_(0),
      challengeActive_(false),
      gameOver_(false) {}

void GameModeHandler::reset(uint8_t initialLives) {
  score_ = 0;
  lives_ = initialLives;
  combo_ = 0;
  maxCombo_ = 0;
  currentChallenge_ = Gesture::Unknown;
  challengeStartMs_ = 0;
  challengeDurationMs_ = 0;
  challengeActive_ = false;
  gameOver_ = (initialLives == 0);
}

void GameModeHandler::startChallenge(Gesture target, uint32_t durationMs, uint32_t nowMs) {
  if (gameOver_ || target == Gesture::Unknown ||
      static_cast<uint8_t>(target) > static_cast<uint8_t>(Gesture::Stop) ||
      durationMs == 0) return;
  currentChallenge_ = target;
  challengeDurationMs_ = durationMs;
  challengeStartMs_ = nowMs;
  challengeActive_ = true;
}

GameAction GameModeHandler::handleGesture(Gesture gesture, uint32_t nowMs) {
  GameAction action{};
  action.event = GameEvent::None;
  action.scoreDelta = 0;
  action.totalScore = score_;
  action.lives = lives_;
  action.combo = combo_;
  action.gameOver = gameOver_;
  action.expectedGesture = currentChallenge_;

  // UNKNOWN or rejected gestures must never trigger any action or actuator command
  if (gesture == Gesture::Unknown ||
      static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)) {
    action.event = GameEvent::Ignored;
    action.description = "UNKNOWN_IGNORED";
    return action;
  }

  // Handle omitted timestamp (nowMs = 0) when challenge is active
  if (nowMs == 0 && challengeStartMs_ > 0) {
    nowMs = challengeStartMs_;
  }

  if (gameOver_) {
    action.description = "GAME_OVER";
    return action;
  }

  if (!challengeActive_) {
    action.description = "GAME_INACTIVE";
    return action;
  }

  // Check if challenge expired before gesture (robust to 32-bit unsigned rollover)
  if (challengeDurationMs_ > 0) {
    uint32_t elapsed = nowMs - challengeStartMs_;
    if (elapsed >= challengeDurationMs_) {
      challengeActive_ = false;
      currentChallenge_ = Gesture::Unknown;
      combo_ = 0;
      if (lives_ > 0) --lives_;
      if (lives_ == 0) gameOver_ = true;

      action.event = GameEvent::TimeoutMiss;
      action.lives = lives_;
      action.combo = 0;
      action.gameOver = gameOver_;
      action.description = "CHALLENGE_TIMEOUT";
      return action;
    }
  }

  if (gesture == currentChallenge_) {
    uint32_t delta = 100 + (combo_ * 20);
    score_ += delta;
    ++combo_;
    if (combo_ > maxCombo_) maxCombo_ = combo_;
    challengeActive_ = false;
    currentChallenge_ = Gesture::Unknown;

    action.event = GameEvent::Success;
    action.scoreDelta = delta;
    action.totalScore = score_;
    action.lives = lives_;
    action.combo = combo_;
    action.gameOver = gameOver_;
    action.description = "CHALLENGE_HIT";
    return action;
  }

  // Mismatched gesture: reactive challenge miss
  combo_ = 0;
  if (lives_ > 0) --lives_;
  if (lives_ == 0) gameOver_ = true;
  challengeActive_ = false;
  currentChallenge_ = Gesture::Unknown;

  action.event = GameEvent::WrongGesture;
  action.lives = lives_;
  action.combo = 0;
  action.gameOver = gameOver_;
  action.description = "WRONG_GESTURE";
  return action;
}

GameAction GameModeHandler::update(uint32_t nowMs) {
  GameAction action{};
  action.event = GameEvent::None;
  action.scoreDelta = 0;
  action.totalScore = score_;
  action.lives = lives_;
  action.combo = combo_;
  action.gameOver = gameOver_;
  action.expectedGesture = currentChallenge_;

  if (challengeActive_ && challengeDurationMs_ > 0) {
    uint32_t elapsed = nowMs - challengeStartMs_;
    if (elapsed >= challengeDurationMs_) {
      challengeActive_ = false;
      currentChallenge_ = Gesture::Unknown;
      combo_ = 0;
      if (lives_ > 0) --lives_;
      if (lives_ == 0) gameOver_ = true;

      action.event = GameEvent::TimeoutMiss;
      action.lives = lives_;
      action.combo = 0;
      action.gameOver = gameOver_;
      action.description = "CHALLENGE_TIMEOUT";
      return action;
    }
  }

  action.description = challengeActive_ ? "CHALLENGE_ACTIVE" : (gameOver_ ? "GAME_OVER" : "GAME_IDLE");
  return action;
}

bool GameModeHandler::isChallengeActive() const {
  return challengeActive_;
}

bool GameModeHandler::isGameOver() const {
  return gameOver_;
}

uint32_t GameModeHandler::getScore() const {
  return score_;
}

uint8_t GameModeHandler::getLives() const {
  return lives_;
}

uint32_t GameModeHandler::getCombo() const {
  return combo_;
}

Gesture GameModeHandler::getCurrentChallenge() const {
  return challengeActive_ ? currentChallenge_ : Gesture::Unknown;
}

uint32_t GameModeHandler::getTimeRemainingMs(uint32_t nowMs) const {
  if (!challengeActive_ || challengeDurationMs_ == 0) return 0;
  if (nowMs == 0 && challengeStartMs_ > 0) {
    nowMs = challengeStartMs_;
  }
  uint32_t elapsed = nowMs - challengeStartMs_;
  if (elapsed >= challengeDurationMs_) return 0;
  return challengeDurationMs_ - elapsed;
}

// ---------------- CUSTOM MODE ----------------
CustomModeHandler::CustomModeHandler() : bindingCount_(0) {
  memset(bindings_, 0, sizeof(bindings_));
}

void CustomModeHandler::clearBindings() {
  bindingCount_ = 0;
  memset(bindings_, 0, sizeof(bindings_));
}

bool CustomModeHandler::bindGesture(Gesture g, uint32_t actionId, const char* name, CustomActionFn fn, void* userData) {
  if (g == Gesture::Unknown ||
      static_cast<uint8_t>(g) > static_cast<uint8_t>(Gesture::Stop) ||
      !name || name[0] == '\0') {
    return false;
  }
  // Check if gesture is already bound; if so, update existing binding in place
  for (size_t i = 0; i < bindingCount_; ++i) {
    if (bindings_[i].gesture == g) {
      bindings_[i].actionId = actionId;
      strncpy(bindings_[i].name, name, kMaxCustomNameLen - 1);
      bindings_[i].name[kMaxCustomNameLen - 1] = '\0';
      bindings_[i].fn = fn;
      bindings_[i].userData = userData;
      return true;
    }
  }
  if (bindingCount_ >= kMaxCustomBindings) {
    return false;
  }
  CustomBinding& b = bindings_[bindingCount_];
  b.gesture = g;
  b.actionId = actionId;
  strncpy(b.name, name, kMaxCustomNameLen - 1);
  b.name[kMaxCustomNameLen - 1] = '\0';
  b.fn = fn;
  b.userData = userData;
  ++bindingCount_;
  return true;
}

bool CustomModeHandler::unbindGesture(Gesture g) {
  for (size_t i = 0; i < bindingCount_; ++i) {
    if (bindings_[i].gesture == g) {
      for (size_t j = i; j + 1 < bindingCount_; ++j) {
        bindings_[j] = bindings_[j + 1];
      }
      --bindingCount_;
      memset(&bindings_[bindingCount_], 0, sizeof(CustomBinding));
      return true;
    }
  }
  return false;
}

CustomAction CustomModeHandler::handleGesture(Gesture gesture) {
  CustomAction action{};
  action.triggered = false;
  action.actionId = 0;
  action.actionName = nullptr;

  // UNKNOWN or rejected gestures must never trigger any action or actuator command
  if (gesture == Gesture::Unknown ||
      static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)) {
    action.description = "UNKNOWN_IGNORED";
    return action;
  }

  for (size_t i = 0; i < bindingCount_; ++i) {
    if (bindings_[i].gesture == gesture) {
      action.triggered = true;
      action.actionId = bindings_[i].actionId;
      action.actionName = bindings_[i].name;
      action.description = "CUSTOM_TRIGGERED";
      if (bindings_[i].fn) {
        bindings_[i].fn(bindings_[i].actionId, bindings_[i].name, bindings_[i].userData);
      }
      return action;
    }
  }

  action.description = "NO_CUSTOM_BINDING";
  return action;
}

size_t CustomModeHandler::getBindingCount() const {
  return bindingCount_;
}

const CustomBinding* CustomModeHandler::getBinding(size_t index) const {
  if (index >= bindingCount_) return nullptr;
  return &bindings_[index];
}

const CustomBinding* CustomModeHandler::findBindingByGesture(Gesture g) const {
  for (size_t i = 0; i < bindingCount_; ++i) {
    if (bindings_[i].gesture == g) return &bindings_[i];
  }
  return nullptr;
}

// ---------------- MODE MANAGER ----------------
ModeManager::ModeManager()
    : mode_(OperatingMode::Robot),
      robotHandler_(),
      smartControlHandler_(),
      presentationHandler_(),
      gameHandler_(),
      macroEngine_(),
      customHandler_(),
      listener_(nullptr) {
  // Register project default macro: LEFT -> RIGHT -> CIRCLE = MACRO_01
  macroEngine_.registerMacro(1, "MACRO_01", {Gesture::Left, Gesture::Right, Gesture::Circle});
}

bool ModeManager::setMode(OperatingMode mode) {
  if (static_cast<uint8_t>(mode) > static_cast<uint8_t>(OperatingMode::Custom)) {
    return false;
  }
  mode_ = mode;
  return true;
}

bool ModeManager::setModeByName(const char* name) {
  OperatingMode parsedMode;
  if (modeFromString(name, parsedMode)) {
    mode_ = parsedMode;
    return true;
  }
  return false;
}

OperatingMode ModeManager::getMode() const {
  return mode_;
}

const char* ModeManager::getModeName() const {
  return modeToString(mode_);
}

void ModeManager::reset() {
  robotHandler_.reset();
  smartControlHandler_.reset();
  presentationHandler_.reset();
  gameHandler_.reset();
  macroEngine_.reset();
}

DispatchResult ModeManager::dispatch(Gesture gesture, uint32_t nowMs) {
  GestureInput input(gesture, 1.0f, false, nowMs);
  return dispatch(input);
}

DispatchResult ModeManager::dispatch(const GestureInput& input) {
  DispatchResult result{};
  result.mode = mode_;
  result.actionTriggered = false;

  // Enforce global contract: UNKNOWN or rejected gestures must NEVER trigger any action or actuator command.
  // Also guard against NaN or non-positive / out-of-range confidence scores.
  if (input.gesture == Gesture::Unknown ||
      static_cast<uint8_t>(input.gesture) > static_cast<uint8_t>(Gesture::Stop) ||
      input.rejected ||
      !(input.confidence > 0.0f) || input.confidence > 1.0f) {
    if (mode_ == OperatingMode::Macro && macroEngine_.isInSequence() && macroEngine_.getAbortOnUnknown()) {
      macroEngine_.abort();
      result.macro.status = StepStatus::Cancelled;
      result.macro.actionTriggered = false;
      result.macro.message = input.rejected ? "REJECTED_ABORTED" : "UNKNOWN_ABORTED";
    }
    result.description = input.rejected ? "REJECTED_INPUT" : "UNKNOWN_GESTURE";
    return result;
  }

  switch (mode_) {
    case OperatingMode::Robot: {
      result.robot = robotHandler_.handleGesture(input.gesture);
      result.actionTriggered = (result.robot.command != RobotCommand::None);
      result.description = result.robot.description;
      if (result.actionTriggered && listener_) {
        listener_->onRobotAction(result.robot);
      }
      break;
    }
    case OperatingMode::SmartControl: {
      result.smartControl = smartControlHandler_.handleGesture(input.gesture);
      result.actionTriggered = (result.smartControl.device != SmartDevice::None);
      result.description = result.smartControl.description;
      if (result.actionTriggered && listener_) {
        listener_->onSmartControlAction(result.smartControl);
      }
      break;
    }
    case OperatingMode::Presentation: {
      result.presentation = presentationHandler_.handleGesture(input.gesture);
      result.actionTriggered = (result.presentation.nav != PresentationNav::None);
      result.description = result.presentation.description;
      if (result.actionTriggered && listener_) {
        listener_->onPresentationAction(result.presentation);
      }
      break;
    }
    case OperatingMode::Game: {
      result.game = gameHandler_.handleGesture(input.gesture, input.timestampMs);
      result.actionTriggered = (result.game.event == GameEvent::Success ||
                                result.game.event == GameEvent::WrongGesture ||
                                result.game.event == GameEvent::TimeoutMiss);
      result.description = result.game.description;
      if (result.actionTriggered && listener_) {
        listener_->onGameAction(result.game);
      }
      break;
    }
    case OperatingMode::Macro: {
      result.macro = macroEngine_.feed(input.gesture, input.timestampMs);
      result.actionTriggered = result.macro.actionTriggered;
      result.description = result.macro.message;
      if (result.actionTriggered && listener_) {
        listener_->onMacroAction(result.macro);
      }
      break;
    }
    case OperatingMode::Custom: {
      result.custom = customHandler_.handleGesture(input.gesture);
      result.actionTriggered = result.custom.triggered;
      result.description = result.custom.description;
      if (result.actionTriggered && listener_) {
        listener_->onCustomAction(result.custom);
      }
      break;
    }
    default: {
      result.description = "INVALID_MODE";
      break;
    }
  }

  return result;
}

DispatchResult ModeManager::update(uint32_t nowMs) {
  DispatchResult result{};
  result.mode = mode_;
  result.actionTriggered = false;

  if (mode_ == OperatingMode::Game) {
    result.game = gameHandler_.update(nowMs);
    result.actionTriggered = (result.game.event == GameEvent::TimeoutMiss);
    result.description = result.game.description;
    if (result.actionTriggered && listener_) {
      listener_->onGameAction(result.game);
    }
  } else if (mode_ == OperatingMode::Macro) {
    result.macro = macroEngine_.update(nowMs);
    result.actionTriggered = result.macro.actionTriggered;
    result.description = result.macro.message;
    if (result.actionTriggered && listener_) {
      listener_->onMacroAction(result.macro);
    }
  } else {
    result.description = "IDLE";
  }

  return result;
}

RobotModeHandler& ModeManager::robot() {
  return robotHandler_;
}

const RobotModeHandler& ModeManager::robot() const {
  return robotHandler_;
}

SmartControlModeHandler& ModeManager::smartControl() {
  return smartControlHandler_;
}

const SmartControlModeHandler& ModeManager::smartControl() const {
  return smartControlHandler_;
}

PresentationModeHandler& ModeManager::presentation() {
  return presentationHandler_;
}

const PresentationModeHandler& ModeManager::presentation() const {
  return presentationHandler_;
}

GameModeHandler& ModeManager::game() {
  return gameHandler_;
}

const GameModeHandler& ModeManager::game() const {
  return gameHandler_;
}

macro_engine::MacroEngine& ModeManager::macroEngine() {
  return macroEngine_;
}

const macro_engine::MacroEngine& ModeManager::macroEngine() const {
  return macroEngine_;
}

CustomModeHandler& ModeManager::custom() {
  return customHandler_;
}

const CustomModeHandler& ModeManager::custom() const {
  return customHandler_;
}

void ModeManager::setActionListener(ModeActionListener* listener) {
  listener_ = listener;
}

lcd_ui::Frame ModeManager::renderStatus(const char* extra) const {
  lcd_ui::Frame frame{};

  // Row 1: MODE: <NAME>
  char topBuf[48];
  snprintf(topBuf, sizeof(topBuf), "MODE: %s", getModeName());
  fillRow(frame.top, topBuf);

  // Row 2: custom detail or mode state summary
  if (extra && extra[0]) {
    fillRow(frame.bottom, extra);
  } else {
    char botBuf[48];
    switch (mode_) {
      case OperatingMode::Robot:
        snprintf(botBuf, sizeof(botBuf), "ANG:%d SPD:%d", robotHandler_.getServoAngle(), robotHandler_.getSpeed());
        break;
      case OperatingMode::SmartControl:
        if (smartControlHandler_.isAlarmActive()) {
          snprintf(botBuf, sizeof(botBuf), "L:%s R:%s ALM!", smartControlHandler_.isLedOn() ? "ON" : "OFF",
                   smartControlHandler_.isRelayOn() ? "ON" : "OFF");
        } else {
          snprintf(botBuf, sizeof(botBuf), "L:%s R:%s", smartControlHandler_.isLedOn() ? "ON" : "OFF",
                   smartControlHandler_.isRelayOn() ? "ON" : "OFF");
        }
        break;
      case OperatingMode::Presentation:
        snprintf(botBuf, sizeof(botBuf), "SLIDE %d/%d", presentationHandler_.getSlideIndex(),
                 presentationHandler_.getMaxSlides());
        break;
      case OperatingMode::Game:
        if (gameHandler_.isGameOver()) {
          snprintf(botBuf, sizeof(botBuf), "GAME OVER S:%u", gameHandler_.getScore());
        } else {
          snprintf(botBuf, sizeof(botBuf), "S:%u L:%u C:%u", gameHandler_.getScore(), gameHandler_.getLives(),
                   gameHandler_.getCombo());
        }
        break;
      case OperatingMode::Macro:
        snprintf(botBuf, sizeof(botBuf), "STEP %u IN_SEQ:%d", static_cast<unsigned>(macroEngine_.getCurrentStep()),
                 macroEngine_.isInSequence() ? 1 : 0);
        break;
      case OperatingMode::Custom:
        snprintf(botBuf, sizeof(botBuf), "BOUND:%u", static_cast<unsigned>(customHandler_.getBindingCount()));
        break;
      default:
        snprintf(botBuf, sizeof(botBuf), "MODE UNKNOWN");
        break;
    }
    fillRow(frame.bottom, botBuf);
  }

  return frame;
}

}  // namespace modes
