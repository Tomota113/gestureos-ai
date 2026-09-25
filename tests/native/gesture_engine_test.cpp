#include <assert.h>
#include <limits>

#include "gesture_engine.h"

namespace {
gesture_engine::Sample sample(uint64_t time, float gyro = 0.0f) {
  return {time, {0.0f, 0.0f, 1.0f, gyro, 0.0f, 0.0f}};
}
}  // namespace

int main() {
  using namespace gesture_engine;
  const Config config{0.5f, 0.2f, 100.0f, 5, 8, 2, 2, 150};
  Engine engine(config);
  assert(engine.valid());
  assert(engine.feed(sample(100)) == Event::None);
  assert(engine.feed(sample(200)) == Event::None);
  assert(engine.feed(sample(300)) == Event::None);  // pre-roll keeps only 200, 300
  assert(engine.feed(sample(400, 100)) == Event::Started);
  assert(engine.recording());
  assert(engine.completedWindow() == nullptr);
  assert(engine.feed(sample(500, 100)) == Event::None);
  assert(engine.feed(sample(600, 30)) == Event::None);  // between stop and start
  assert(engine.feed(sample(700)) == Event::None);
  assert(engine.feed(sample(800)) == Event::Completed);
  assert(!engine.recording());
  assert(engine.completedSize() == 7);
  const Sample* window = engine.completedWindow();
  assert(window && window[0].timestampUs == 200 && window[1].timestampUs == 300);
  assert(window[2].timestampUs == 400 && window[6].timestampUs == 800);
  assert(engine.feed(sample(900)) == Event::None);
  assert(engine.completedWindow() == window);  // retained until next start
  assert(engine.feed(sample(1000, 100)) == Event::Started);
  assert(engine.completedWindow() == nullptr);

  engine.reset();
  assert(!engine.recording() && engine.completedSize() == 0);
  assert(engine.feed(sample(10, 100)) == Event::Started);
  assert(engine.feed(sample(10, 100)) == Event::InvalidSample);
  assert(!engine.recording());
  assert(engine.feed(sample(20, 100)) == Event::Started);
  Sample nan = sample(30);
  nan.axes[4] = std::numeric_limits<float>::quiet_NaN();
  assert(engine.feed(nan) == Event::InvalidSample);
  assert(engine.completedWindow() == nullptr);
  assert(engine.feed(sample(100)) == Event::None);
  assert(engine.feed(sample(300, 100)) == Event::InvalidSample);  // stream gap

  const Config shortConfig{0.5f, 0.2f, 100.0f, 5, 8, 2, 0, 150};
  Engine shortEngine(shortConfig);
  assert(shortEngine.valid());
  assert(shortEngine.feed(sample(1, 100)) == Event::Started);
  assert(shortEngine.feed(sample(2)) == Event::None);
  assert(shortEngine.feed(sample(3)) == Event::TooShort);
  assert(shortEngine.completedWindow() == nullptr);

  const Config longConfig{0.5f, 0.2f, 100.0f, 3, 4, 1, 0, 150};
  Engine longEngine(longConfig);
  assert(longEngine.valid());
  assert(longEngine.feed(sample(1, 100)) == Event::Started);
  assert(longEngine.feed(sample(2, 100)) == Event::None);
  assert(longEngine.feed(sample(3, 100)) == Event::None);
  assert(longEngine.feed(sample(4, 100)) == Event::TooLong);
  assert(!longEngine.recording() && longEngine.completedWindow() == nullptr);

  Config invalid = config;
  invalid.startEnergy = invalid.stopEnergy;
  Engine invalidEngine(invalid);
  assert(!invalidEngine.valid());
  assert(invalidEngine.feed(sample(1, 100)) == Event::InvalidConfig);
  invalid = config;
  invalid.maxSamples = kMaxWindowSamples + 1;
  assert(!Engine(invalid).valid());
  invalid = config;
  invalid.minSamples = invalid.preRollSamples + invalid.quietSamples;
  assert(!Engine(invalid).valid());
  invalid = config;
  invalid.maxGapUs = 0;
  assert(!Engine(invalid).valid());
  return 0;
}
