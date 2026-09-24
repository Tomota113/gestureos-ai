#include <assert.h>
#include <initializer_list>
#include <stdio.h>
#include <string.h>
#include "lcd_ui.h"

int main() {
  using namespace lcd_ui;
  const Frame boot = render(Screen::Boot);
  assert(strcmp(boot.top, "GESTUREOS AI    ") == 0);
  assert(strcmp(boot.bottom, "STARTING        ") == 0);
  const Frame ready = render(Screen::Ready);
  assert(strcmp(ready.bottom, "READY           ") == 0);
  const Frame recording = render(Screen::Recording, "circle_clockwise");
  assert(strcmp(recording.top, "RECORDING       ") == 0);
  assert(strcmp(recording.bottom, "CIRCLE CLOCKWISE") == 0);
  const Frame accepted = render(Screen::Accepted, "very_long_gesture_name");
  assert(strcmp(accepted.top, "VERY LONG GESTUR") == 0);
  assert(strcmp(accepted.bottom, "ACCEPTED        ") == 0);
  const Frame unknown = render(Screen::Unknown, "0.99");
  assert(strcmp(unknown.top, "UNKNOWN         ") == 0);
  assert(strcmp(unknown.bottom, "TRY AGAIN       ") == 0);
  const Frame error = render(Screen::SensorError, "i2c\nfailed");
  assert(strcmp(error.top, "SENSOR ERROR    ") == 0);
  assert(strcmp(error.bottom, "I2C?FAILED      ") == 0);
  for (const Frame* frame : {&boot, &ready, &recording, &accepted, &unknown, &error}) {
    assert(strlen(frame->top) == kColumns && strlen(frame->bottom) == kColumns);
    assert(frame->top[kColumns] == '\0' && frame->bottom[kColumns] == '\0');
    assert(strchr(frame->top, '%') == nullptr && strchr(frame->bottom, '%') == nullptr);
  }
  puts("LCD 16x2 presentation tests passed (software only).");
}
