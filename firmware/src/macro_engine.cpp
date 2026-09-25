#include "macro_engine.h"
#include <string.h>

namespace macro_engine {

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
}  // namespace

const char* gestureToString(Gesture gesture) {
  switch (gesture) {
    case Gesture::Left:
      return "LEFT";
    case Gesture::Right:
      return "RIGHT";
    case Gesture::Up:
      return "UP";
    case Gesture::Down:
      return "DOWN";
    case Gesture::Circle:
      return "CIRCLE";
    case Gesture::CircleCcw:
      return "CIRCLE_CCW";
    case Gesture::Shake:
      return "SHAKE";
    case Gesture::Push:
      return "PUSH";
    case Gesture::Stop:
      return "STOP";
    case Gesture::Unknown:
    default:
      return "UNKNOWN";
  }
}

Gesture gestureFromString(const char* name) {
  if (!name) return Gesture::Unknown;
  if (strCaseEqual(name, "left") || strCaseEqual(name, "swipe_left")) return Gesture::Left;
  if (strCaseEqual(name, "right") || strCaseEqual(name, "swipe_right")) return Gesture::Right;
  if (strCaseEqual(name, "up") || strCaseEqual(name, "swipe_up")) return Gesture::Up;
  if (strCaseEqual(name, "down") || strCaseEqual(name, "swipe_down")) return Gesture::Down;
  if (strCaseEqual(name, "circle") || strCaseEqual(name, "circle_clockwise") || strCaseEqual(name, "circle_cw")) return Gesture::Circle;
  if (strCaseEqual(name, "circle_ccw") || strCaseEqual(name, "circle_counter_clockwise")) return Gesture::CircleCcw;
  if (strCaseEqual(name, "shake")) return Gesture::Shake;
  if (strCaseEqual(name, "push")) return Gesture::Push;
  if (strCaseEqual(name, "stop") || strCaseEqual(name, "x")) return Gesture::Stop;
  return Gesture::Unknown;
}

bool isDirectional(Gesture gesture) {
  switch (gesture) {
    case Gesture::Left:
    case Gesture::Right:
    case Gesture::Up:
    case Gesture::Down:
    case Gesture::Circle:
    case Gesture::CircleCcw:
      return true;
    default:
      return false;
  }
}

MacroEngine::MacroEngine()
    : macroCount_(0),
      currentStep_(0),
      lastGestureTimeMs_(0),
      timeoutMs_(kDefaultTimeoutMs),
      abortOnUnknown_(true),
      callback_(nullptr),
      callbackUserData_(nullptr) {
  memset(macros_, 0, sizeof(macros_));
  memset(buffer_, 0, sizeof(buffer_));
}

void MacroEngine::setTimeoutMs(uint32_t timeoutMs) {
  timeoutMs_ = timeoutMs;
}

uint32_t MacroEngine::getTimeoutMs() const {
  return timeoutMs_;
}

void MacroEngine::setAbortOnUnknown(bool abort) {
  abortOnUnknown_ = abort;
}

bool MacroEngine::getAbortOnUnknown() const {
  return abortOnUnknown_;
}

