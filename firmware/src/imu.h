#pragma once
#include <Arduino.h>

struct ImuSample {
  int64_t timestampUs;
  float axes[6];  // ax, ay, az in g; gx, gy, gz in degrees/s. Gravity retained.
};

enum class ReadResult { NoData, Sample, Error };

class Imu {
 public:
  bool begin();
  ReadResult read(ImuSample& sample);
  uint8_t address() const { return address_; }

 private:
  uint8_t address_ = 0;
  bool readBytes(uint8_t reg, uint8_t* data, size_t size);
  bool writeChecked(uint8_t reg, uint8_t value);
};
