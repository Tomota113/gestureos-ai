#include "imu.h"
#include <Wire.h>
#include <esp_timer.h>
#include "config.h"

namespace {
int16_t signedWord(const uint8_t* bytes) {
  const uint16_t value = (uint16_t(bytes[0]) << 8) | bytes[1];
  return value <= 32767 ? int16_t(value) : int16_t(int32_t(value) - 65536);
}
}  // namespace

bool Imu::readBytes(uint8_t reg, uint8_t* data, size_t size) {
  Wire.beginTransmission(address_);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(address_, size, true) != size) return false;
  for (size_t i = 0; i < size; ++i) data[i] = Wire.read();
  return true;
}

bool Imu::writeChecked(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(address_);
  Wire.write(reg);
  Wire.write(value);
  if (Wire.endTransmission() != 0) return false;
  uint8_t actual = 0;
  return readBytes(reg, &actual, 1) && actual == value;
}

bool Imu::begin() {
  if (!Wire.begin(config::kSda, config::kScl, config::kI2cHz)) return false;
  Wire.setTimeOut(10);
  for (uint8_t candidate : {uint8_t(0x68), uint8_t(0x69)}) {
    address_ = candidate;
    uint8_t identity = 0;
    if (readBytes(0x75, &identity, 1) && identity == 0x68) break;
    address_ = 0;
  }
  if (address_ == 0) return false;

  // Reset explicitly; do not compare the self-clearing reset bit on read-back.
  Wire.beginTransmission(address_);
  Wire.write(0x6B);
  Wire.write(0x80);
  if (Wire.endTransmission() != 0) return false;
  delay(100);
  if (!writeChecked(0x6B, 0x01)) return false;  // Wake, X gyro PLL.
  delay(100);
  // DLPF=3; 1 kHz source divided to desired rate; +/-500 dps; +/-4 g.
  return writeChecked(0x6C, 0x00) && writeChecked(0x1A, 0x03) &&
         writeChecked(0x19, config::kDivider) && writeChecked(0x1B, 0x08) &&
         writeChecked(0x1C, 0x08) && writeChecked(0x38, 0x01);
}

ReadResult Imu::read(ImuSample& sample) {
  uint8_t status = 0;
  if (!readBytes(0x3A, &status, 1)) return ReadResult::Error;
  if ((status & 1) == 0) return ReadResult::NoData;
  uint8_t bytes[14];
  // Timestamp is host-MCU read time, NOT a hardware interrupt timestamp.
  sample.timestampUs = esp_timer_get_time();
  if (!readBytes(0x3B, bytes, sizeof(bytes))) return ReadResult::Error;
  for (int axis = 0; axis < 3; ++axis) {
    sample.axes[axis] = signedWord(bytes + 2 * axis) / 8192.0f;
    sample.axes[axis + 3] = signedWord(bytes + 8 + 2 * axis) / 65.5f;
  }
  return ReadResult::Sample;
}