bool MacroEngine::registerMacro(uint32_t id, const char* name, const Gesture* sequence, size_t length, uint32_t payload) {
  if (id == 0 || length == 0 || length > kMaxSequenceLength || !sequence || !name || name[0] == '\0') {
    return false;
  }
  // Prevent registering sequences containing Unknown or out-of-range gestures
  for (size_t i = 0; i < length; ++i) {
    if (sequence[i] == Gesture::Unknown ||
        static_cast<uint8_t>(sequence[i]) > static_cast<uint8_t>(Gesture::Stop)) {
      return false;
    }
  }

  // Check for duplicate sequence or prefix collision with other macros
  for (size_t i = 0; i < macroCount_; ++i) {
    if (macros_[i].id == id) continue;  // Updating an existing macro ID is handled below

    // Exact duplicate sequence check
    if (macros_[i].length == length) {
      bool same = true;
      for (size_t j = 0; j < length; ++j) {
        if (macros_[i].sequence[j] != sequence[j]) {
          same = false;
          break;
        }
      }
      if (same) return false;
    }

    // Prefix collision check: one sequence cannot be a strict prefix of another
    size_t minLen = (macros_[i].length < length) ? macros_[i].length : length;
    bool prefixMatch = true;
    for (size_t j = 0; j < minLen; ++j) {
      if (macros_[i].sequence[j] != sequence[j]) {
        prefixMatch = false;
        break;
      }
    }
    if (prefixMatch) {
      return false;
    }
  }

  // If macro with same ID already exists, update in place
  for (size_t i = 0; i < macroCount_; ++i) {
    if (macros_[i].id == id) {
      macros_[i].length = length;
      macros_[i].actionPayload = payload;
      strncpy(macros_[i].name, name, kMaxMacroNameLen - 1);
      macros_[i].name[kMaxMacroNameLen - 1] = '\0';
      for (size_t j = 0; j < length; ++j) {
        macros_[i].sequence[j] = sequence[j];
      }

      // If a sequence was in progress, verify if any remaining macro matches current buffer
      if (currentStep_ > 0) {
        bool candidateStillMatches = false;
        for (size_t k = 0; k < macroCount_; ++k) {
          if (matchesPrefix(macros_[k], buffer_, currentStep_)) {
            candidateStillMatches = true;
            break;
          }
        }
        if (!candidateStillMatches) {
          currentStep_ = 0;
          memset(buffer_, 0, sizeof(buffer_));
        }
      }

      return true;
    }
  }

  if (macroCount_ >= kMaxMacros) {
    return false;
  }

  MacroDefinition& m = macros_[macroCount_];
  m.id = id;
  m.length = length;
  m.actionPayload = payload;
  strncpy(m.name, name, kMaxMacroNameLen - 1);
  m.name[kMaxMacroNameLen - 1] = '\0';
  for (size_t i = 0; i < length; ++i) {
    m.sequence[i] = sequence[i];
  }
  ++macroCount_;
  return true;
}

bool MacroEngine::registerMacro(uint32_t id, const char* name, std::initializer_list<Gesture> sequence, uint32_t payload) {
  Gesture arr[kMaxSequenceLength];
  size_t len = 0;
  for (auto g : sequence) {
    if (len >= kMaxSequenceLength) return false;
    arr[len++] = g;
  }
  return registerMacro(id, name, arr, len, payload);
}

bool MacroEngine::unregisterMacro(uint32_t id) {
  for (size_t i = 0; i < macroCount_; ++i) {
    if (macros_[i].id == id) {
      for (size_t j = i; j + 1 < macroCount_; ++j) {
        macros_[j] = macros_[j + 1];
      }
      --macroCount_;
      memset(&macros_[macroCount_], 0, sizeof(MacroDefinition));

      // If a sequence was in progress, verify if any remaining macro matches current buffer
      if (currentStep_ > 0) {
        bool candidateStillMatches = false;
        for (size_t k = 0; k < macroCount_; ++k) {
          if (matchesPrefix(macros_[k], buffer_, currentStep_)) {
            candidateStillMatches = true;
            break;
          }
        }
        if (!candidateStillMatches) {
          currentStep_ = 0;
          memset(buffer_, 0, sizeof(buffer_));
        }
      }

      return true;
    }
  }
  return false;
}

void MacroEngine::clearMacros() {
  macroCount_ = 0;
  currentStep_ = 0;
  lastGestureTimeMs_ = 0;
  memset(macros_, 0, sizeof(macros_));
  memset(buffer_, 0, sizeof(buffer_));
}

size_t MacroEngine::getMacroCount() const {
  return macroCount_;
}

const MacroDefinition* MacroEngine::getMacro(size_t index) const {
  if (index >= macroCount_) return nullptr;
  return &macros_[index];
}

const MacroDefinition* MacroEngine::findMacroById(uint32_t id) const {
  for (size_t i = 0; i < macroCount_; ++i) {
    if (macros_[i].id == id) return &macros_[i];
  }
  return nullptr;
}

