#include "gesture_engine.h"

#include <cmath>

namespace gesture_engine {
namespace {

bool validConfig(const Config& c) {
  return std::isfinite(c.startEnergy) && std::isfinite(c.stopEnergy) &&
         std::isfinite(c.gyroScaleDps) && c.startEnergy > c.stopEnergy &&
         c.stopEnergy > 0 && c.gyroScaleDps > 0 &&
         c.minSamples >= 2 && c.minSamples <= c.maxSamples &&
         c.maxSamples <= kMaxWindowSamples && c.quietSamples >= 1 &&
         c.quietSamples < c.maxSamples && c.preRollSamples <= kMaxPreRollSamples &&
         c.preRollSamples < c.maxSamples &&
         c.maxGapUs > 0 &&
         c.minSamples > c.preRollSamples + c.quietSamples;
}

bool motionEnergy(const Sample& sample, const Config& config, double& energy) {
  for (float axis : sample.axes) {
    if (!std::isfinite(axis)) return false;
  }
  double accelSquared = 0;
  double gyroSquared = 0;
  for (size_t i = 0; i < 3; ++i) {
    accelSquared += double(sample.axes[i]) * sample.axes[i];
    gyroSquared += double(sample.axes[i + 3]) * sample.axes[i + 3];
  }
  energy = std::fabs(std::sqrt(accelSquared) - 1.0) +
           std::sqrt(gyroSquared) / config.gyroScaleDps;
  return std::isfinite(energy);
}

}  // namespace

Engine::Engine(const Config& config)
    : config_(config), valid_(validConfig(config)), recording_(false),
      completed_(false), seenTimestamp_(false), lastTimestampUs_(0),
      windowCount_(0), quietCount_(0), preRollCount_(0), preRollNext_(0) {}

bool Engine::valid() const { return valid_; }

void Engine::reset() {
  recording_ = false;
  completed_ = false;
  seenTimestamp_ = false;
  lastTimestampUs_ = 0;
  windowCount_ = 0;
  quietCount_ = 0;
  preRollCount_ = 0;
  preRollNext_ = 0;
}

void Engine::savePreRoll(const Sample& sample) {
  if (config_.preRollSamples == 0) return;
  preRoll_[preRollNext_] = sample;
  preRollNext_ = (preRollNext_ + 1) % config_.preRollSamples;
  if (preRollCount_ < config_.preRollSamples) ++preRollCount_;
}

void Engine::beginWindow(const Sample& sample) {
  windowCount_ = 0;
  const size_t first = preRollCount_ == config_.preRollSamples ? preRollNext_ : 0;
  for (size_t i = 0; i < preRollCount_; ++i) {
    window_[windowCount_++] = preRoll_[(first + i) % config_.preRollSamples];
  }
  window_[windowCount_++] = sample;
  preRollCount_ = 0;
  preRollNext_ = 0;
  quietCount_ = 0;
  completed_ = false;
  recording_ = true;
}

Event Engine::feed(const Sample& sample) {
  if (!valid_) return Event::InvalidConfig;
  double energy = 0;
  if ((seenTimestamp_ && (sample.timestampUs <= lastTimestampUs_ ||
                          sample.timestampUs - lastTimestampUs_ > config_.maxGapUs)) ||
      !motionEnergy(sample, config_, energy)) {
    reset();
    return Event::InvalidSample;
  }
  seenTimestamp_ = true;
  lastTimestampUs_ = sample.timestampUs;

  if (!recording_) {
    if (energy >= config_.startEnergy) {
      beginWindow(sample);
      return Event::Started;
    }
    savePreRoll(sample);
    return Event::None;
  }

  // The fixed capacity also bounds computation and memory on the ESP32.
  if (windowCount_ >= config_.maxSamples) {
    recording_ = false;
    completed_ = false;
    preRollCount_ = 0;
    return Event::TooLong;
  }
  window_[windowCount_++] = sample;
  quietCount_ = energy <= config_.stopEnergy ? quietCount_ + 1 : 0;
  if (quietCount_ >= config_.quietSamples) {
    recording_ = false;
    completed_ = windowCount_ >= config_.minSamples;
    preRollCount_ = 0;
    return completed_ ? Event::Completed : Event::TooShort;
  }
  if (windowCount_ >= config_.maxSamples) {
    recording_ = false;
    completed_ = false;
    preRollCount_ = 0;
    return Event::TooLong;
  }
  return Event::None;
}

bool Engine::recording() const { return recording_; }

const Sample* Engine::completedWindow() const {
  return completed_ ? window_ : nullptr;
}

size_t Engine::completedSize() const {
  return completed_ ? windowCount_ : 0;
}

}  // namespace gesture_engine
