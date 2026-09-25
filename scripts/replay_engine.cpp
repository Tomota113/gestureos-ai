#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>

#include "gesture_engine.h"

namespace {
bool parseFloat(const char* text, float& value) {
  char* end = nullptr;
  errno = 0;
  value = std::strtof(text, &end);
  return errno == 0 && end != text && *end == '\0' && std::isfinite(value);
}

bool parseUnsigned(const char* text, unsigned long long& value) {
  if (*text == '-' || *text == '+') return false;
  char* end = nullptr;
  errno = 0;
  value = std::strtoull(text, &end, 10);
  return errno == 0 && end != text && *end == '\0';
}

const char* name(gesture_engine::Event event) {
  using gesture_engine::Event;
  switch (event) {
    case Event::Started: return "started";
    case Event::Completed: return "completed";
    case Event::TooShort: return "too_short";
    case Event::TooLong: return "too_long";
    case Event::InvalidSample: return "invalid_sample";
    case Event::InvalidConfig: return "invalid_config";
    case Event::None: return "none";
  }
  return "unknown";
}
}  // namespace

int main(int argc, char** argv) {
  if (argc != 9) {
    std::cerr << "Expected: start stop gyro_scale min max quiet pre_roll max_gap_us\n";
    return 2;
  }
  gesture_engine::Config config{};
  unsigned long long integers[5]{};
  if (!parseFloat(argv[1], config.startEnergy) ||
      !parseFloat(argv[2], config.stopEnergy) ||
      !parseFloat(argv[3], config.gyroScaleDps)) {
    std::cerr << "Invalid numeric threshold\n";
    return 2;
  }
  for (int i = 0; i < 5; ++i) {
    if (!parseUnsigned(argv[i + 4], integers[i])) {
      std::cerr << "Invalid integer configuration\n";
      return 2;
    }
  }
  if (integers[0] > gesture_engine::kMaxWindowSamples ||
      integers[1] > gesture_engine::kMaxWindowSamples ||
      integers[2] > gesture_engine::kMaxWindowSamples ||
      integers[3] > gesture_engine::kMaxPreRollSamples) {
    std::cerr << "Configuration exceeds engine capacity\n";
    return 2;
  }
  config.minSamples = static_cast<size_t>(integers[0]);
  config.maxSamples = static_cast<size_t>(integers[1]);
  config.quietSamples = static_cast<size_t>(integers[2]);
  config.preRollSamples = static_cast<size_t>(integers[3]);
  config.maxGapUs = static_cast<uint64_t>(integers[4]);
  gesture_engine::Engine engine(config);
  if (!engine.valid()) {
    std::cerr << "Engine rejected configuration\n";
    return 2;
  }

  std::string line;
  size_t count = 0;
  uint64_t lastTimestampUs = 0;
  while (std::getline(std::cin, line)) {
    if (++count > 500) {
      std::cerr << "Replay exceeds 500 samples\n";
      return 2;
    }
    std::istringstream stream(line);
    gesture_engine::Sample sample{};
    std::string extra;
    if (!(stream >> sample.timestampUs >> sample.axes[0] >> sample.axes[1] >>
          sample.axes[2] >> sample.axes[3] >> sample.axes[4] >>
          sample.axes[5]) || (stream >> extra)) {
      std::cerr << "Malformed replay sample at line " << count << "\n";
      return 2;
    }
    lastTimestampUs = sample.timestampUs;
    const gesture_engine::Event event = engine.feed(sample);
    if (event == gesture_engine::Event::None) continue;
    std::cout << "{\"event\":\"" << name(event) << "\",\"sample_index\":"
              << count - 1 << ",\"timestamp_us\":" << sample.timestampUs;
    if (event == gesture_engine::Event::Completed) {
      const gesture_engine::Sample* window = engine.completedWindow();
      const size_t size = engine.completedSize();
      std::cout << ",\"window_samples\":" << size
                << ",\"window_start_us\":" << window[0].timestampUs
                << ",\"window_end_us\":" << window[size - 1].timestampUs;
    }
    std::cout << "}\n";
    if (event == gesture_engine::Event::InvalidConfig) return 2;
  }
  if (count == 0) {
    std::cerr << "Empty replay stream\n";
    return 2;
  }
  if (engine.recording()) {
    std::cout << "{\"event\":\"unfinished_at_end\",\"sample_index\":"
              << count - 1 << ",\"timestamp_us\":" << lastTimestampUs << "}\n";
  }
  return 0;
}