const MacroDefinition* MacroEngine::findMacroByName(const char* name) const {
  if (!name) return nullptr;
  for (size_t i = 0; i < macroCount_; ++i) {
    if (strCaseEqual(macros_[i].name, name)) return &macros_[i];
  }
  return nullptr;
}

bool MacroEngine::matchesPrefix(const MacroDefinition& macro, const Gesture* sequence, size_t len) const {
  if (macro.length < len) return false;
  for (size_t i = 0; i < len; ++i) {
    if (macro.sequence[i] != sequence[i]) return false;
  }
  return true;
}

StepResult MacroEngine::feed(Gesture gesture, uint32_t nowMs) {
  // UNKNOWN rejection: must never trigger any action or actuator command
  if (gesture == Gesture::Unknown ||
      static_cast<uint8_t>(gesture) > static_cast<uint8_t>(Gesture::Stop)) {
    if (currentStep_ > 0 && abortOnUnknown_) {
      currentStep_ = 0;
      memset(buffer_, 0, sizeof(buffer_));
      StepResult res{};
      res.status = StepStatus::Cancelled;
      res.actionTriggered = false;
      res.macroId = 0;
      res.macroName = nullptr;
      res.actionPayload = 0;
      res.currentStep = 0;
      res.expectedTotal = 0;
      res.message = "ABORTED_ON_UNKNOWN";
      return res;
    }
    StepResult res{};
    res.status = StepStatus::Ignored;
    res.actionTriggered = false;
    res.macroId = 0;
    res.macroName = nullptr;
    res.actionPayload = 0;
    res.currentStep = currentStep_;
    res.expectedTotal = 0;
    res.message = "UNKNOWN_IGNORED";
    return res;
  }

  // Handle omitted timestamp (nowMs = 0) when sequence is already active
  if (nowMs == 0 && lastGestureTimeMs_ > 0) {
    nowMs = lastGestureTimeMs_;
  }

  // Inter-gesture timeout window check (robust to 32-bit unsigned rollover)
  if (currentStep_ > 0 && timeoutMs_ > 0) {
    uint32_t elapsed = nowMs - lastGestureTimeMs_;
    if (elapsed >= timeoutMs_) {
      currentStep_ = 0;
      memset(buffer_, 0, sizeof(buffer_));
    }
  }

  // Defensive array bounds check
  if (currentStep_ >= kMaxSequenceLength) {
    currentStep_ = 0;
    memset(buffer_, 0, sizeof(buffer_));
  }

  // Tentative sequence candidate
  buffer_[currentStep_] = gesture;
  size_t testLen = currentStep_ + 1;

  const MacroDefinition* fullMatch = nullptr;
  size_t candidateCount = 0;
  size_t minExpected = 0;

  for (size_t i = 0; i < macroCount_; ++i) {
    if (matchesPrefix(macros_[i], buffer_, testLen)) {
      candidateCount++;
      if (macros_[i].length == testLen) {
        fullMatch = &macros_[i];
      } else {
        if (minExpected == 0 || macros_[i].length < minExpected) {
          minExpected = macros_[i].length;
        }
      }
    }
  }

  if (fullMatch != nullptr) {
    // Full sequence recognized: safe action dispatch
    StepResult res{};
    res.status = StepStatus::Completed;
    res.actionTriggered = true;
    res.macroId = fullMatch->id;
    res.macroName = fullMatch->name;
    res.actionPayload = fullMatch->actionPayload;
    res.currentStep = testLen;
    res.expectedTotal = testLen;
    res.message = "MACRO_DISPATCHED";

    currentStep_ = 0;  // Reset state machine after full completion
    memset(buffer_, 0, sizeof(buffer_));
    if (callback_) {
      callback_(res, callbackUserData_);
    }
    return res;
  }

  if (candidateCount > 0) {
    // Sequence in progress
    currentStep_ = testLen;
    lastGestureTimeMs_ = nowMs;

    StepResult res{};
    res.status = StepStatus::Progress;
    res.actionTriggered = false;
    res.macroId = 0;
    res.macroName = nullptr;
    res.actionPayload = 0;
    res.currentStep = currentStep_;
    res.expectedTotal = minExpected;
    res.message = "SEQUENCE_PROGRESS";
    return res;
  }

  // No candidates match: invalid transition or unexpected movement
  if (currentStep_ > 0) {
    currentStep_ = 0;
    memset(buffer_, 0, sizeof(buffer_));
    StepResult res{};
    res.status = StepStatus::Cancelled;
    res.actionTriggered = false;
    res.macroId = 0;
    res.macroName = nullptr;
    res.actionPayload = 0;
    res.currentStep = 0;
    res.expectedTotal = 0;
    res.message = "INVALID_TRANSITION";
    return res;
  }

  // At step 0, no macro starts with this gesture
  memset(buffer_, 0, sizeof(buffer_));
  StepResult res{};
  res.status = StepStatus::Ignored;
  res.actionTriggered = false;
  res.macroId = 0;
  res.macroName = nullptr;
  res.actionPayload = 0;
  res.currentStep = 0;
  res.expectedTotal = 0;
  res.message = "NO_MATCHING_MACRO";
  return res;
}

