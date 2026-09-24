#include "capture_protocol.h"
#include <stdio.h>
#include <string.h>

namespace capture_protocol {
bool parseRequest(const char* line, Request& request) {
  if (strncmp(line, "CAPTURE ", 8) != 0) return false;
  Request candidate{};
  unsigned long count = 0;
  char extra = 0;
  if (sscanf(line + 8, "%32s %32s %lu %c", candidate.id, candidate.label,
             &count, &extra) != 3) return false;
  if (strlen(candidate.id) != 32 || count < 50 || count > 500) return false;
  for (char c : candidate.id) {
    if (c == 0) break;
    if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  }
  if (candidate.label[0] < 'a' || candidate.label[0] > 'z') return false;
  for (char c : candidate.label) {
    if (c == 0) break;
    if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_')) return false;
  }
  candidate.samples = static_cast<uint16_t>(count);
  request = candidate;
  return true;
}

uint32_t crc32(const char* data, size_t size, uint32_t previous) {
  uint32_t crc = previous ^ 0xFFFFFFFFu;
  for (size_t i = 0; i < size; ++i) {
    crc ^= static_cast<uint8_t>(data[i]);
    for (int bit = 0; bit < 8; ++bit)
      crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
  }
  return crc ^ 0xFFFFFFFFu;
}
}  // namespace capture_protocol
