#include <Arduino.h>
#include "config.h"
#include "imu.h"

Imu imu;
bool ready = false;
uint32_t sequence = 0;
uint32_t errors = 0;
uint32_t lastDiagnosticMs = 0;

void setup() {
  Serial.begin(config::kSerialBaud);
  delay(300);
  Serial.printf("# gestureos-smoke-v1 rate_hz=%u accel=g gyro=deg_s uncalibrated=1\n",
                config::kSampleRateHz);
  ready = imu.begin();
  if (!ready) {
    Serial.println("# ERROR imu_init: check supply, wiring, address, WHO_AM_I");
    return;
  }
  Serial.printf("# imu_address=0x%02x sda=%d scl=%d dlpf=3 accel_range_g=4 gyro_range_dps=500\n",
                imu.address(), config::kSda, config::kScl);
  Serial.println("seq,timestamp_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,i2c_errors");
}

void loop() {
  if (!ready) {
    delay(1000);
    Serial.println("# ERROR imu_not_ready");
    return;
  }
  ImuSample sample{};
  const ReadResult result = imu.read(sample);
  if (result == ReadResult::Error) ++errors;
  if (result == ReadResult::Sample) {
    Serial.printf("%lu,%lld,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%lu\n",
                  static_cast<unsigned long>(sequence++),
                  static_cast<long long>(sample.timestampUs),
                  sample.axes[0], sample.axes[1], sample.axes[2],
                  sample.axes[3], sample.axes[4], sample.axes[5],
                  static_cast<unsigned long>(errors));
  }
  if (errors && millis() - lastDiagnosticMs >= 1000) {
    Serial.printf("# ERROR i2c_total=%lu\n", static_cast<unsigned long>(errors));
    lastDiagnosticMs = millis();
  }
  // DATA_RDY prevents intentionally rereading stale data. Gaps are measured
  // by the PC; this initial polling test has no FIFO overrun counter.
  delay(1);
}