StepResult MacroEngine::update(uint32_t nowMs) {
  if (currentStep_ > 0 && timeoutMs_ > 0) {
    uint32_t elapsed = nowMs - lastGestureTimeMs_;
    if (elapsed >= timeoutMs_) {
      currentStep_ = 0;
      memset(buffer_, 0, sizeof(buffer_));
      StepResult res{};
      res.status = StepStatus::Timeout;
      res.actionTriggered = false;
      res.macroId = 0;
      res.macroName = nullptr;
      res.actionPayload = 0;
      res.currentStep = 0;
      res.expectedTotal = 0;
      res.message = "TIMEOUT_RESET";
      return res;
    }
  }

  size_t minExpected = 0;
  if (currentStep_ > 0) {
    for (size_t i = 0; i < macroCount_; ++i) {
      if (matchesPrefix(macros_[i], buffer_, currentStep_)) {
        if (minExpected == 0 || macros_[i].length < minExpected) {
          minExpected = macros_[i].length;
        }
      }
    }
  }

  StepResult res{};
  res.status = (currentStep_ > 0) ? StepStatus::Progress : StepStatus::Ignored;
  res.actionTriggered = false;
  res.macroId = 0;
  res.macroName = nullptr;
  res.actionPayload = 0;
  res.currentStep = currentStep_;
  res.expectedTotal = minExpected;
  res.message = "TICK_OK";
  return res;
}

StepResult MacroEngine::abort() {
  bool wasInSeq = (currentStep_ > 0);
  currentStep_ = 0;
  memset(buffer_, 0, sizeof(buffer_));
  StepResult res{};
  res.status = wasInSeq ? StepStatus::Cancelled : StepStatus::Ignored;
  res.actionTriggered = false;
  res.macroId = 0;
  res.macroName = nullptr;
  res.actionPayload = 0;
  res.currentStep = 0;
  res.expectedTotal = 0;
  res.message = wasInSeq ? "ABORTED_MANUAL" : "IDLE";
  return res;
}

void MacroEngine::reset() {
  currentStep_ = 0;
  lastGestureTimeMs_ = 0;
  memset(buffer_, 0, sizeof(buffer_));
}

bool MacroEngine::isInSequence() const {
  return currentStep_ > 0;
}

size_t MacroEngine::getCurrentStep() const {
  return currentStep_;
}

uint32_t MacroEngine::getLastGestureTimeMs() const {
  return lastGestureTimeMs_;
}

const Gesture* MacroEngine::getCurrentBuffer() const {
  return buffer_;
}

void MacroEngine::setDispatchCallback(MacroDispatchCallback callback, void* userData) {
  callback_ = callback;
  callbackUserData_ = userData;
}

}  // namespace macro_engine
