#include "menu.h"

namespace menu {
namespace {

void clearRow(char (&row)[lcd_ui::kColumns + 1]) {
  for (size_t i = 0; i < lcd_ui::kColumns; ++i) row[i] = ' ';
  row[lcd_ui::kColumns] = '\0';
}

void copyText(char (&row)[lcd_ui::kColumns + 1], size_t offset, const char* text) {
  if (!text || offset >= lcd_ui::kColumns) return;
  for (size_t i = offset; i < lcd_ui::kColumns && *text; ++i, ++text) {
    row[i] = *text;
  }
}

void menuRow(char (&row)[lcd_ui::kColumns + 1], Item item, bool selected) {
  clearRow(row);
  row[0] = selected ? '>' : ' ';
  row[1] = ' ';
  copyText(row, 2, itemName(item));
}

}  // namespace

const char* itemName(Item item) {
  switch (item) {
    case Item::Run: return "RUN";
    case Item::Dataset: return "DATASET";
    case Item::Test: return "TEST";
    case Item::Modes: return "MODES";
    case Item::Settings: return "SETTINGS";
    case Item::Calibrate: return "CALIBRATE";
    case Item::Stats: return "STATS";
    case Item::About: return "ABOUT";
    default: return "UNKNOWN";
  }
}

Navigator::Navigator() : selectedIndex_(0), pageOpen_(false) {}

void Navigator::reset() {
  selectedIndex_ = 0;
  pageOpen_ = false;
}

Event Navigator::handle(Input input) {
  Event result{EventKind::None, selected()};
  if (pageOpen_) {
    if (input == Input::Left) {
      pageOpen_ = false;
      result.kind = EventKind::BackToMenu;
    }
    return result;
  }
  switch (input) {
    case Input::Up:
      selectedIndex_ = (selectedIndex_ + kItemCount - 1) % kItemCount;
      break;
    case Input::Down:
      selectedIndex_ = (selectedIndex_ + 1) % kItemCount;
      break;
    case Input::Press:
      pageOpen_ = true;
      result.kind = EventKind::OpenPage;
      break;
    case Input::Left:
    case Input::Right:
    default:
      break;
  }
  result.item = selected();
  return result;
}

Item Navigator::selected() const {
  return static_cast<Item>(selectedIndex_);
}

bool Navigator::pageOpen() const {
  return pageOpen_;
}

lcd_ui::Frame Navigator::render() const {
  lcd_ui::Frame frame{};
  if (pageOpen_) {
    clearRow(frame.top);
    clearRow(frame.bottom);
    copyText(frame.top, 0, itemName(selected()));
    copyText(frame.bottom, 0, "LEFT: BACK");
    return frame;
  }
  const size_t first = (selectedIndex_ / 2) * 2;
  menuRow(frame.top, static_cast<Item>(first), selectedIndex_ == first);
  menuRow(frame.bottom, static_cast<Item>(first + 1), selectedIndex_ == first + 1);
  return frame;
}

}  // namespace menu
