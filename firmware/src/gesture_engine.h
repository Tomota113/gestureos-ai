#pragma once

#include <stddef.h>
#include <stdint.h>

namespace gesture_engine {

constexpr size_t kMaxWindowSamples = 256;
constexpr size_t kMaxPreRollSamples = 32;

struct Sample {
  uint64_t timestampUs;
  float axes[6];  // acceleration in g, gyroscope in degrees/s; gravity retained
};

struct Config {
  float startEnergy;
  float stopEnergy;
  float gyroScaleDps;
  size_t minSamples;
  size_t maxSamples;
  size_t quietSamples;
  size_t preRollSamples;
  uint64_t maxGapUs;  // reject missing or stalled samples during a stream
};

enum class Event : uint8_t {
  None, Started, Completed, TooShort, TooLong, InvalidSample, InvalidConfig
};

// Candidate detection only. No labels, model scores or action authorization.
class Engine {
 public:
  explicit Engine(const Config& config);
  bool valid() const;
  void reset();
  Event feed(const Sample& sample);
  bool recording() const;
  const Sample* completedWindow() const;  // valid until the next Started/reset
  size_t completedSize() const;

 private:
  Config config_;
  bool valid_;
  bool recording_;
  bool completed_;
  bool seenTimestamp_;
  uint64_t lastTimestampUs_;
  size_t windowCount_;
  size_t quietCount_;
  Sample window_[kMaxWindowSamples];
  Sample preRoll_[kMaxPreRollSamples];
  size_t preRollCount_;
  size_t preRollNext_;

  void savePreRoll(const Sample& sample);
  void beginWindow(const Sample& sample);
};

}  // namespace gesture_engine
