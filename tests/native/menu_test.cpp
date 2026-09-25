#include <assert.h>
#include <initializer_list>
#include <string.h>

#include "menu.h"

namespace {
void frameIsBounded(const lcd_ui::Frame& frame) {
  assert(strlen(frame.top) == lcd_ui::kColumns);
  assert(strlen(frame.bottom) == lcd_ui::kColumns);
}
}  // namespace

int main() {
  using namespace menu;
  const char* names[kItemCount] = {
      "RUN", "DATASET", "TEST", "MODES", "SETTINGS", "CALIBRATE", "STATS", "ABOUT"};
  for (size_t i = 0; i < kItemCount; ++i) {
    assert(strcmp(itemName(static_cast<Item>(i)), names[i]) == 0);
  }
  assert(strcmp(itemName(static_cast<Item>(99)), "UNKNOWN") == 0);

  Navigator navigator;
  assert(navigator.selected() == Item::Run);
  assert(!navigator.pageOpen());
  lcd_ui::Frame frame = navigator.render();
  frameIsBounded(frame);
  assert(strcmp(frame.top, "> RUN           ") == 0);
  assert(strcmp(frame.bottom, "  DATASET       ") == 0);

  Event event = navigator.handle(Input::Right);
  assert(event.kind == EventKind::None && event.item == Item::Run);
  event = navigator.handle(Input::Left);
  assert(event.kind == EventKind::None && !navigator.pageOpen());

  for (size_t i = 1; i < kItemCount; ++i) {
    event = navigator.handle(Input::Down);
    assert(event.kind == EventKind::None);
    assert(event.item == static_cast<Item>(i));
    frameIsBounded(navigator.render());
  }
  assert(navigator.selected() == Item::About);
  frame = navigator.render();
  assert(strcmp(frame.top, "  STATS         ") == 0);
  assert(strcmp(frame.bottom, "> ABOUT         ") == 0);

  navigator.handle(Input::Down);  // Wrap at the bottom.
  assert(navigator.selected() == Item::Run);
  navigator.handle(Input::Up);  // Wrap at the top.
  assert(navigator.selected() == Item::About);

  event = navigator.handle(Input::Press);
  assert(event.kind == EventKind::OpenPage && event.item == Item::About);
  assert(navigator.pageOpen());
  frame = navigator.render();
  frameIsBounded(frame);
  assert(strcmp(frame.top, "ABOUT           ") == 0);
  assert(strcmp(frame.bottom, "LEFT: BACK      ") == 0);

  for (Input ignored : {Input::Up, Input::Down, Input::Right, Input::Press}) {
    event = navigator.handle(ignored);
    assert(event.kind == EventKind::None && event.item == Item::About);
    assert(navigator.pageOpen());
  }
  event = navigator.handle(Input::Left);
  assert(event.kind == EventKind::BackToMenu && event.item == Item::About);
  assert(!navigator.pageOpen());
  frame = navigator.render();
  assert(strcmp(frame.bottom, "> ABOUT         ") == 0);

  navigator.reset();
  assert(navigator.selected() == Item::Run && !navigator.pageOpen());
  event = navigator.handle(static_cast<Input>(99));
  assert(event.kind == EventKind::None && event.item == Item::Run);
  return 0;
}
