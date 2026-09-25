#pragma once

#include <stddef.h>
#include <stdint.h>
#include "lcd_ui.h"
#include "macro_engine.h"

namespace modes {

using macro_engine::Gesture;
using macro_engine::gestureToString;
using macro_engine::gestureFromString;
using macro_engine::isDirectional;
using macro_engine::StepStatus;
using macro_engine::MacroDefinition;

enum class OperatingMode : uint8_t {
  Robot = 0,
  SmartControl,
  Presentation,
  Game,
  Macro,
  Custom
};

const char* modeToString(OperatingMode mode);
bool modeFromString(const char* str, OperatingMode& outMode);

struct GestureInput {
  Gesture gesture;
  float confidence;
  bool rejected;
  uint32_t timestampMs;

  GestureInput(Gesture g = Gesture::Unknown, float conf = 1.0f, bool rej = false, uint32_t ts = 0)
      : gesture(g), confidence(conf), rejected(rej), timestampMs(ts) {}
};

// ---------------- ROBOT MODE ----------------
enum class RobotCommand : uint8_t {
  None = 0,
  MoveLeft,
  MoveRight,
  MoveUp,
  MoveDown,
  CircleSpin,
  Stop
};

struct RobotAction {
  RobotCommand command;
  int16_t servoAngle;
  int8_t speed;
  const char* description;
};

class RobotModeHandler {
public:
  RobotModeHandler();
  void reset();
  RobotAction handleGesture(Gesture gesture);
  int16_t getServoAngle() const;
  int8_t getSpeed() const;
  RobotCommand getLastCommand() const;

private:
  int16_t servoAngle_;
  int8_t speed_;
  RobotCommand lastCommand_;
};

// ---------------- SMART CONTROL MODE ----------------
enum class SmartDevice : uint8_t {
  None = 0,
  Led,
  Relay,
  Alarm,
  All
};

enum class DeviceState : uint8_t {
  Off = 0,
  On = 1,
  Triggered = 2
};

struct SmartControlAction {
  SmartDevice device;
  DeviceState state;
  const char* description;
};

class SmartControlModeHandler {
public:
  SmartControlModeHandler();
  void reset();
  SmartControlAction handleGesture(Gesture gesture);
  bool isLedOn() const;
  bool isRelayOn() const;
  bool isAlarmActive() const;

private:
  bool ledOn_;
  bool relayOn_;
  bool alarmActive_;
};

// ---------------- PRESENTATION MODE ----------------
enum class PresentationNav : uint8_t {
  None = 0,
  Next,
  Prev,
  First,
  Last,
  Action,
  Exit
};

struct PresentationAction {
  PresentationNav nav;
  int32_t slideIndex;
  const char* description;
};

class PresentationModeHandler {
public:
  PresentationModeHandler();
  void reset();
  PresentationAction handleGesture(Gesture gesture);
  int32_t getSlideIndex() const;
  void setSlideIndex(int32_t index);
  void setMaxSlides(int32_t maxSlides);
  int32_t getMaxSlides() const;

private:
  int32_t slideIndex_;
  int32_t maxSlides_;
};

// ---------------- GAME MODE ----------------
enum class GameEvent : uint8_t {
  None = 0,
  Ignored,
  Success,
  WrongGesture,
  TimeoutMiss,
  GameOver,
  NewChallenge
};

struct GameAction {
  GameEvent event;
  uint32_t scoreDelta;
  uint32_t totalScore;
  uint8_t lives;
  uint32_t combo;
  bool gameOver;
  Gesture expectedGesture;
  const char* description;
};

class GameModeHandler {
public:
  GameModeHandler();
  void reset(uint8_t initialLives = 3);
  void startChallenge(Gesture target, uint32_t durationMs, uint32_t nowMs);
  GameAction handleGesture(Gesture gesture, uint32_t nowMs);
  GameAction update(uint32_t nowMs);

