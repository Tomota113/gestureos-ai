#include <Arduino.h>
#include "capture_protocol.h"
#include "config.h"
#include "imu.h"

namespace {
Imu imu;
bool sensorReady = false;
bool active = false;
capture_protocol::Request request{};
uint16_t sequence = 0;
uint32_t checksum = 0;
uint32_t startedMs = 0;
char command[128];
size_t commandLength = 0;
bool overflow = false;

void error(const char* reason) {
  Serial.printf("{\"type\":\"error\",\"reason\":\"%s\"}\n", reason);
}

void handleCommand(const char* line) {
  if (strcmp(line, "ABORT") == 0) {
    active = false;
    error("aborted");
    return;
  }
  if (active) { error("busy"); return; }
  if (!sensorReady) { error("imu_not_ready"); return; }
  if (!capture_protocol::parseRequest(line, request)) {
    error("invalid_capture_command");
    return;
  }
  sequence = 0;
  checksum = 0;
  Serial.printf("{\"type\":\"begin\",\"protocol\":\"gestureos-capture-v1\","
                "\"capture_id\":\"%s\",\"label\":\"%s\",\"samples\":%u,"
                "\"rate_hz\":%u,\"accel_unit\":\"g\",\"gyro_unit\":\"deg_s\","
                "\"calibrated\":false,\"accel_range_g\":4,\"gyro_range_dps\":500}\n",
                request.id, request.label, request.samples, config::kSampleRateHz);
  startedMs = millis();
  active = true;
}

void readCommands() {
  // Limit work per loop so an input burst cannot starve the sensor indefinitely.
  for (unsigned i = 0; i < 64 && Serial.available(); ++i) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      command[commandLength] = 0;
      if (overflow) error("command_too_long");
      else handleCommand(command);
      commandLength = 0;
      overflow = false;
    } else if (c != '\r' && !overflow) {
      if (commandLength + 1 >= sizeof(command) || c < 32 || c > 126) overflow = true;
      else command[commandLength++] = c;
    }
  }
}

void captureSample() {
  if (millis() - startedMs > 5000u + request.samples * 1000u / config::kSampleRateHz) {
    active = false;
    error("capture_timeout");
    return;
  }
  ImuSample sample{};
  const auto result = imu.read(sample);
  if (result == ReadResult::Error) {
    active = false;
    error("i2c_read_failed");
    return;
  }
  if (result != ReadResult::Sample) return;
  char frame[160];
  const int length = snprintf(frame, sizeof(frame),
      "D,%u,%lld,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,0\n", sequence,
      static_cast<long long>(sample.timestampUs), sample.axes[0], sample.axes[1],
      sample.axes[2], sample.axes[3], sample.axes[4], sample.axes[5]);
  if (length <= 0 || static_cast<size_t>(length) >= sizeof(frame)) {
    active = false;
    error("frame_overflow");
    return;
  }
  checksum = capture_protocol::crc32(frame, length, checksum);
  Serial.write(reinterpret_cast<const uint8_t*>(frame), length);
  if (++sequence == request.samples) {
    Serial.printf("{\"type\":\"end\",\"capture_id\":\"%s\",\"samples\":%u,"
                  "\"crc32\":\"%08lx\"}\n", request.id, sequence,
                  static_cast<unsigned long>(checksum));
    active = false;
  }
}
}  // namespace

void setup() {
  Serial.begin(config::kSerialBaud);
  delay(300);
  sensorReady = imu.begin();
  if (!sensorReady) { error("imu_init_failed"); return; }
  Serial.printf("{\"type\":\"ready\",\"protocol\":\"gestureos-capture-v1\","
                "\"rate_hz\":%u,\"imu_address\":%u}\n",
                config::kSampleRateHz, imu.address());
}

void loop() {
  readCommands();
  if (active) captureSample();
  delay(1);
}
