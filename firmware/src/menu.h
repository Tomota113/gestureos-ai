#pragma once

#include <stddef.h>
#include <stdint.h>

#include "lcd_ui.h"

namespace menu {

enum class Item : uint8_t {
  Run, Dataset, Test, Modes, Settings, Calibrate, Stats, About
};

enum class Input : uint8_t { Up, Down, Press, Left, Right };
enum class EventKind : uint8_t { None, OpenPage, BackToMenu };

struct Event {
  EventKind kind;
  Item item;
};

constexpr size_t kItemCount = 8;
const char* itemName(Item item);

// Navigation only. OpenPage is a page request, never an actuator command.
class Navigator {
 public:
  Navigator();
  void reset();
  Event handle(Input input);
  Item selected() const;
  bool pageOpen() const;
  lcd_ui::Frame render() const;

 private:
  size_t selectedIndex_;
  bool pageOpen_;
};

}  // namespace menu