  bool isChallengeActive() const;
  bool isGameOver() const;
  uint32_t getScore() const;
  uint8_t getLives() const;
  uint32_t getCombo() const;
  Gesture getCurrentChallenge() const;
  uint32_t getTimeRemainingMs(uint32_t nowMs) const;

private:
  uint32_t score_;
  uint8_t lives_;
  uint32_t combo_;
  uint32_t maxCombo_;
  Gesture currentChallenge_;
  uint32_t challengeStartMs_;
  uint32_t challengeDurationMs_;
  bool challengeActive_;
  bool gameOver_;
};

// ---------------- CUSTOM MODE ----------------
typedef void (*CustomActionFn)(uint32_t actionId, const char* name, void* userData);

struct CustomAction {
  bool triggered;
  uint32_t actionId;
  const char* actionName;
  const char* description;
};

constexpr size_t kMaxCustomBindings = 16;
constexpr size_t kMaxCustomNameLen = 24;

struct CustomBinding {
  Gesture gesture;
  uint32_t actionId;
  char name[kMaxCustomNameLen];
  CustomActionFn fn;
  void* userData;
};

class CustomModeHandler {
public:
  CustomModeHandler();
  void clearBindings();
  bool bindGesture(Gesture g, uint32_t actionId, const char* name, CustomActionFn fn = nullptr, void* userData = nullptr);
  bool unbindGesture(Gesture g);
  CustomAction handleGesture(Gesture gesture);
  size_t getBindingCount() const;
  const CustomBinding* getBinding(size_t index) const;
  const CustomBinding* findBindingByGesture(Gesture g) const;

private:
  CustomBinding bindings_[kMaxCustomBindings];
  size_t bindingCount_;
};

// ---------------- UNIFIED DISPATCH RESULT ----------------
struct DispatchResult {
  OperatingMode mode;
  bool actionTriggered;  // Strictly FALSE for Unknown or rejected gestures
  const char* description;

  RobotAction robot;
  SmartControlAction smartControl;
  PresentationAction presentation;
  GameAction game;
  macro_engine::StepResult macro;
  CustomAction custom;
};

class ModeActionListener {
public:
  virtual ~ModeActionListener() = default;
  virtual void onRobotAction(const RobotAction& action) { (void)action; }
  virtual void onSmartControlAction(const SmartControlAction& action) { (void)action; }
  virtual void onPresentationAction(const PresentationAction& action) { (void)action; }
  virtual void onGameAction(const GameAction& action) { (void)action; }
  virtual void onMacroAction(const macro_engine::StepResult& action) { (void)action; }
  virtual void onCustomAction(const CustomAction& action) { (void)action; }
};

// ---------------- MODE MANAGER ----------------
class ModeManager {
public:
  ModeManager();

  // Mode management
  bool setMode(OperatingMode mode);
  bool setModeByName(const char* name);
  OperatingMode getMode() const;
  const char* getModeName() const;
  void reset();

  // Main dispatch entry points
  DispatchResult dispatch(Gesture gesture, uint32_t nowMs = 0);
  DispatchResult dispatch(const GestureInput& input);

  // Periodic tick for timed modes (Game, Macro timeouts)
  DispatchResult update(uint32_t nowMs);

  // Sub-handlers
  RobotModeHandler& robot();
  const RobotModeHandler& robot() const;

  SmartControlModeHandler& smartControl();
  const SmartControlModeHandler& smartControl() const;

  PresentationModeHandler& presentation();
  const PresentationModeHandler& presentation() const;

  GameModeHandler& game();
  const GameModeHandler& game() const;

  macro_engine::MacroEngine& macroEngine();
  const macro_engine::MacroEngine& macroEngine() const;

  CustomModeHandler& custom();
  const CustomModeHandler& custom() const;

  // Listener
  void setActionListener(ModeActionListener* listener);

  // LCD 16x2 presentation helper
  lcd_ui::Frame renderStatus(const char* extra = nullptr) const;

private:
  OperatingMode mode_;
  RobotModeHandler robotHandler_;
  SmartControlModeHandler smartControlHandler_;
  PresentationModeHandler presentationHandler_;
  GameModeHandler gameHandler_;
  macro_engine::MacroEngine macroEngine_;
  CustomModeHandler customHandler_;
  ModeActionListener* listener_;
};

}  // namespace modes
