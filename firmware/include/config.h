#pragma once
#include <stdint.h>

namespace config {
constexpr int kSda = 21;
constexpr int kScl = 22;
constexpr uint32_t kI2cHz = 100000;
constexpr uint32_t kSerialBaud = 230400;
constexpr uint16_t kSampleRateHz = 100;
constexpr uint8_t kDivider = 1000 / kSampleRateHz - 1;
static_assert(kSampleRateHz == 50 || kSampleRateHz == 100,
              "The smoke test supports 50 or 100 Hz");
}  // namespace config
