#include "lcd_ui.h"

namespace lcd_ui {
namespace {
void fillRow(char (&target)[kColumns + 1], const char* source, bool label = false) {
  for (size_t i = 0; i < kColumns; ++i) target[i] = ' ';
  target[kColumns] = '\0';
  if (!source) return;
  for (size_t i = 0; i < kColumns && source[i]; ++i) {
    unsigned char c = static_cast<unsigned char>(source[i]);
    if (c < 32 || c > 126) c = '?';
    if (label && c == '_') c = ' ';
    if (label && c >= 'a' && c <= 'z') c = static_cast<unsigned char>(c - 'a' + 'A');
    target[i] = static_cast<char>(c);
  }
}
}  // namespace

Frame render(Screen screen, const char* detail) {
  Frame frame{};
  switch (screen) {
    case Screen::Boot:
      fillRow(frame.top, "GESTUREOS AI");
      fillRow(frame.bottom, "STARTING");
      break;
    case Screen::Ready:
      fillRow(frame.top, "GESTUREOS AI");
      fillRow(frame.bottom, "READY");
      break;
    case Screen::Recording:
      fillRow(frame.top, "RECORDING");
      fillRow(frame.bottom, detail, true);
      break;
    case Screen::Accepted:
      fillRow(frame.top, detail, true);
      fillRow(frame.bottom, "ACCEPTED");
      break;
    case Screen::Unknown:
      fillRow(frame.top, "UNKNOWN");
      fillRow(frame.bottom, "TRY AGAIN");
      break;
    case Screen::SensorError:
      fillRow(frame.top, "SENSOR ERROR");
      fillRow(frame.bottom, detail, true);
      break;
    default:
      fillRow(frame.top, "UNKNOWN");
      fillRow(frame.bottom, "TRY AGAIN");
  }
  return frame;
}
}  // namespace lcd_ui
