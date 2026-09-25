#pragma once

#include <initializer_list>
#include <stddef.h>
#include <stdint.h>

namespace macro_engine {

enum class Gesture : uint8_t {
  Unknown = 0,
  Left,
  Right,
  Up,
  Down,
  Circle,
  CircleCcw,
  Shake,
  Push,
  Stop
};

const char* gestureToString(Gesture gesture);
Gesture gestureFromString(const char* name);
bool isDirectional(Gesture gesture);

constexpr size_t kMaxSequenceLength = 8;
constexpr size_t kMaxMacros = 16;
constexpr size_t kMaxMacroNameLen = 24;
constexpr uint32_t kDefaultTimeoutMs = 2000;

enum class StepStatus : uint8_t {
  Ignored = 0,    // Unknown or rejected gesture; no action, state unchanged
  Progress,       // Gesture matched next step in a sequence; awaiting completion
  Completed,      // Full sequence recognized; macro action safely dispatched
  Cancelled,      // Invalid transition or unexpected movement; sequence aborted
  Timeout         // Inter-gesture timeout expired; sequence reset
};

struct MacroDefinition {
  uint32_t id;
  char name[kMaxMacroNameLen];
  Gesture sequence[kMaxSequenceLength];
  size_t length;
  uint32_t actionPayload;
};

struct StepResult {
  StepStatus status;
  bool actionTriggered;          // true ONLY if status == Completed
  uint32_t macroId;              // Valid when actionTriggered is true
  const char* macroName;         // Valid when actionTriggered is true
  uint32_t actionPayload;        // Valid when actionTriggered is true
  size_t currentStep;            // Current sequence step
  size_t expectedTotal;          // Target sequence length for candidate
  const char* message;
};

typedef void (*MacroDispatchCallback)(const StepResult& result, void* userData);

class MacroEngine {
public:
  MacroEngine();

  // Configuration
  void setTimeoutMs(uint32_t timeoutMs);
  uint32_t getTimeoutMs() const;
  void setAbortOnUnknown(bool abort);
  bool getAbortOnUnknown() const;

  // Macro registration
  bool registerMacro(uint32_t id, const char* name, const Gesture* sequence, size_t length, uint32_t payload = 0);
  bool registerMacro(uint32_t id, const char* name, std::initializer_list<Gesture> sequence, uint32_t payload = 0);
  bool unregisterMacro(uint32_t id);
  void clearMacros();
  size_t getMacroCount() const;
  const MacroDefinition* getMacro(size_t index) const;
  const MacroDefinition* findMacroById(uint32_t id) const;
  const MacroDefinition* findMacroByName(const char* name) const;

  // State machine feeding
  StepResult feed(Gesture gesture, uint32_t nowMs = 0);
  StepResult update(uint32_t nowMs);
  StepResult abort();
  void reset();

  // State inspection
  bool isInSequence() const;
  size_t getCurrentStep() const;
  uint32_t getLastGestureTimeMs() const;
  const Gesture* getCurrentBuffer() const;

  // Dispatch callback
  void setDispatchCallback(MacroDispatchCallback callback, void* userData = nullptr);

private:
  MacroDefinition macros_[kMaxMacros];
  size_t macroCount_;

  Gesture buffer_[kMaxSequenceLength];
  size_t currentStep_;
  uint32_t lastGestureTimeMs_;
  uint32_t timeoutMs_;
  bool abortOnUnknown_;

  MacroDispatchCallback callback_;
  void* callbackUserData_;

  bool matchesPrefix(const MacroDefinition& macro, const Gesture* sequence, size_t len) const;
};

}  // namespace macro_engine
