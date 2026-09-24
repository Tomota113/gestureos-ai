#pragma once
#include <stddef.h>

namespace lcd_ui {
constexpr size_t kColumns = 16;

// Presentation only: a hardware adapter will write both rows after pin/voltage checks.
struct Frame {
  char top[kColumns + 1];
  char bottom[kColumns + 1];
};

enum class Screen { Boot, Ready, Recording, Accepted, Unknown, SensorError };

Frame render(Screen screen, const char* detail = nullptr);
}  // namespace lcd_ui
